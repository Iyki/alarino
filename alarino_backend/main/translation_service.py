from main import logger
from response import APIResponse, ResponseData
from db_models import Word, Translation, MissingTranslation
from languages import Language

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
        language=target
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
