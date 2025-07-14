import json
import re

from sqlalchemy import false
from sqlalchemy.exc import IntegrityError

from data.seed_data_utils import add_word, create_translation, upload_data_in_batches
from main import app, logger
from main.db_models import db
from main.languages import Language


def process_translation(english_word:str, yoruba_translations:list, part_of_speech:str =None) -> list:
    invalid_entries = []
    # remove all substrings enclosed in parentheses
    english_word = re.sub(r'\([^)]*\)', '', english_word).strip()

    if part_of_speech:
        eng_word_obj = add_word(Language.ENGLISH, english_word, part_of_speech=part_of_speech)
    else:
        eng_word_obj = add_word(Language.ENGLISH, english_word)

    if eng_word_obj is None:
        invalid_entries.append({
            "english": english_word,
            "yoruba": ", ".join(yoruba_translations),
            "reason": "Invalid English word"
        })
        return invalid_entries

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
        db.session.flush()
        create_translation(eng_word_obj, yor_word_obj)
    return invalid_entries


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

            if not parts_of_speech:
                invalid_entries.extend(process_translation(english_word, yoruba_translations))
            else:
                for pos in parts_of_speech:
                    invalid_entries.extend(process_translation(english_word, yoruba_translations, pos))

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

        return invalid_entries


def write_data():
    with open("datasets/en-yo-dataset.json", "r", encoding="utf-8") as f:
        entries = json.load(f)
    logger.info(f"Finished loading data file with {len(entries)} translations")

    # Set the starting batch index. Change to > 0 to resume a failed run.
    batch_start = 0
    upload_data_in_batches(
        entries=entries,
        upload_func=write_data_batch,
        invalid_files_prefix="invalid_datasets/translations/invalid_entries_batch",
        batch_size=500, batch_start=batch_start
    )


if __name__ == '__main__':
    write_data()
