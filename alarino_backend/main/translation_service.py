# translation_service.py
import csv
import io
from datetime import date
import threading
from typing import Tuple, Dict, Optional

from main import logger
from main.db_models import Word, DailyWord, Translation, MissingTranslation, Proverb
from main.languages import Language
from main.llm_service import get_llm_service
from main.response import APIResponse, TranslationResponseData, WordOfTheDayResponseData, ProverbResponseData, BulkUploadResponseData
from data.seed_data_utils import add_word, create_translation, is_valid_english_word, is_valid_yoruba_word


def _get_llm_translation(text: str, source: Language, target: Language, result_container: dict):
    """Fetches experimental translation from the LLM service and stores it in the result_container."""
    llm_service = get_llm_service()
    translation = None
    if llm_service:
        try:
            translation = llm_service.get_translation(text, source.value, target.value)
        except Exception as e:
            logger.error(f"Error getting experimental translation: {e}")
    result_container['experimental'] = translation


def translate(db, text: str, source: Language, target: Language, addr: str, user_agent: str) -> tuple[dict, int]:
    text = text.strip().lower()
    if not text:
        return APIResponse.error("Text must not be empty.", 400).as_response()

    # --- Start Parallel Execution ---
    results = {}
    
    # Thread for LLM translation
    llm_thread = threading.Thread(target=_get_llm_translation, args=(text, source, target, results))
    llm_thread.start()

    # Main thread for database translation
    source_word = Word.query.filter_by(language=source, word=text).first()
    translated_words = []
    if source_word:
        translations = (
            Translation.query
            .filter_by(source_word_id=source_word.w_id)
            .join(Word, Translation.target_word_id == Word.w_id)
            .filter(Word.language == target)
            .all()
        )
        if translations:
            translated_words = [t.target_word.word for t in translations]
            logger.info(f"[Translated '{text}' from {source} to {target}]")
        else:
            log_missing_translation(db, text, source, target, addr, user_agent)
    else:
        log_missing_translation(db, text, source, target, addr, user_agent)
    
    # Wait for the LLM thread to complete
    llm_thread.join(timeout=0.5)
    # --- End Parallel Execution ---

    experimental_translation = results.get('experimental')

    if not translated_words and not experimental_translation:
        return APIResponse.error("Word not found.", 404).as_response()

    response_data = TranslationResponseData(
        translation=translated_words,
        source_word=text,
        to_language=target,
        experimental_translation=experimental_translation
    )
    return APIResponse.success("Translation successful.", response_data).as_response()


def log_missing_translation(db, text, source_lang, target_lang, addr, user_agent):
    existing = MissingTranslation.query.filter_by(
        text=text,
        source_language=source_lang,
        target_language=target_lang
    ).first()

    if existing:
        existing.hit_count += 1
    else:
        missing = MissingTranslation(
            text=text,
            source_language=source_lang,
            target_language=target_lang,
            user_ip=addr,
            user_agent=user_agent
        )
        db.session.add(missing)

    db.session.commit()


def find_single_word_with_translation(db, can_reuse=True) -> Optional[Tuple[Word, Word]]:
    """
    Find a random Yoruba word that has an English translation.
    Returns a tuple of (yoruba_word, english_word) or None if no suitable word is found.
    """
    # Get list of previously used word IDs to avoid repetition
    used_word_ids = db.session.query(DailyWord.word_id).all()
    used_ids_set = set() if can_reuse else set(word_id for (word_id,) in used_word_ids)

    # Filter Yoruba words that are single-word and not used before
    selected_word = (
        Word.query
        .filter(Word.language == Language.YORUBA)
        .filter(~Word.word.contains(" "))
        .filter(~Word.w_id.in_(used_ids_set))
        .order_by(db.func.random())
        .first()
    )

    if not selected_word:
        return None

    # Find the English translations
    translations = (
        Translation.query
        .filter_by(target_word_id=selected_word.w_id)
        .join(Word, Translation.source_word_id == Word.w_id)
        .filter(Word.language == Language.ENGLISH)
        .all()
    )

    if not translations:
        return None

    # Get the first English translation
    english_word = translations[0].source_word
    return selected_word, english_word


def get_word_of_the_day(db, daily_word_cache: Dict[date, Tuple[str, str]]) -> Tuple[Dict, int]:
    """
    Get the word of the day, either from cache, database, or by selecting a new one.
    Args:
        db: SQLAlchemy database instance?
        daily_word_cache: Cache dictionary mapping dates to (yoruba_word, english_word) tuples
    Returns:
        An API response tuple (response_dict, status_code)
    """
    today = date.today()
    # Check the in-memory cache first
    if today in daily_word_cache:
        yoruba_word, english_word = daily_word_cache[today]
        response_data = WordOfTheDayResponseData(yoruba_word=yoruba_word, english_word=english_word)
        return APIResponse.success("Word of the day fetched from cache.", response_data).as_response()
    try:
        # Check if already selected today in the DB
        existing = DailyWord.query.filter_by(date=today).first()
        if existing:
            yoruba_word = existing.word.word
            # Use the direct en_word relationship if available
            if existing.en_word:
                english_word = existing.en_word.word
                daily_word_cache[today] = (yoruba_word, english_word)

                response_data = WordOfTheDayResponseData(yoruba_word=yoruba_word, english_word=english_word)
                return APIResponse.success("Word of the day fetched from database.", response_data).as_response()
            else:
                # If no English word is associated, this is an error condition
                return APIResponse.error("Daily word has no English translation", 500).as_response()

        # Maximum attempts to find a word with translation
        max_attempts = 5
        for _ in range(max_attempts):
            word_pair = find_single_word_with_translation(db)
            if not word_pair:
                continue
            yoruba_word, english_word = word_pair

            # Save to daily_words with the English word reference
            daily = DailyWord(
                word=yoruba_word,
                en_word=english_word
            )
            db.session.add(daily)
            db.session.commit()
            # Cache it
            daily_word_cache[today] = (yoruba_word.word, english_word.word)

            response_data = WordOfTheDayResponseData(yoruba_word=yoruba_word.word, english_word=english_word.word)
            return APIResponse.success("Word of the day fetched successfully.", response_data).as_response()

        # If we've exhausted our attempts and still haven't found a word with translation
        return APIResponse.error("Could not find a word with an English translation after multiple attempts",
                                 500).as_response()

    except Exception as e:
        return APIResponse.error(str(e), 500).as_response()


def get_random_proverb(db):
    """
    Fetches a random proverb from the database.
    """
    try:
        proverb = Proverb.query.order_by(db.func.random()).first()
        if not proverb:
            return APIResponse.error("No proverbs found in the database.", 404).as_response()
        response_data = ProverbResponseData(
            yoruba_text=proverb.yoruba_text,
            english_text=proverb.english_text
        )
        return APIResponse.success("Proverb fetched successfully.", response_data).as_response()

    except Exception as e:
        logger.error(f"Error fetching random proverb: {e}")
        return APIResponse.error("An error occurred while fetching a proverb.", 500).as_response()


def _process_translation_pair(row: list, dry_run: bool, successful_pairs: list, failed_pairs: list):
    """
    Processes a single row from the bulk upload CSV.
    """
    original_line = ",".join(row)

    if len(row) != 2:
        failed_pairs.append({"line": original_line, "reason": "Invalid format: each line must contain exactly two values"})
        return

    english_word_str, yoruba_word_str = [item.strip().lower() for item in row]

    # Validation
    if not is_valid_english_word(english_word_str):
        failed_pairs.append({"line": original_line, "reason": f"Invalid English word: '{english_word_str}'"})
        return
    if not is_valid_yoruba_word(yoruba_word_str):
        failed_pairs.append({"line": original_line, "reason": f"Invalid Yoruba word: '{yoruba_word_str}'"})
        return

    if dry_run:
        # In dry_run, we just validate and report
        successful_pairs.append({"english": english_word_str, "yoruba": yoruba_word_str})
    else:
        # In a live run, we add the words and translation
        english_word_obj = add_word(language=Language.ENGLISH, word_text=english_word_str)
        yoruba_word_obj = add_word(language=Language.YORUBA, word_text=yoruba_word_str)
        
        if english_word_obj and yoruba_word_obj:
            create_translation(english_word_obj, yoruba_word_obj)
            successful_pairs.append({"english": english_word_str, "yoruba": yoruba_word_str})
        else:
            failed_pairs.append({"line": original_line, "reason": "Failed to process one or both words."})


def bulk_upload_words(db, text_input: str, dry_run: bool) -> tuple[dict, int]:
    """
    Bulk upload words from a comma-separated text input using seed data utils.
    """
    successful_pairs = []
    failed_pairs = []

    text_io = io.StringIO(text_input)
    reader = csv.reader(text_io)

    for row in reader:
        if not row:
            continue
        _process_translation_pair(row, dry_run, successful_pairs, failed_pairs)

    message = "Bulk upload validation completed"
    if not dry_run:
        db.session.commit()
        message = "Bulk upload process completed."

    response_data = BulkUploadResponseData(
        successful_pairs=successful_pairs,
        failed_pairs=failed_pairs,
        dry_run=dry_run
    )
    
    return APIResponse.success(message, response_data).as_response()
