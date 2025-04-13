import json

from shared_utils import Language
from main.db_models import db, Word, Translation
from sqlalchemy.exc import IntegrityError
from main import app, logger

def add_word(language: str, word_text: str, part_of_speech: str = None):
    word_text = word_text.strip().lower()
    existing_word = Word.query.filter_by(language=language, word=word_text).first()
    if existing_word:
        return existing_word
    word = Word(language=language, word=word_text, part_of_speech=part_of_speech)
    db.session.add(word)
    return word


def create_translation(source: Word, target: Word):
    existing = Translation.query.filter_by(
        source_word_id=source.w_id,
        target_word_id=target.w_id
    ).first()
    if existing:
        return
    translation = Translation(source_word=source, target_word=target)
    db.session.add(translation)


def write_data_batch(entries: list):
    with app.app_context():
        batch_start = 0
        batch_end = len(entries) - 1

        for i, entry in enumerate(entries):
            english_word = entry.get("english_word", "").strip().lower()
            parts_of_speech = entry.get("parts_of_speech", [])
            yoruba_text = entry.get("yoruba_translations", "")

            if not english_word or not yoruba_text:
                continue

            yoruba_translations = [y.strip() for y in yoruba_text.split(",") if y.strip()]

            for pos in parts_of_speech:
                eng_word_obj = add_word(Language.ENGLISH, english_word, part_of_speech=pos)

                for yoruba_word in yoruba_translations:
                    yor_word_obj = add_word(Language.YORUBA, yoruba_word)
                    db.session.flush()  # ensures .id is set
                    create_translation(eng_word_obj, yor_word_obj)

            if i == batch_start:
                logger.info(f"Starting at: {english_word} | POS: {parts_of_speech} | Yoruba: {yoruba_text}")
            if i >= batch_end:
                logger.info(f"Ending at: {english_word} | POS: {parts_of_speech} | Yoruba: {yoruba_text}")
                break

        try:
            db.session.commit()
            logger.info("Word data seeded successfully.")
        except IntegrityError as e:
            db.session.rollback()
            logger.error("Integrity Error:", e)
            # raise e


def write_data():
    with open("./en-yo-dataset.json", "r", encoding="utf-8") as f:
        entries = json.load(f)
    logger.info(f"finished loading data file with {len(entries)} items")

    batch_start = 0
    batch_size = 500
    while batch_start < len(entries):
        end = min(batch_start+batch_size, len(entries))
        logger.info(f"Processing batch {batch_start} to {end}")
        write_data_batch(entries[batch_start:end])
        batch_start += batch_size

    logger.info("Finished processing all data.")


if __name__ == '__main__':
    write_data()