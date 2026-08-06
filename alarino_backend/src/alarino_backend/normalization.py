"""Canonical text normalization and alphabet validation for alarino.

Lives in its own module (no DB dependency) so it can be imported by both
the ORM layer (db_models.py — for the NFCWord/NFCText TypeDecorators) and
the service layer (seed_data_utils.py, translation_service.py — for read
paths and explicit pre-write normalization), as well as by offline data
tooling (offline/) that must share the exact same alphabet and
normalization without importing the Flask/DB stack.

The TypeDecorators in db_models.py call these functions at SQLAlchemy
bind time, which means every ORM write and every parameterized query
goes through the same normalization regardless of whether the call site
remembered to normalize first. The explicit calls in the service layer
remain as defense in depth (redundant but harmless under the
TypeDecorator) and as the only normalization for paths that don't touch
the ORM (e.g., translate_llm passes user input to an LLM, not to a query).
"""

import re
import unicodedata

# Valid Yoruba character sets (NFC-normalized on use; see _is_valid_yoruba).
YORUBA_CONSONANTS = "bdfghjklmnprstwygbṣ"  # Standard consonants (excluding c, q, v, x, z)
YORUBA_VOWELS = "aàáeèéẹẹ̀ẹ́iìíoòóọọ̀ọ́uùú"  # Standard vowels with tone marks
YORUBA_NASAL_VOWELS = "mḿm̀nńǹ"  # Nasal vowels with tone marks
YORUBA_CHARACTER_SET = YORUBA_CONSONANTS + YORUBA_VOWELS + YORUBA_NASAL_VOWELS


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


def _is_valid_yoruba(text: str, extra_chars: str) -> bool:
    """
    Generic validation helper for Yoruba text.
    Args:
        text: The text to validate.
        extra_chars: Additional characters to allow.
    Returns:
        bool: Whether the text is valid.
    """
    if not text:
        return False
    # Normalize input to NFC so the codepoints align with the (NFC) char class
    # below. Without this, NFD input that is canonically valid Yoruba would be
    # rejected because its decomposed codepoints don't appear in the char set.
    text = unicodedata.normalize('NFC', text.strip().lower())
    valid_chars = unicodedata.normalize('NFC', YORUBA_CHARACTER_SET + extra_chars)
    escaped_chars = re.escape(valid_chars)
    pattern = f"^[{escaped_chars}]+$"
    return bool(re.match(pattern, text, re.UNICODE))


def is_valid_yoruba_word(word: str) -> bool:
    """
    Validates if a word contains only valid Yoruba characters.
    Args:
        word: The word to validate.
    Returns:
        bool: Whether the word is valid.
    """
    return _is_valid_yoruba(word, extra_chars="'- ")


def is_valid_yoruba_text(text: str) -> bool:
    """
    Validates if a text contains only valid Yoruba characters and punctuation.
    Args:
        text: The text to validate.
    Returns:
        bool: Whether the text is valid.
    """
    return _is_valid_yoruba(text, extra_chars="' -.,?!;:")


def is_valid_english_word(word: str) -> bool:
    """
    Validates if a word contains only valid English characters
    Args:
        word: The word to validate
    Returns:
        bool: Whether the word contains only valid English characters
    """
    # NFC normalize for consistency with the Yoruba validators. ASCII is
    # invariant under NFC/NFD, so this is a no-op for ASCII input but ensures
    # any stray combining marks in input are handled the same way storage does.
    word = unicodedata.normalize("NFC", word.strip().lower())
    if not word:
        return False

    # Simple regex pattern for English text (letters, apostrophes, hyphens, spaces)
    pattern = r'^[a-z\'\- ]+$'
    return bool(re.match(pattern, word, re.UNICODE))


def is_valid_english_text(text: str) -> bool:
    """
    Validates if a text contains only valid English characters and punctuation.
    Args:
        text: The text to validate.
    Returns:
        bool: Whether the text is valid.
    """
    text = unicodedata.normalize("NFC", text.strip().lower())
    if not text:
        return False

    # Simple regex pattern for English text (letters, apostrophes, hyphens, spaces, and punctuation)
    pattern = r"^[a-z' .,?!;:-]+$"
    return bool(re.match(pattern, text, re.UNICODE))


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
