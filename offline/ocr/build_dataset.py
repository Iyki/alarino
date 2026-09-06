#!/usr/bin/env python3
"""Build a bulk-upload CSV from cross-model OCR consensus.

Takes the comparison reports produced by compare_runs.py, keeps only entries
where every available model agreed exactly (bucket == "unanimous"), parses
each entry into word pairs, and writes the extended header CSV that
POST /api/admin/bulk-upload accepts: english,yoruba,pos,provenance,confidence.
pos comes from the printed POS markers (n. -> n, v.t. -> v, ...), provenance
records the source book and page ("cms-dict-1913:n150"), and confidence
scales with how many models agreed (2 -> 0.9, 3 -> 0.95... capped at 0.95).

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

# Abbreviation markers as printed in the 1913 dictionary (its front matter
# lists them on pg010), mapped to the canonical PartOfSpeech codes the
# backend's CHECK constraint allows. Ordered longest first so
# "v.t. and i." wins over "v.t.".
POS_MARKERS = {
    "v.t. and i.": "v", "v.i. and t.": "v", "aux. v.": "v",
    "v.t.": "v", "v.i.": "v", "p.p.": "v", "v.": "v",
    "n.pl.": "n", "n.": "n",
    "adj.": "adj", "adv.": "adv", "conj.": "conj", "interj.": "interj",
    "prep.": "prep", "pron.": "pron", "art.": "det",
}
# Stripped without changing the current POS section ("sing." qualifies the
# preceding gloss; "pref." entries are affixes with no canonical POS).
NEUTRAL_MARKERS = ("sing.", "pref.")
# Everything from these markers to the next POS marker is a cross-reference
# or usage example, not a translation — drop those tokens.
DROP_MARKERS = ("cf.", "e.g.", "see")
_ARTICLE_RE = re.compile(r"^(?:a|an|the|to|of)\s+", re.IGNORECASE)

# A gloss containing any of these reads as a definition fragment ("usually of
# bamboo", "ancient of days"), not a translation term.
_GLOSS_STOPWORDS = {
    "a", "an", "the", "of", "with", "for", "by", "in", "on", "at", "as",
    "who", "which", "that", "is", "are", "was", "used", "one", "etc", "see",
}


# A marker can be matched anywhere it stands as its own token: markers
# contain periods (or are "see") and legitimate Yorùbá/English translations
# never are, so this cannot fire inside a translation. Longest-first
# alternation makes "v.t. and i." win over "v.t.".
_ALL_MARKERS = sorted(
    [*POS_MARKERS, *NEUTRAL_MARKERS, *DROP_MARKERS], key=len, reverse=True
)
_SECTION_RE = re.compile(
    r"(?:^|\s)(" + "|".join(re.escape(m) for m in _ALL_MARKERS) + r")(?=\s|$)"
)
_DROP = object()  # section sentinel: tokens here are not translations


def translation_candidates(body: str) -> list[tuple[str | None, str]]:
    """Extract (pos, token) pairs from everything after the headword. The
    text is sectioned at the printed markers — a POS marker governs every
    translation until the next one ("Sole, n. atẹlẹsẹ. v.t. fi atẹsẹ si.
    adj. nikanṣoṣo."), cross-reference sections (cf., e.g.) are dropped —
    then each section splits on commas/semicolons."""
    after_head = body.split(",", 1)[1] if "," in body else ""
    parts = _SECTION_RE.split(after_head)
    results = []
    current_pos: object = None

    def add_tokens(text: str) -> None:
        if current_pos is _DROP:
            return
        for raw in re.split(r"[,;]", text):
            token = raw.strip().strip(".").strip()
            if token:
                results.append((current_pos, token))

    add_tokens(parts[0])  # anything before the first marker
    for marker, text in zip(parts[1::2], parts[2::2]):
        if marker in DROP_MARKERS:
            current_pos = _DROP
        elif marker in POS_MARKERS:
            current_pos = POS_MARKERS[marker]
        # NEUTRAL_MARKERS: stripped, section POS unchanged
        add_tokens(text)
    return results


def page_direction(entries: list[dict]) -> str:
    """'en-yo' or 'yo-en', decided by majority over ALL of a page's headwords.
    Page-level (not per-entry) because undiacritized Yorùbá headwords like
    'Agara' are pure ASCII and would be misread as English one entry at a
    time, while a page's diacritic-bearing majority is unambiguous."""
    yoruba_heads = sum(1 for e in entries if not e["head"].isascii())
    return "yo-en" if yoruba_heads > len(entries) / 2 else "en-yo"


def pairs_from_entry(head: str, body: str, direction: str) -> tuple[list[tuple[str, str, str]], str]:
    """Turn one unanimous entry into (english, yoruba, pos) triples, where
    pos is the canonical PartOfSpeech code or "" when the entry (or section)
    carried no recognizable marker.

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
        for pos, token in candidates:
            # A capitalized token is a secondary headword ("Sought, Seek,
            # v.t. ..."), not a Yorùbá translation — those are lowercase.
            if token[0].isupper():
                continue
            if normalization.is_valid_yoruba_word(token):
                pairs.append((head, token, pos or ""))
        return pairs, "" if pairs else "no-valid-yoruba"
    if not normalization.is_valid_yoruba_word(head):
        return [], "head"
    for pos, token in candidates:
        token = _ARTICLE_RE.sub("", token.lower()).strip()
        words = token.split()
        # Keep short glosses that read as words/terms, not definitions.
        if (
            words
            and len(words) <= 3
            and not _GLOSS_STOPWORDS.intersection(words)
            and normalization.is_valid_english_word(token)
        ):
            pairs.append((token, head, pos or ""))
    return pairs, "" if pairs else "no-valid-english"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=Path("offline/out"),
                    help="output root holding comparison/ (CSV goes to <out>/bulk_upload.csv)")
    ap.add_argument("--csv", type=Path, help="explicit output CSV path")
    ap.add_argument("--pages", nargs="+",
                    help="only harvest these pages (default: every comparison report)")
    args = ap.parse_args()

    reports = sorted((args.out / "comparison").glob("*.json"))
    if args.pages:
        wanted = set(args.pages)
        reports = [r for r in reports if r.stem in wanted]
        missing = wanted - {r.stem for r in reports}
        if missing:
            sys.exit(f"error: no comparison report for: {', '.join(sorted(missing))}")
    if not reports:
        sys.exit("error: no comparison reports found; run compare_runs.py first")

    # (english, yoruba) -> {pos, provenance, confidence}; first sighting wins,
    # except a known POS fills in for an earlier unknown one.
    pairs: dict[tuple[str, str], dict] = {}
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
            # More independent models agreeing -> higher confidence.
            confidence = round(min(0.7 + 0.1 * len(entry["versions"]), 0.95), 2)
            for english, yoruba, pos in entry_pairs:
                key = (english, yoruba)
                if key not in pairs:
                    pairs[key] = {
                        "pos": pos,
                        "provenance": f"cms-dict-1913:{report['page']}",
                        "confidence": confidence,
                    }
                elif pos and not pairs[key]["pos"]:
                    pairs[key]["pos"] = pos

    csv_path = args.csv or args.out / "bulk_upload.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["english", "yoruba", "pos", "provenance", "confidence"])
        for (english, yoruba), meta in pairs.items():
            writer.writerow([
                english, yoruba, meta["pos"], meta["provenance"], meta["confidence"],
            ])

    print(f"{stats['entries']} entries -> {stats['unanimous']} unanimous -> "
          f"{stats['used']} usable entries -> {len(pairs)} unique pairs")
    print(f"skipped: {stats['skipped_head']} unusable headword, "
          f"{stats['skipped_no_pairs']} with no valid translation tokens")
    print(f"wrote {csv_path}")


if __name__ == "__main__":
    main()
