import json
from pathlib import Path

from sqlalchemy.exc import IntegrityError

from alarino_backend import create_app
from alarino_backend.data.seed_data_utils import add_proverb, is_valid_english_text, is_valid_yoruba_text, upload_data_in_batches
from alarino_backend.db_models import db
from alarino_backend.runtime import logger

DATA_DIR = Path(__file__).resolve().parent


def load_proverbs_from_file(file_path: str):
    """
    Reads a JSONL file and yields each line as a dictionary.
    Args:
        file_path: The path to the JSONL file.
    Yields:
        A dictionary for each line in the file.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                logger.warning(f"Skipping invalid JSON line: {line.strip()}")
                continue


def seed_proverbs_batch(entries: list, batch_id: int, app=None) -> list:
    """
    Seeds a batch of proverbs into the database.
    Args:
        entries: A list of proverb entries.
        batch_id: The identifier for the current batch.
    Returns:
        A list of invalid entries found in the batch.
    """
    invalid_entries = []
    app = app or create_app()

    with app.app_context():
        for entry in entries:
            yoruba_text = entry.get("yoruba", "").strip()
            english_text = entry.get("english", "").strip()

            if not yoruba_text or not english_text:
                invalid_entries.append({**entry, "reason": "Missing yoruba or english text"})
                continue

            if not is_valid_yoruba_text(yoruba_text):
                reason = "Invalid Yoruba text"
                logger.warning(f"Skipping invalid proverb: {yoruba_text} ({reason})")
                invalid_entries.append({**entry, "reason": reason})
                continue
            if not is_valid_english_text(english_text):
                reason = "Invalid English text"
                logger.warning(f"Skipping invalid proverb: {english_text} ({reason})")
                invalid_entries.append({**entry, "reason": reason})
                continue

            add_proverb(yoruba_text, english_text)

        try:
            db.session.commit()
            logger.info(f"Batch {batch_id}: Committed {len(entries) - len(invalid_entries)} proverbs.")
        except IntegrityError:
            db.session.rollback()
            logger.warning(f"Batch {batch_id}: IntegrityError, rolling back session.")

    return invalid_entries


def write_proverbs_data(app=None):
    """
    Main function to seed proverbs from the train.jsonl file.
    """
    file_path = DATA_DIR / "datasets" / "train.jsonl"
    proverbs = list(load_proverbs_from_file(file_path))
    logger.info(f"Loaded {len(proverbs)} proverbs from {file_path}")

    app = app or create_app()

    # Set the starting batch index. Change to > 0 to resume a failed run.
    batch_start = 0
    upload_data_in_batches(
        entries=proverbs,
        upload_func=lambda entries, batch_id: seed_proverbs_batch(entries, batch_id, app),
        invalid_files_prefix=DATA_DIR / "invalid_datasets" / "proverbs" / "invalid_proverbs_batch",
        batch_size=500, batch_start=batch_start
    )


if __name__ == '__main__':
    write_proverbs_data()
