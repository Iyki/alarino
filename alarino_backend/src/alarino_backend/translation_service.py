# translation_service.py
import csv
import io
from datetime import date
import threading
from typing import Tuple, Dict, Optional

from alarino_backend.data.seed_data_utils import add_word, create_translation, is_valid_english_word, is_valid_yoruba_word, normalize_word_text
from alarino_backend.db_models import Word, DailyWord, Example, Sense, Translation, MissingTranslation, Proverb, ProverbWord
from alarino_backend.languages import Language
from alarino_backend.llm_service import get_llm_service
from alarino_backend.response import (
    APIResponse,
    BulkUploadResponseData,
    ProverbResponseData,
    SenseGroup,
    TranslationInSenseGroup,
    TranslationResponseData,
    WordOfTheDayResponseData,
)
from alarino_backend.runtime import logger


def translate_llm(text: str, source: Language, target: Language) -> tuple[dict, int]:
    """Translates text using the LLM service."""
    text = normalize_word_text(text)
    if not text:
        return APIResponse.error("Text must not be empty.", 400).as_response()

    llm_service = get_llm_service()
    if not llm_service:
        return APIResponse.error("LLM service not configured.", 500).as_response()

    try:
        translation = llm_service.get_translation(text, source.value, target.value)
        if not translation:
            return APIResponse.error("Translation not found.", 404).as_response()

        response_data = TranslationResponseData(
            translation=translation,
            source_word=text,
            to_language=target
        )
        return APIResponse.success("Translation successful.", response_data).as_response()
    except Exception as e:
        logger.error(f"Error getting LLM translation: {e}")
        return APIResponse.error("An error occurred during translation.", 500).as_response()


def translate(db, text: str, source: Language, target: Language, user_agent: str) -> tuple[dict, int]:
    text = normalize_word_text(text)
    if not text:
        return APIResponse.error("Text must not be empty.", 400).as_response()

    source_word = Word.query.filter_by(language=source, text=text).first()
    if not source_word:
        log_missing_translation(db, text, source, target, user_agent)
        return APIResponse.error("Word not found.", 404).as_response()

    # Bidirectional lookup. Translation is stored as a directed edge — the
    # curator added it as source→target — but a user querying in either
    # direction should find a match if either direction was curated. Match the
    # source_word on EITHER column and return the opposite-side word, filtered
    # by the requested target language and deduped by w_id so a pair that
    # happens to be curated in both directions doesn't return duplicates.
    translations = (
        Translation.query
        .filter(
            (Translation.source_word_id == source_word.w_id)
            | (Translation.target_word_id == source_word.w_id)
        )
        .all()
    )
    seen_word_ids: set[int] = set()
    translated_words: list[str] = []
    # Group results by the *looked-up* word's sense (Phase 6c). For each
    # matching translation, the looked-up side may be either source or target;
    # the "my sense" is whichever sense FK sits on the same side. Default
    # bucket (sense_id None) catches translations whose sense FKs are NULL —
    # shouldn't happen post-Phase-6b for new data but kept as a safety net.
    sense_buckets: dict[Optional[int], SenseGroup] = {}
    for translation in translations:
        if translation.source_word_id == source_word.w_id:
            other = translation.target_word
            my_sense = translation.source_sense
            other_sense = translation.target_sense
        else:
            other = translation.source_word
            my_sense = translation.target_sense
            other_sense = translation.source_sense

        if other.language != target.value or other.w_id in seen_word_ids:
            continue
        seen_word_ids.add(other.w_id)
        translated_words.append(other.text)

        sense_key = my_sense.sense_id if my_sense is not None else None
        if sense_key not in sense_buckets:
            sense_buckets[sense_key] = SenseGroup(
                label=my_sense.sense_label if my_sense else None,
                definition=my_sense.definition if my_sense else None,
                register=my_sense.register if my_sense else None,
                domain=my_sense.domain if my_sense else None,
                part_of_speech=(my_sense.part_of_speech if my_sense else None),
            )
        examples = _examples_for_sense_pair(my_sense, other_sense)
        sense_buckets[sense_key].translations.append(
            TranslationInSenseGroup(
                word=other.text,
                note=translation.note,
                provenance=translation.provenance,
                examples=examples,
            )
        )

    if not translated_words:
        log_missing_translation(db, text, source, target, user_agent)
        return APIResponse.error("Word found but translation not available.", 404).as_response()

    logger.info(f"[Translated '{text}' from {source} to {target}]")

    # Sense groups are ordered by first-seen sense_id for deterministic output;
    # the default-sense bucket (key None) sorts to the end if present.
    ordered_groups = sorted(
        sense_buckets.items(),
        key=lambda item: (item[0] is None, item[0] or 0),
    )
    response_data = TranslationResponseData(
        translation=translated_words,
        source_word=source_word.text,
        to_language=target,
        senses=[group for _, group in ordered_groups],
    )
    return APIResponse.success("Translation successful.", response_data).as_response()


def _examples_for_sense_pair(
    source_sense: Optional[Sense], target_sense: Optional[Sense]
) -> list[dict]:
    """Return Example rows attached to the given (source_sense, target_sense)
    pair, formatted as {source, target} dicts. If either sense is None, returns
    [] — Phase 6b backfilled examples to point at sense pairs but a future
    raw-SQL inserted Example without sense FKs would not match. Read paths
    surface only sense-attached examples; legacy examples linked only by
    translation_id surface through Phase 6c-incompatible read paths (none
    exposed today) until 6d drops translation_id."""
    if source_sense is None or target_sense is None:
        return []
    rows = (
        Example.query
        .filter_by(
            source_sense_id=source_sense.sense_id,
            target_sense_id=target_sense.sense_id,
        )
        .all()
    )
    return [
        {"source": row.example_source, "target": row.example_target}
        for row in rows
    ]


def log_missing_translation(db, text, source_lang, target_lang, user_agent):
    # Atomic upsert: on first hit insert with user_agent and hit_count=1; on
    # subsequent hits increment hit_count without overwriting user_agent. The
    # previous read-modify-write pattern lost concurrent increments under load.
    dialect_name = db.session.get_bind().dialect.name
    if dialect_name == "postgresql":
        from sqlalchemy.dialects.postgresql import insert
    elif dialect_name == "sqlite":
        from sqlalchemy.dialects.sqlite import insert
    else:
        raise NotImplementedError(
            f"log_missing_translation upsert not implemented for dialect {dialect_name!r}"
        )

    table = MissingTranslation.__table__
    stmt = insert(table).values(
        text=text,
        source_language=source_lang,
        target_language=target_lang,
        user_agent=user_agent,
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=["text", "source_language", "target_language"],
        set_={"hit_count": table.c.hit_count + 1},
    )
    db.session.execute(stmt)
    db.session.commit()


def _derive_yoruba_english(translation: Translation) -> Tuple[Word, Word]:
    """Return (yoruba_word, english_word) for a translation, regardless of
    which column each language sits in. Translation rows are directed (Phase 4
    keeps them that way), so the Yoruba/English assignment cannot be derived
    from source/target position — only from Word.language."""
    sw, tw = translation.source_word, translation.target_word
    if sw.language == Language.YORUBA.value:
        return sw, tw
    return tw, sw


def find_random_unused_translation(db, can_reuse: bool = True) -> Optional[Translation]:
    """Pick a random Translation that hasn't been used as a daily word, with
    the Yoruba side restricted to single-word entries (the daily-word feature
    spotlights individual Yoruba words, not phrases). With can_reuse=True the
    used-set filter is skipped — same semantic as the previous version.

    Phase 4 keeps Translation as a directed edge, so the Yoruba side may sit
    on either source_word or target_word. The single-word filter is applied
    in Python rather than SQL because the "yoruba side is on one of two
    columns" condition is awkward to express portably; alarino's translations
    table is small enough that loading the candidate set is negligible."""
    query = Translation.query
    if not can_reuse:
        used_set = {
            t_id for (t_id,) in db.session.query(DailyWord.translation_id).all()
        }
        if used_set:
            query = query.filter(~Translation.t_id.in_(used_set))

    yoruba = Language.YORUBA.value
    for translation in query.order_by(db.func.random()).all():
        yo_word = (
            translation.source_word
            if translation.source_word.language == yoruba
            else translation.target_word
        )
        if " " not in yo_word.text:
            return translation
    return None


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
            yoruba_word_obj, english_word_obj = _derive_yoruba_english(existing.translation)
            yoruba_word = yoruba_word_obj.text
            english_word = english_word_obj.text
            daily_word_cache[today] = (yoruba_word, english_word)

            response_data = WordOfTheDayResponseData(yoruba_word=yoruba_word, english_word=english_word)
            return APIResponse.success("Word of the day fetched from database.", response_data).as_response()

        # Pick a fresh translation for today.
        translation = find_random_unused_translation(db)
        if translation is None:
            return APIResponse.error(
                "Could not find a translation suitable for the daily word.",
                500,
            ).as_response()

        yoruba_word_obj, english_word_obj = _derive_yoruba_english(translation)
        daily = DailyWord(translation=translation)
        db.session.add(daily)
        db.session.commit()
        daily_word_cache[today] = (yoruba_word_obj.text, english_word_obj.text)

        response_data = WordOfTheDayResponseData(
            yoruba_word=yoruba_word_obj.text, english_word=english_word_obj.text
        )
        return APIResponse.success("Word of the day fetched successfully.", response_data).as_response()

    except Exception as e:
        return APIResponse.error(str(e), 500).as_response()


def get_proverbs_containing(db, language: Language, word_text: str) -> list[Proverb]:
    """Return every Proverb whose `proverb_words` join entries reference a Word
    matching (language, word_text). Returns an empty list if no match.

    Phase 3 backfill is best-effort: proverbs that predate Phase 3 are linked
    only if their tokenized words match an existing Word row at backfill time.
    Misses are silently skipped, so a missing result here does not necessarily
    mean the proverb does not contain the word — it may just predate the link.
    """
    word_text = normalize_word_text(word_text)
    if not word_text:
        return []
    return (
        Proverb.query
        .join(ProverbWord, ProverbWord.proverb_id == Proverb.p_id)
        .join(Word, Word.w_id == ProverbWord.word_id)
        .filter(Word.language == language, Word.text == word_text)
        .distinct()
        .all()
    )


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
