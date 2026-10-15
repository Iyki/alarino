#!/usr/bin/env python3
"""Decode the FreeLang English→Yorùbá export into a reference lexicon.

FreeLang is used only as a reference when resolving disputed spellings in
the OCR'd books; nothing from it is uploaded to the dictionary.

The export (offline/scans/freelang_dict_2.pdf) is a digital text PDF, not a
scan, so there is nothing to OCR. Its Yorùbá was written with a legacy font
that stored subdotted letters as look-alike Latin-1 characters ("õpõ" for
ọ̀pọ̀, "ÿ" for ṣ), and those characters are what the PDF renders and
stores. DECODE maps them back. The table was read off known words and then
confirmed by scoring every alternative tone assignment against the seed and
Babalola lexicons (the toneless CMS 1913 spellings are excluded from that
check because they bias it toward under-marked forms).

Each reference entry records flags a consumer must respect:
- "unclear": the raw text contains "ñ" or "æ", which the source uses
  inconsistently, so the decoded spelling is unreliable;
- "plain_e": the word contains an e without a subdot. The source usually
  writes mid-tone ẹ as plain "e", so a plain e here cannot tell e from ẹ.

Usage:
    python offline/freelang_decode.py   # writes offline/out/freelang/reference.json
"""

import argparse
import itertools
import json
import re
import sys
import unicodedata
from pathlib import Path

import pymupdf

REPO_ROOT = Path(__file__).resolve().parents[1]
PDF = REPO_ROOT / "offline" / "scans" / "freelang_dict_2.pdf"
OUT = REPO_ROOT / "offline" / "out" / "freelang"

D, G, A = "̣", "̀", "́"
DECODE = {
    "ÿ": "ṣ",
    "ô": "o" + D, "ö": "o" + D + A, "õ": "o" + D + G,
    "Ô": "O" + D, "Õ": "O" + D + G,
    "ç": "e" + D, "ë": "e" + D + A, "ê": "e" + D + G,
    "ý": "n" + G, "¸": "n" + G, "þ": "n" + A,
}
UNCLEAR = set("ñæ")

sys.path.insert(0, str(REPO_ROOT / "alarino_backend" / "src"))
from alarino_backend import normalization  # noqa: E402


def nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


def decode(text: str) -> str:
    return nfc("".join(DECODE.get(ch, ch) for ch in text))


def read_entries() -> list[tuple[str, str]]:
    """The export is laid out as 'english', '-', 'yoruba' text lines."""
    doc = pymupdf.open(PDF)
    lines = [l.strip() for l in "\n".join(p.get_text() for p in doc).splitlines()]
    return [(lines[i], lines[i + 2]) for i in range(len(lines) - 2) if lines[i + 1] == "-"]


def dotted_e_variants(word: str):
    """Spellings of word with one or more plain e's given a subdot."""
    d = list(unicodedata.normalize("NFD", word))
    plain = [i for i, ch in enumerate(d) if ch == "e" and (i + 1 >= len(d) or d[i + 1] != D)]
    for k in range(1, len(plain) + 1):
        for combo in itertools.combinations(plain, k):
            dd = d[:]
            for i in sorted(combo, reverse=True):
                dd.insert(i + 1, D)
            yield nfc("".join(dd))


def main() -> None:
    argparse.ArgumentParser(description=__doc__.splitlines()[0]).parse_args()
    entries = []
    for english, raw_yoruba in read_entries():
        english = english.strip().lower()
        if not normalization.is_valid_english_word(english):
            continue
        for raw in re.split(r"[,;]", raw_yoruba):
            raw = raw.strip().lower()
            if not raw:
                continue
            yoruba = decode(raw)
            flags = []
            if UNCLEAR & set(raw):
                flags.append("unclear")
            elif not normalization.is_valid_yoruba_word(yoruba):
                continue
            if any(True for _ in dotted_e_variants(yoruba)):
                flags.append("plain_e")
            entries.append({"english": english, "yoruba": yoruba, "raw": raw, "flags": flags})

    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "reference.json"
    path.write_text(json.dumps(entries, ensure_ascii=False, indent=1))
    flagged = sum(1 for e in entries if e["flags"])
    print(f"wrote {len(entries)} reference spellings ({flagged} flagged) to {path}")

if __name__ == "__main__":
    main()
