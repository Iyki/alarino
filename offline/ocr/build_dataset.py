#!/usr/bin/env python3
"""Build a bulk-upload CSV from cross-model OCR consensus.

Takes the comparison reports produced by compare_runs.py, keeps only entries
where every available model agreed exactly (bucket == "unanimous"), parses
each entry into word pairs, and writes the two-column no-header CSV that
POST /api/admin/bulk-upload accepts: english,yoruba per line.

Both directions of the dictionary are handled: English→Yorùbá entries
("Solely, adv. kiki, nikanṣoṣo.") yield one row per Yorùbá translation;
Yorùbá→English entries ("Àganwó, n. mahogany tree.") yield one row per
short English gloss. Every candidate is checked with the backend's own
validators, so nothing in the output can be rejected at upload time; the
strict modern-charset check also drops un-modernized 1913 orthography
(ā, õ, ...) rather than importing it.

Usage:
    python offline/ocr/build_dataset.py --out offline/out
    # writes offline/out/bulk_upload.csv
"""

import argparse
import csv
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
try:
    from alarino_backend import normalization
except ModuleNotFoundError:
    sys.path.insert(0, str(REPO_ROOT / "alarino_backend" / "src"))
    from alarino_backend import normalization

# Part-of-speech markers as printed in the 1913 dictionary. Longest first so
# "v.t. and i." wins over "v.t.".
POS_MARKERS = [
    "v.t. and i.", "v.i. and t.", "v. aux.", "v.t.", "v.i.", "v.",
    "adj.", "adv.", "conj.", "interj.", "prep.", "pron.", "n.", "art.",
]
_ARTICLE_RE = re.compile(r"^(?:a|an|the|to|of)\s+", re.IGNORECASE)

# A gloss containing any of these reads as a definition fragment ("usually of
# bamboo", "ancient of days"), not a translation term.
_GLOSS_STOPWORDS = {
    "a", "an", "the", "of", "with", "for", "by", "in", "on", "at", "as",
    "who", "which", "that", "is", "are", "was", "used", "one", "etc", "see",
}


def translation_candidates(body: str) -> list[str]:
    """Extract translation tokens from everything after the headword: split
    on commas/semicolons, then strip leading POS markers from each token."""
    after_head = body.split(",", 1)[1] if "," in body else ""
    tokens = []
    for raw in re.split(r"[,;]", after_head):
        token = raw.strip()
        stripped = True
        while stripped:
            stripped = False
            for marker in POS_MARKERS:  # longest-first
                if token == marker or token.startswith(marker + " "):
                    token = token[len(marker):].strip()
                    stripped = True
        token = token.strip().strip(".").strip()
        if token:
            tokens.append(token)
    return tokens


def page_direction(entries: list[dict]) -> str:
    """'en-yo' or 'yo-en', decided by majority over ALL of a page's headwords.
    Page-level (not per-entry) because undiacritized Yorùbá headwords like
    'Agara' are pure ASCII and would be misread as English one entry at a
    time, while a page's diacritic-bearing majority is unambiguous."""
    yoruba_heads = sum(1 for e in entries if not e["head"].isascii())
    return "yo-en" if yoruba_heads > len(entries) / 2 else "en-yo"


def pairs_from_entry(head: str, body: str, direction: str) -> tuple[list[tuple[str, str]], str]:
    """Turn one unanimous entry into (english, yoruba) pairs.

    Returns (pairs, reason): pairs may be empty, in which case reason says
    why the whole entry was skipped ("head" = unusable headword). Individual
    candidate tokens that fail validation are silently dropped — unanimity
    makes the survivors trustworthy, not the whole line.
    """
    head = head.strip().strip(".").lower()
    candidates = translation_candidates(body)
    pairs = []
    if direction == "en-yo":
        if not normalization.is_valid_english_word(head):
            return [], "head"
        for token in candidates:
            # A capitalized token is a secondary headword ("Sought, Seek,
            # v.t. ..."), not a Yorùbá translation — those are lowercase.
            if token[0].isupper():
                continue
            if normalization.is_valid_yoruba_word(token):
                pairs.append((head, token))
        return pairs, "" if pairs else "no-valid-yoruba"
    if not normalization.is_valid_yoruba_word(head):
        return [], "head"
    for token in candidates:
        token = _ARTICLE_RE.sub("", token.lower()).strip()
        words = token.split()
        # Keep short glosses that read as words/terms, not definitions.
        if (
            words
            and len(words) <= 3
            and not _GLOSS_STOPWORDS.intersection(words)
            and normalization.is_valid_english_word(token)
        ):
            pairs.append((token, head))
    return pairs, "" if pairs else "no-valid-english"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=Path("offline/out"),
                    help="output root holding comparison/ (CSV goes to <out>/bulk_upload.csv)")
    ap.add_argument("--csv", type=Path, help="explicit output CSV path")
    args = ap.parse_args()

    reports = sorted((args.out / "comparison").glob("*.json"))
    if not reports:
        sys.exit("error: no comparison reports found; run compare_runs.py first")

    pairs: dict[tuple[str, str], str] = {}  # pair -> page of first sighting
    stats = {"entries": 0, "unanimous": 0, "skipped_head": 0,
             "skipped_no_pairs": 0, "used": 0}
    for report_path in reports:
        report = json.loads(report_path.read_text())
        direction = page_direction(report["entries"])
        for entry in report["entries"]:
            stats["entries"] += 1
            if entry["bucket"] != "unanimous":
                continue
            stats["unanimous"] += 1
            body = next(iter(entry["versions"].values()))
            entry_pairs, reason = pairs_from_entry(entry["head"], body, direction)
            if not entry_pairs:
                stats["skipped_head" if reason == "head" else "skipped_no_pairs"] += 1
                continue
            stats["used"] += 1
            for pair in entry_pairs:
                pairs.setdefault(pair, report["page"])

    csv_path = args.csv or args.out / "bulk_upload.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for english, yoruba in pairs:
            writer.writerow([english, yoruba])

    print(f"{stats['entries']} entries -> {stats['unanimous']} unanimous -> "
          f"{stats['used']} usable entries -> {len(pairs)} unique pairs")
    print(f"skipped: {stats['skipped_head']} unusable headword, "
          f"{stats['skipped_no_pairs']} with no valid translation tokens")
    print(f"wrote {csv_path}")


if __name__ == "__main__":
    main()
