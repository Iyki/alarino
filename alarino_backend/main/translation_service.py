#translation_service.py
from datetime import date
from main import logger
from response import APIResponse, ResponseData
from db_models import Word, DailyWord, Translation, MissingTranslation
from languages import Language
from typing import Tuple, Dict, Optional, List, Union

def translate(db, text: str, source: Language, target: Language, addr: str, user_agent: str) -> tuple[dict, int]:
    text = text.strip().lower()
    if not text:
        return APIResponse.error("Text must not be empty.", 400).as_response()

    source_word = Word.query.filter_by(language=source, word=text).first()
    if not source_word:
        # Log to missing_translations
        log_missing_translation(db, text, source, target, addr, user_agent)
        return APIResponse.error("Word not found.", 404).as_response()

    translations = (
        Translation.query
        .filter_by(source_word_id=source_word.w_id)
        .join(Word, Translation.target_word_id == Word.w_id)
        .filter(Word.language == target)
        .all()
    )
    if not translations:
        log_missing_translation(db, text, source, target, addr, user_agent)
        return APIResponse.error("Word found but translation not available.", 404).as_response()

    translated_words = [t.target_word.word for t in translations]
    logger.info(f"[Translated '{text}' from {source} to {target}]")

    response_data = ResponseData(
        translation=translated_words,
        source_word=source_word.word,
        to_language=target
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

def find_single_word_with_translation(db) -> Optional[Tuple[Word, Word]]:
    """
    Find a random Yoruba word that has an English translation.
    Returns a tuple of (yoruba_word, english_word) or None if no suitable word is found.
    """
    # Get list of previously used word IDs to avoid repetition
    used_word_ids = db.session.query(DailyWord.word_id).all()
    used_ids_set = set(word_id for (word_id,) in used_word_ids)

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
        response_data = ResponseData([yoruba_word], english_word, Language.YORUBA)
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

                response_data = ResponseData([yoruba_word], english_word, Language.YORUBA)
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

            response_data = ResponseData([yoruba_word.word], english_word.word, Language.YORUBA)
            return APIResponse.success("Word of the day fetched successfully.", response_data).as_response()

        # If we've exhausted our attempts and still haven't found a word with translation
        return APIResponse.error("Could not find a word with an English translation after multiple attempts", 500).as_response()

    except Exception as e:
        return APIResponse.error(str(e), 500).as_response()

