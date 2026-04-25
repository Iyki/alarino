import json
import re
import unicodedata
from pathlib import Path
from typing import Callable

from alarino_backend.db_models import Proverb, ProverbWord, Sense, db, Word, Translation
from alarino_backend.languages import Language
# normalize_word_text and normalize_text live in alarino_backend.normalization
# so the TypeDecorators in db_models.py can use them without a circular import.
# Re-exported here for callers that import them from this module.
from alarino_backend.normalization import normalize_text, normalize_word_text  # noqa: F401
from alarino_backend.runtime import logger

# Define valid Yoruba character sets
_YORUBA_CONSONANTS = "bdfghjklmnprstwygbṣ"  # Standard consonants (excluding c, q, v, x, z)
_YORUBA_VOWELS = "aàáeèéẹẹ̀ẹ́iìíoòóọọ̀ọ́uùú"  # Standard vowels with tone marks
_YORUBA_NASAL_VOWELS = "mḿm̀nńǹ"  # Nasal vowels with tone marks
_YORUBA_CHARACTER_SET = _YORUBA_CONSONANTS + _YORUBA_VOWELS + _YORUBA_NASAL_VOWELS


def add_word(language: Language, word_text: str):
    """Insert a word, returning the existing row if (language, word) already
    exists. POS is no longer a Word-level attribute (Phase 6d dropped
    Word.part_of_speech) — to attach POS, set it on a Sense for this Word
    after creation."""
    word_text = normalize_word_text(word_text)

    if language == Language.YORUBA and not is_valid_yoruba_word(word_text):
        logger.debug(f"Invalid Yoruba word rejected: {word_text}")
        return None
    if language == Language.ENGLISH and not is_valid_english_word(word_text):
        logger.debug(f"Invalid English word rejected: {word_text}")
        return None

    existing_word = Word.query.filter_by(language=language, text=word_text).first()
    if existing_word:
        return existing_word
    word = Word(language=language, text=word_text)
    db.session.add(word)
    return word


def add_proverb(yoruba_proverb: str, english_proverb: str):
    """
    Adds a new proverb to the database and extracts its words.
    Args:
        db: The database session.
        yoruba_proverb: The Yoruba version of the proverb.
        english_proverb: The English version of the proverb.
    """
    # Normalize text-level inputs to NFC before any storage or comparison so
    # canonically-equivalent forms (precomposed vs decomposed Yoruba) collide
    # at the unique constraint and at duplicate detection.
    yoruba_proverb = normalize_text(yoruba_proverb)
    english_proverb = normalize_text(english_proverb)

    # Check if the proverb already exists
    existing_proverb = Proverb.query.filter_by(
        yoruba_text=yoruba_proverb,
        english_text=english_proverb
    ).first()

    if existing_proverb:
        logger.info(f"Proverb already exists: '{yoruba_proverb}'")
        return

    # Add the new proverb
    new_proverb = Proverb(yoruba_text=yoruba_proverb, english_text=english_proverb)
    db.session.add(new_proverb)
    db.session.flush()  # Need new_proverb.p_id to populate proverb_words.
    logger.info(f"Added proverb: '{yoruba_proverb}'")

    # Extract individual words and connect them to the proverb via proverb_words.
    # Words that fail validation (add_word returns None) are silently skipped — the
    # proverb itself is still stored, only the join entry is missing.
    for language, raw_text in (
        (Language.YORUBA, yoruba_proverb),
        (Language.ENGLISH, english_proverb),
    ):
        position = 0
        for token in re.findall(r'\b\w+\b', raw_text):
            word = add_word(language=language, word_text=token)
            if word is None:
                continue
            db.session.flush()  # Need word.w_id if add_word inserted a new row.
            db.session.add(
                ProverbWord(
                    proverb_id=new_proverb.p_id,
                    word_id=word.w_id,
                    language=language.value,
                    position=position,
                )
            )
            position += 1


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
    valid_chars = unicodedata.normalize('NFC', _YORUBA_CHARACTER_SET + extra_chars)
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

class AmbiguousSenseError(ValueError):
    """Raised when a write path that doesn't specify a sense is asked to
    operate on a word that has more than one curated sense. The caller must
    either pick a sense explicitly or fall back to a sense-aware API."""


def _ensure_default_sense(word: Word) -> Sense:
    """Return THE sense for the word, creating a default one if none exist.

    Strict: if the word already has multiple senses, this raises
    AmbiguousSenseError. Bulk-upload and similar write paths that carry no
    sense information would otherwise silently bind a new translation to
    whichever sense has the lowest sense_id — an arbitrary choice that
    almost certainly doesn't match curator intent. Failing loud forces
    the caller to use a sense-aware path (or for the curator to deduplicate
    senses on the word) before the silent corruption can land.
    """
    word.w_id  # ensure attribute is loaded; flush if needed
    if word.w_id is None:
        db.session.flush()
    senses = (
        Sense.query
        .filter_by(word_id=word.w_id)
        .order_by(Sense.sense_id)
        .all()
    )
    if len(senses) > 1:
        labels = [(s.sense_id, s.sense_label) for s in senses]
        raise AmbiguousSenseError(
            f"Word w_id={word.w_id} ({word.language}:{word.text!r}) has "
            f"{len(senses)} senses {labels!r}; cannot pick a default. "
            "Use a sense-aware API to specify which sense the new "
            "translation should attach to."
        )
    if senses:
        return senses[0]
    # Default sense carries no POS metadata. Phase 6d removed the
    # Word.part_of_speech column that this previously copied; callers who
    # want POS set it on the Sense explicitly via a future curation flow.
    sense = Sense(word_id=word.w_id)
    db.session.add(sense)
    db.session.flush()
    return sense


def create_translation(source: Word, target: Word):
    """Create a Translation between two Words, attaching to each Word's
    default sense. Raises AmbiguousSenseError if either word has multiple
    curated senses (the bulk-upload format carries no sense info; binding
    to whichever sense_id is lowest would silently corrupt curator intent).

    Idempotent on the (source_sense, target_sense) pair: if a Translation
    already exists with the resolved sense pair, this is a no-op. Polysemy
    that targets the same surface words via *different* sense pairs is
    representable — that's exactly what the unique_translation_sense_pair
    constraint allows."""
    source_sense = _ensure_default_sense(source)
    target_sense = _ensure_default_sense(target)
    existing = Translation.query.filter_by(
        source_sense_id=source_sense.sense_id,
        target_sense_id=target_sense.sense_id,
    ).first()
    if existing:
        return
    translation = Translation(
        source_word=source,
        target_word=target,
        source_sense_id=source_sense.sense_id,
        target_sense_id=target_sense.sense_id,
    )
    db.session.add(translation)


def upload_data_in_batches(entries: list, upload_func: Callable[[list, int], list],
                           invalid_files_prefix: str,
                           batch_size: int = 500, batch_start: int = 0):
    all_invalid_entries = []

    while batch_start < len(entries):
        end = min(batch_start + batch_size, len(entries))
        batch_id = (batch_start // batch_size) + 1
        logger.info(f"Processing batch {batch_id} from index {batch_start} to {end}")
        batch = entries[batch_start:end]
        batch_invalids = upload_func(batch, batch_id)

        if batch_invalids:
            all_invalid_entries.extend(batch_invalids)
            # Write invalid entries for the current batch
            batch_file = Path(f"{invalid_files_prefix}_{batch_id}.json")
            batch_file.parent.mkdir(parents=True, exist_ok=True)
            with open(batch_file, "w", encoding="utf-8") as f:
                json.dump(batch_invalids, f, indent=2, ensure_ascii=False)
            logger.warning(f"Wrote {len(batch_invalids)} invalid entries to {batch_file}")

        batch_start += batch_size

    if all_invalid_entries:
        invalid_file_path = Path(f"{invalid_files_prefix}_all.json")
        invalid_file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(invalid_file_path, "w", encoding="utf-8") as f:
            json.dump(all_invalid_entries, f, indent=2, ensure_ascii=False)
        logger.info(f"Wrote {len(all_invalid_entries)} total invalid entries to {invalid_file_path}")

    logger.info(f"Finished processing all {len(entries)} entries. Skipped {len(all_invalid_entries)} invalid entries.")
