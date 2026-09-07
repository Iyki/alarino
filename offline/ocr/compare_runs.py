#!/usr/bin/env python3
"""Compare OCR transcripts of the same pages across models.

Aligns dictionary entries by English headword, diffs the Yorùbá text, and
buckets each entry:

  unanimous          all available models agree exactly
  diacritic_dispute  same base letters, models disagree only on tone marks
                     and/or subdots — the review-queue / voting cases
  divergent          models disagree beyond diacritics (structure, words)
  partial            headword found in only some models' transcripts

Models are optional votes: a page is compared across whichever transcripts
exist under <out>/<model>/<page>.txt.

Usage:
    python offline/ocr/compare_runs.py --out offline/out n100 n150 n200
    (page names default to every page any model has transcribed)

Writes <out>/comparison/<page>.json with the full per-entry detail and
prints a summary.
"""

import argparse
import difflib
import json
import re
import sys
import unicodedata
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
try:
    from alarino_backend import normalization
except ModuleNotFoundError:
    sys.path.insert(0, str(REPO_ROOT / "alarino_backend" / "src"))
    from alarino_backend import normalization

DEFAULT_MODELS = ["qwen3-vl-235b", "gemma-4-31b", "dots-3-note", "gemini-3.8-flash"]

def is_entry_start(line: str) -> bool:
    """An entry line starts with a capitalized headword followed by a comma,
    e.g. "Son-in-law, n. ..." or "Àganwó, n. mahogany tree.". str.isupper()
    is Unicode-aware, which matters for the Yorùbá→English section where
    headwords start with accented capitals (À, Ẹ, Ọ, Ṣ...)."""
    return bool(line) and line[0].isupper() and "," in line[:45]


def strip_diacritics(text: str) -> str:
    """Reduce to lowercase base letters: NFD, drop combining marks. Removes
    both tone marks and subdots, so two spellings that differ only in
    diacritics collapse to the same string."""
    decomposed = unicodedata.normalize("NFD", text.casefold())
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def _segment_lines(text: str) -> list[str]:
    """Normalize a transcript into candidate entry lines. Some models ignore
    the one-entry-per-line instruction and return the page as one run-on
    line, keep the print's line-wrap hyphenation ("contem- ner"), or keep
    the running header ("AGA 9 AGB"). Rejoin hyphenated wraps, split lines
    at sentence boundaries followed by an uppercase letter, and drop
    leading all-caps/page-number header tokens."""
    text = re.sub(r"(?<=\w)-\s+(?=\w)", "", text)  # "contem- ner" -> "contemner"
    lines: list[str] = []
    for raw_line in text.splitlines():
        raw_line = raw_line.strip()
        if raw_line:
            # [^\Wa-z\d_] = any Unicode uppercase letter (incl. À, Ẹ, Ọ, Ṣ).
            lines.extend(re.split(r"(?<=[.;!?])\s+(?=[^\Wa-z\d_])", raw_line))
    if lines:  # strip a leading running header like "AGA 9 AGB"
        tokens = lines[0].split()
        while tokens and (
            tokens[0].isdigit() or (len(tokens[0]) > 1 and tokens[0].isupper())
        ):
            tokens.pop(0)
        lines[0] = " ".join(tokens)
    return [line for line in lines if line]


def parse_entries(text: str) -> list[dict]:
    """Split a transcript into entries, folding wrapped continuation lines
    into the preceding entry. Returns [{head, body}] in page order."""
    entries: list[dict] = []
    for line in _segment_lines(text):
        if is_entry_start(line) or not entries:
            head = line.split(",", 1)[0]
            entries.append({"head": head, "body": line})
        else:
            entries[-1]["body"] += " " + line
    for e in entries:
        e["body"] = normalization.normalize_text(" ".join(e["body"].split()))
        e["key"] = strip_diacritics(e["head"])
    return entries


def align_to_reference(ref: list[dict], other: list[dict]) -> dict[int, int]:
    """Order-preserving alignment of two entry lists by headword key.
    Returns {ref_index: other_index}."""
    matcher = difflib.SequenceMatcher(
        None, [e["key"] for e in ref], [e["key"] for e in other], autojunk=False
    )
    mapping: dict[int, int] = {}
    for a, b, size in matcher.get_matching_blocks():
        for i in range(size):
            mapping[a + i] = b + i
    return mapping


def diacritic_diff_words(bodies: list[str]) -> list[dict]:
    """For bodies that are identical after strip_diacritics, list the word
    positions where the raw spellings differ, with each variant."""
    token_lists = [b.split() for b in bodies]
    diffs = []
    for pos, words in enumerate(zip(*token_lists)):
        if len(set(words)) > 1:
            diffs.append({"position": pos, "variants": sorted(set(words))})
    return diffs


def compare_page(page: str, out_root: Path, models: list[str]) -> dict | None:
    transcripts = {
        m: parse_entries((out_root / m / f"{page}.txt").read_text())
        for m in models
        if (out_root / m / f"{page}.txt").is_file()
    }
    if len(transcripts) < 2:
        return None

    # Reference = the transcript with the most entries (most complete parse).
    ref_model = max(transcripts, key=lambda m: len(transcripts[m]))
    ref = transcripts[ref_model]
    alignments = {
        m: align_to_reference(ref, entries)
        for m, entries in transcripts.items()
        if m != ref_model
    }

    results = []
    for i, ref_entry in enumerate(ref):
        versions = {ref_model: ref_entry["body"]}
        for m, mapping in alignments.items():
            if i in mapping:
                versions[m] = transcripts[m][mapping[i]]["body"]

        if len(versions) < len(transcripts):
            bucket = "partial"
            detail = {"missing_in": sorted(set(transcripts) - set(versions))}
        elif len(set(versions.values())) == 1:
            bucket = "unanimous"
            detail = {}
        elif len({strip_diacritics(v) for v in versions.values()}) == 1:
            bucket = "diacritic_dispute"
            detail = {"words": diacritic_diff_words(list(versions.values()))}
        else:
            bucket = "divergent"
            detail = {}

        results.append({
            "head": ref_entry["head"],
            "bucket": bucket,
            "versions": versions,
            **detail,
        })

    return {
        "page": page,
        "models": sorted(transcripts),
        "reference": ref_model,
        "entry_counts": {m: len(e) for m, e in transcripts.items()},
        "entries": results,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("pages", nargs="*", help="page names (default: all found)")
    ap.add_argument("--out", type=Path, default=Path("offline/out"))
    ap.add_argument("--models", nargs="+", default=DEFAULT_MODELS)
    args = ap.parse_args()

    pages = args.pages or sorted(
        {f.stem for m in args.models for f in (args.out / m).glob("*.txt")}
    )
    if not pages:
        sys.exit("error: no transcripts found")

    report_dir = args.out / "comparison"
    report_dir.mkdir(parents=True, exist_ok=True)

    totals: dict[str, int] = {}
    for page in pages:
        report = compare_page(page, args.out, args.models)
        if report is None:
            print(f"{page}: fewer than 2 transcripts, skipped")
            continue
        (report_dir / f"{page}.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=1)
        )
        counts: dict[str, int] = {}
        for e in report["entries"]:
            counts[e["bucket"]] = counts.get(e["bucket"], 0) + 1
            totals[e["bucket"]] = totals.get(e["bucket"], 0) + 1
        n = len(report["entries"])
        summary = ", ".join(f"{k}={v}" for k, v in sorted(counts.items()))
        print(f"{page}: {n} entries across {len(report['models'])} models "
              f"(ref={report['reference']}): {summary}")

    if totals:
        n = sum(totals.values())
        print(f"\ntotal: {n} entries: "
              + ", ".join(f"{k}={v} ({v / n:.0%})" for k, v in sorted(totals.items())))
        print(f"reports: {report_dir}/<page>.json")


if __name__ == "__main__":
    main()
