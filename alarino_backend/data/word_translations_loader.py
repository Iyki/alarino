import json
import re

from sqlalchemy.exc import IntegrityError

from data.seed_data import add_word, create_translation
from main import app, logger
from main.db_models import db
from main.languages import Language

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
