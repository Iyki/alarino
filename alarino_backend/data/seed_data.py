import json
import re
import unicodedata

from main.languages import Language
from main.db_models import db, Word, Translation
from sqlalchemy.exc import IntegrityError
from main import app, logger

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

def is_valid_yoruba_word(word: str) -> bool:
    """
    Validates if a word contains only valid Yoruba characters
    Args:
        word: The word to validate
    Returns:
        bool: Whether the word contains only valid Yoruba characters
    """
    if not word:
        return False
    word = word.strip().lower()

    # Define valid Yoruba character sets
    consonants = "bdfghjklmnprstwygbṣ" # Standard consonants (excluding c, q, v, x, z)
    vowels = "aàáeèéẹẹ̀ẹ́iìíoòóọọ̀ọ́uùú" # Standard vowels with tone marks
    nasal_vowels = "mḿm̀nńǹ" # Nasal vowels with tone marks
    extras = "'- " # Additional valid characters

    valid_chars = consonants + vowels + nasal_vowels + extras
    valid_chars = unicodedata.normalize('NFC', valid_chars)

    escaped_chars = re.escape(valid_chars)
    pattern = f"^[{escaped_chars}]+$"

    return bool(re.match(pattern, word, re.UNICODE))

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


def write_data_batch(entries: list, batch_id: int) -> list[dict]:
    with app.app_context():
        batch_start = 0
        batch_end = len(entries) - 1
        invalid_entries = []

        for i, entry in enumerate(entries):
            english_word = entry.get("english_word", "").strip().lower()
            parts_of_speech = entry.get("parts_of_speech", [])
            yoruba_text = entry.get("yoruba_translations", "")

            if not english_word or not yoruba_text:
                continue

            yoruba_translations = [y.strip() for y in yoruba_text.split(",") if y.strip()]

            for pos in parts_of_speech:
                english_word = re.sub(r'\([^)]*\)', '', english_word).strip()
                eng_word_obj = add_word(Language.ENGLISH, english_word, part_of_speech=pos)
                if eng_word_obj is None:
                    invalid_entries.append({
                        "english": english_word,
                        "yoruba": yoruba_word,
                        "reason": "Invalid English word"
                    })
                    continue

                for yoruba_word in yoruba_translations:
                    yoruba_word = re.sub(r'\([^)]*\)', '', yoruba_word).strip()
                    yor_word_obj = add_word(Language.YORUBA, yoruba_word)
                    if yor_word_obj is None:
                        invalid_entries.append({
                            "english": english_word,
                            "yoruba": yoruba_word,
                            "reason": "Invalid Yoruba word"
                        })
                        continue

                    db.session.flush()  # ensures .id is set
                    create_translation(eng_word_obj, yor_word_obj)

            if i == batch_start:
                logger.info(f"Starting at: {english_word} | POS: {parts_of_speech} | Yoruba: {yoruba_text}")
            if i >= batch_end:
                logger.info(f"Ending at: {english_word} | POS: {parts_of_speech} | Yoruba: {yoruba_text}")

        try:
            db.session.commit()
            logger.info("Batch data committed successfully.")
            logger.warning(f"Rejected {len(invalid_entries)} invalid entries.")
        except IntegrityError as e:
            db.session.rollback()
            logger.exception("Integrity Error:", e)

        if invalid_entries:
            batch_file = f"invalid_datasets/invalid_entries_batch_{batch_id}.json"
            with open(batch_file, "w", encoding="utf-8") as f:
                json.dump(invalid_entries, f, indent=2, ensure_ascii=False)
            logger.warning(f"Wrote {len(invalid_entries)} invalid entries to {batch_file}")

        return invalid_entries


def write_data():
    with open("datasets/en-yo-dataset.json", "r", encoding="utf-8") as f:
        entries = json.load(f)
    logger.info(f"Finished loading data file with {len(entries)} items")

    all_invalid_entries = []

    batch_start = 0
    batch_size = 500
    while batch_start < len(entries):
        end = min(batch_start + batch_size, len(entries))
        batch_id = (batch_start // batch_size) + 1

        logger.info(f"Processing batch {batch_start} to {end}")
        batch_invalids = write_data_batch(entries[batch_start:end], batch_id)
        all_invalid_entries.extend(batch_invalids)
        batch_start += batch_size

    if all_invalid_entries:
        with open("invalid_datasets/invalid_yoruba_entries_all.json", "w", encoding="utf-8") as f:
            json.dump(all_invalid_entries, f, indent=2, ensure_ascii=False)
        logger.info(f"Wrote {len(all_invalid_entries)} total invalid entries.")

    logger.info("Finished processing all data.")


if __name__ == '__main__':
    write_data()