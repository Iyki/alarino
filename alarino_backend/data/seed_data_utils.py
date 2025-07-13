import json
import re
import unicodedata
from typing import Callable

from main import logger
from main.db_models import Proverb, db, Word, Translation
from main.languages import Language

# Define valid Yoruba character sets
_YORUBA_CONSONANTS = "bdfghjklmnprstwygbṣ"  # Standard consonants (excluding c, q, v, x, z)
_YORUBA_VOWELS = "aàáeèéẹẹ̀ẹ́iìíoòóọọ̀ọ́uùú"  # Standard vowels with tone marks
_YORUBA_NASAL_VOWELS = "mḿm̀nńǹ"  # Nasal vowels with tone marks
_YORUBA_CHARACTER_SET = _YORUBA_CONSONANTS + _YORUBA_VOWELS + _YORUBA_NASAL_VOWELS


def add_word(language: Language, word_text: str, part_of_speech: str = None):
    word_text = word_text.strip().strip(" ,.?!()").lower()
    word_text = unicodedata.normalize('NFC', word_text)

    if language == Language.YORUBA and not is_valid_yoruba_word(word_text):
        logger.debug(f"Invalid Yoruba word rejected: {word_text}")
        return None
    if language == Language.ENGLISH and not is_valid_english_word(word_text):
        logger.debug(f"Invalid English word rejected: {word_text}")
        return None

    existing_word = Word.query.filter_by(language=language, word=word_text).first()
    if existing_word:
        return existing_word
    word = Word(language=language, word=word_text, part_of_speech=part_of_speech)
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
    logger.info(f"Added proverb: '{yoruba_proverb}'")

    # Extract and add individual words
    yoruba_words = re.findall(r'\b\w+\b', yoruba_proverb)
    english_words = re.findall(r'\b\w+\b', english_proverb)

    for word in yoruba_words:
        add_word(language=Language.YORUBA, word_text=word)

    for word in english_words:
        add_word(language=Language.ENGLISH, word_text=word)


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
    text = text.strip().lower()
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
    word = word.strip().lower()
    if not word:
        return False

    # Simple regex pattern for English text (letters, apostrophes, hyphens, spaces)
    pattern = r'^[a-z\'\- ]+$'
    return bool(re.match(pattern, word, re.UNICODE))


def create_translation(source: Word, target: Word):
    existing = Translation.query.filter_by(
        source_word_id=source.w_id,
        target_word_id=target.w_id
    ).first()
    if existing:
        return
    translation = Translation(source_word=source, target_word=target)
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
            batch_file = f"{invalid_files_prefix}_{batch_id}.json"
            with open(batch_file, "w", encoding="utf-8") as f:
                json.dump(batch_invalids, f, indent=2, ensure_ascii=False)
            logger.warning(f"Wrote {len(batch_invalids)} invalid entries to {batch_file}")

        batch_start += batch_size

    if all_invalid_entries:
        invalid_file_path = f"{invalid_files_prefix}_all.json"
        with open(invalid_file_path, "w", encoding="utf-8") as f:
            json.dump(all_invalid_entries, f, indent=2, ensure_ascii=False)
        logger.info(f"Wrote {len(all_invalid_entries)} total invalid entries to {invalid_file_path}")

    logger.info(f"Finished processing all entries. Skipped {len(all_invalid_entries)} invalid entries.")
