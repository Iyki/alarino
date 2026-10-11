"""Per-book settings for the offline OCR pipeline.

Each scanned dictionary differs in where its pages live, which pages hold
entries, how an entry is laid out, which half of the book is Yorùbá→English,
and what provenance tag its uploaded rows carry.
"""

from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCANS = REPO_ROOT / "offline" / "scans"
OUT = REPO_ROOT / "offline" / "out"


def _stems(*ranges: tuple[int, int]) -> frozenset[str]:
    return frozenset(f"pg{i:03d}" for lo, hi in ranges for i in range(lo, hi + 1))


@dataclass(frozen=True)
class Book:
    key: str
    pages_dir: Path
    out_dir: Path
    content: frozenset[str]
    provenance: str
    # "cms": "Headword, pos. translation, translation." with dotted POS markers.
    # "bracketed": "headword [respelling] pos gloss, gloss" with bare POS codes.
    entry_style: str
    # Pages whose headwords are Yorùbá. None = infer per page from headword
    # diacritics (works for CMS, whose sections are interleaved by the scan).
    yo_en: frozenset[str] | None = None


BOOKS = {
    "cms1913": Book(
        key="cms1913",
        pages_dir=SCANS / "pages",
        out_dir=OUT,
        content=_stems((11, 457)),
        provenance="cms-dict-1913",
        entry_style="cms",
    ),
    # Olabiyi Babalola Yai, Yoruba-English/English-Yoruba Concise Dictionary
    # (Hippocrene, 1996). PDF page index = printed page - 2. Yorùbá→English is
    # printed 13-114, English→Yorùbá printed 116-257; pg113 is the section
    # title and pg256+ are publisher ads.
    "babalola1996": Book(
        key="babalola1996",
        pages_dir=SCANS / "babalola1996" / "pages",
        out_dir=OUT / "babalola1996",
        content=_stems((11, 112), (114, 255)),
        provenance="babalola-yai-1996",
        entry_style="bracketed",
        yo_en=_stems((11, 112)),
    ),
}
