"""Canonical text normalization for alarino.

Lives in its own module (no DB dependency) so it can be imported by both
the ORM layer (db_models.py — for the NFCWord/NFCText TypeDecorators) and
the service layer (seed_data_utils.py, translation_service.py — for read
paths and explicit pre-write normalization).

The TypeDecorators in db_models.py call these functions at SQLAlchemy
bind time, which means every ORM write and every parameterized query
goes through the same normalization regardless of whether the call site
remembered to normalize first. The explicit calls in the service layer
remain as defense in depth (redundant but harmless under the
TypeDecorator) and as the only normalization for paths that don't touch
the ORM (e.g., translate_llm passes user input to an LLM, not to a query).
"""

import unicodedata


def normalize_word_text(text: str) -> str:
    """Canonical normalization for word lookups: strip surrounding whitespace
    and punctuation, lowercase, then NFC. Storage and read paths must both go
    through this so canonically-equivalent inputs (e.g., precomposed vs.
    decomposed Yoruba diacritics) collapse to the same key."""
    cleaned = text.strip().strip(" ,.?!()").lower()
    return unicodedata.normalize("NFC", cleaned)


def normalize_text(text: str) -> str:
    """Canonical normalization for sentence/proverb-level text: strip leading
    and trailing whitespace, then NFC. Case is preserved (proverbs may carry
    intentional capitalization) and inner punctuation is preserved."""
    return unicodedata.normalize("NFC", text.strip())


def audit_normalization_integrity(db) -> dict[str, list[int]]:
    """Scan every canonical text column and return the row IDs whose stored
    value is not the canonical form expected by its column type.

    Returns a dict keyed by ``"table.column"`` mapping to a sorted list of
    primary-key IDs that violate the invariant. An empty value list means
    the column is clean. An empty top-level dict means everything is clean.

    Intended uses:
    - Smoke test in CI against staging after migrations.
    - Periodic agentic drift detector that opens a GitHub issue if any
      list is non-empty (Phase 3c).
    - Belt-and-suspenders check in tests to confirm the NFCWord/NFCText
      TypeDecorators are doing their job.

    The check runs in Python (using the same ``normalize_word_text`` /
    ``normalize_text`` helpers the column types use) so it is portable
    across SQLite and Postgres without needing Postgres's
    ``unicode_normalize()`` function. For very large tables this is
    O(N) per check; alarino is well below the size where that matters.
    """
    from alarino_backend.db_models import MissingTranslation, Proverb, Word

    violations: dict[str, list[int]] = {}

    for row in db.session.query(Word.w_id, Word.text).all():
        if row.text != normalize_word_text(row.text):
            violations.setdefault("words.text", []).append(row.w_id)

    for row in db.session.query(
        MissingTranslation.m_id, MissingTranslation.text
    ).all():
        if row.text != normalize_word_text(row.text):
            violations.setdefault(
                "missing_translations.text", []
            ).append(row.m_id)

    for row in db.session.query(
        Proverb.p_id, Proverb.yoruba_text, Proverb.english_text
    ).all():
        if row.yoruba_text != normalize_text(row.yoruba_text):
            violations.setdefault(
                "proverbs.yoruba_text", []
            ).append(row.p_id)
        if row.english_text != normalize_text(row.english_text):
            violations.setdefault(
                "proverbs.english_text", []
            ).append(row.p_id)

    for key in violations:
        violations[key].sort()
    return violations
