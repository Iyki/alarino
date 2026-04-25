import json
import re
import unicodedata
from pathlib import Path
from typing import Callable, Optional

from alarino_backend.db_models import Proverb, ProverbWord, Sense, db, Word, Translation
from alarino_backend.languages import Language
from alarino_backend.parts_of_speech import PartOfSpeech
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


def add_word(
    language: Language,
    word_text: str,
    part_of_speech: Optional[PartOfSpeech] = None,
):
    """Insert a word, returning the existing row if (language, word) already
    exists. ``part_of_speech`` must be a PartOfSpeech enum value or None;
    arbitrary strings are no longer accepted (the DB-level
    ck_words_part_of_speech_valid CHECK would reject them anyway)."""
    word_text = normalize_word_text(word_text)

    if language == Language.YORUBA and not is_valid_yoruba_word(word_text):
        logger.debug(f"Invalid Yoruba word rejected: {word_text}")
        return None
    if language == Language.ENGLISH and not is_valid_english_word(word_text):
        logger.debug(f"Invalid English word rejected: {word_text}")
        return None

    existing_word = Word.query.filter_by(language=language, word=word_text).first()
    if existing_word:
        return existing_word
    pos_value = part_of_speech.value if part_of_speech is not None else None
    word = Word(language=language, word=word_text, part_of_speech=pos_value)
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

def _ensure_default_sense(word: Word) -> Sense:
    """Return a sense for the word, creating a default one if none exist.

    Phase 6b ensures every Translation has non-NULL source_sense_id and
    target_sense_id. The bulk-upload write path doesn't carry sense-level
    information today (the input format is just word→word pairs), so we
    default to the first sense if one exists, otherwise create one carrying
    the word's part_of_speech. Polysemy — multiple senses per word with
    distinct labels/definitions — is supported by the schema and will be
    populated by an explicit admin curation flow in a later feature.
    """
    word.w_id  # ensure attribute is loaded; flush if needed
    if word.w_id is None:
        db.session.flush()
    existing = (
        Sense.query
        .filter_by(word_id=word.w_id)
        .order_by(Sense.sense_id)
        .first()
    )
    if existing is not None:
        return existing
    sense = Sense(word_id=word.w_id, part_of_speech=word.part_of_speech)
    db.session.add(sense)
    db.session.flush()
    return sense


def create_translation(source: Word, target: Word):
    existing = Translation.query.filter_by(
        source_word_id=source.w_id,
        target_word_id=target.w_id
    ).first()
    if existing:
        return
    source_sense = _ensure_default_sense(source)
    target_sense = _ensure_default_sense(target)
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
