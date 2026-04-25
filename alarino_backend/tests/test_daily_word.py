"""Tests for the Phase 5 DailyWord normalization: storage now uses
translation_id and read paths derive Yoruba/English from Word.language."""

from datetime import date

import pytest

import alarino_backend.app as app_module
import alarino_backend.translation_service as translation_service
from alarino_backend import db
from alarino_backend.db_models import DailyWord, Translation, Word


@pytest.fixture
def db_app():
    app = app_module.create_app()
    app.config["TESTING"] = True
    with app.app_context():
        db.create_all()
        try:
            yield app
        finally:
            db.session.remove()
            db.drop_all()


def _seed_translation(en: str, yo: str, *, en_to_yo: bool = True) -> Translation:
    # Route through create_translation so sense FKs are populated (Phase 6d
    # made them NOT NULL; constructing Translation directly without sense FKs
    # would fail the constraint).
    from alarino_backend.data.seed_data_utils import create_translation

    en_word = Word(language="en", text=en)
    yo_word = Word(language="yo", text=yo)
    db.session.add_all([en_word, yo_word])
    db.session.flush()
    src, tgt = (en_word, yo_word) if en_to_yo else (yo_word, en_word)
    create_translation(src, tgt)
    db.session.commit()
    return Translation.query.filter_by(
        source_word_id=src.w_id, target_word_id=tgt.w_id
    ).one()


def test_daily_word_no_longer_has_word_id_or_en_word_id_columns():
    columns = {c.name for c in DailyWord.__table__.columns}
    assert "word_id" not in columns
    assert "en_word_id" not in columns
    assert "translation_id" in columns


def test_daily_word_translation_id_is_not_unique():
    # Originally Phase 5 made translation_id UNIQUE, but that broke
    # find_random_unused_translation's default can_reuse=True path (a
    # past daily word being re-picked would crash on the constraint).
    # Phase 7 bug-fix relaxed it. Date uniqueness still ensures one
    # daily word per date.
    column = DailyWord.__table__.c.translation_id
    assert column.nullable is False
    assert column.unique is not True


def test_get_word_of_the_day_picks_unused_translation_when_db_empty(db_app):
    t = _seed_translation("hello", "bawo")
    cache = {}

    response, status = translation_service.get_word_of_the_day(db, cache)

    assert status == 200
    assert response["data"]["yoruba_word"] == "bawo"
    assert response["data"]["english_word"] == "hello"
    # Persisted under the expected translation_id.
    daily = DailyWord.query.one()
    assert daily.translation_id == t.t_id
    assert daily.date == date.today()


def test_get_word_of_the_day_works_when_translation_was_curated_yo_to_en(db_app):
    # Phase 4 keeps directed storage. The daily-word read path must derive
    # the Yoruba/English sides from Word.language, NOT from positional
    # source/target. Seed a translation curated in the YO→EN direction
    # (yoruba is source_word_id, english is target_word_id) and verify the
    # response still shows the Yoruba side as yoruba_word.
    _seed_translation("hello", "bawo", en_to_yo=False)
    cache = {}

    response, status = translation_service.get_word_of_the_day(db, cache)

    assert status == 200
    assert response["data"]["yoruba_word"] == "bawo"
    assert response["data"]["english_word"] == "hello"


def test_get_word_of_the_day_returns_existing_daily_word_when_present(db_app):
    t = _seed_translation("hello", "bawo")
    db.session.add(DailyWord(translation_id=t.t_id, date=date.today()))
    db.session.commit()
    cache = {}

    response, status = translation_service.get_word_of_the_day(db, cache)

    assert status == 200
    assert response["data"]["yoruba_word"] == "bawo"
    assert response["data"]["english_word"] == "hello"
    # No additional row created.
    assert DailyWord.query.count() == 1


def test_find_random_unused_translation_excludes_used_translations(db_app):
    t1 = _seed_translation("hello", "bawo")
    t2 = _seed_translation("house", "ile")
    db.session.add(DailyWord(translation_id=t1.t_id, date=date(2024, 1, 1)))
    db.session.commit()

    selected = translation_service.find_random_unused_translation(db, can_reuse=False)
    assert selected is not None
    assert selected.t_id == t2.t_id


def test_find_random_unused_translation_skips_multiword_yoruba_phrases(db_app):
    # Daily-word feature should only pick single-word Yoruba entries.
    _seed_translation("phrase", "ile mi")
    selected = translation_service.find_random_unused_translation(db)
    assert selected is None


def test_same_translation_can_be_daily_word_on_different_dates(db_app):
    # P1a regression test: previously a UNIQUE on translation_id rejected
    # the second insert and made get_word_of_the_day 500 on its second-ever
    # call against a fresh DB. After the Phase 7 bug-fix, the same
    # translation can be the daily word on different dates.
    t = _seed_translation("hello", "bawo")
    db.session.add(DailyWord(translation_id=t.t_id, date=date(2024, 1, 1)))
    db.session.add(DailyWord(translation_id=t.t_id, date=date(2024, 1, 2)))
    db.session.commit()

    assert DailyWord.query.count() == 2


def test_get_word_of_the_day_succeeds_when_only_translation_was_already_used(db_app):
    # Exact P1a repro from the review: seed one old DailyWord, then call
    # get_word_of_the_day. The picker defaults to can_reuse=True so it can
    # legitimately return the same translation. The endpoint must not 500.
    t = _seed_translation("hello", "bawo")
    db.session.add(DailyWord(translation_id=t.t_id, date=date(2024, 1, 1)))
    db.session.commit()
    cache = {}

    response, status = translation_service.get_word_of_the_day(db, cache)
    assert status == 200
    assert response["data"]["yoruba_word"] == "bawo"
    # Two rows: the seeded historical one, plus today's.
    assert DailyWord.query.count() == 2


def test_translation_id_uniqueness_is_not_enforced_at_db_level(db_app):
    # Belt-and-suspenders against re-introducing the unique constraint:
    # inserting two daily_words pointing at the same translation_id must
    # not raise even at the DB level.
    t = _seed_translation("hello", "bawo")
    db.session.add(DailyWord(translation_id=t.t_id, date=date(2024, 1, 1)))
    db.session.add(DailyWord(translation_id=t.t_id, date=date(2024, 1, 2)))
    db.session.commit()  # must not raise IntegrityError
