import json
import re
import unicodedata

from sqlalchemy.exc import IntegrityError

from main import app, logger
from main.db_models import db, Word, Translation, Proverb
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


