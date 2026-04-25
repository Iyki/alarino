"""Tests for the PartOfSpeech enum + CHECK constraints (Phase 6b POS-check
sub-phase, revision c4b8e1a5d927)."""

import pytest
from sqlalchemy.exc import IntegrityError

import alarino_backend.app as app_module
from alarino_backend import db
from alarino_backend.data.seed_data_utils import add_word
from alarino_backend.db_models import Sense, Word
from alarino_backend.languages import Language
from alarino_backend.parts_of_speech import ALLOWED_POS_VALUES, PartOfSpeech


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


def test_allowed_pos_values_includes_all_enum_codes():
    enum_values = {p.value for p in PartOfSpeech}
    assert set(ALLOWED_POS_VALUES) == enum_values


def test_allowed_pos_values_is_sorted():
    # Sorted for stable CHECK-constraint SQL across migrations.
    assert list(ALLOWED_POS_VALUES) == sorted(ALLOWED_POS_VALUES)


def test_part_of_speech_str_returns_short_code():
    assert str(PartOfSpeech.NOUN) == "n"
    assert str(PartOfSpeech.INTERJECTION) == "interj"


@pytest.mark.parametrize("pos", list(PartOfSpeech))
def test_word_check_constraint_accepts_every_canonical_pos_value(db_app, pos):
    # Construct via model (not add_word) to bypass the Yoruba char-set
    # validator — we're exercising the DB-level CHECK constraint here.
    db.session.add(Word(language="yo", word=f"w-{pos.value}", part_of_speech=pos.value))
    db.session.commit()
    stored = Word.query.filter_by(word=f"w-{pos.value}").one()
    assert stored.part_of_speech == pos.value


def test_word_accepts_null_part_of_speech(db_app):
    add_word(language=Language.YORUBA, word_text="ile")
    db.session.commit()
    assert Word.query.filter_by(word="ile").one().part_of_speech is None


def test_add_word_persists_part_of_speech_enum(db_app):
    # Sanity that the seed_data_utils path forwards the enum value.
    add_word(language=Language.YORUBA, word_text="ile", part_of_speech=PartOfSpeech.NOUN)
    db.session.commit()
    assert Word.query.filter_by(word="ile").one().part_of_speech == "n"


def test_word_check_constraint_rejects_non_canonical_pos(db_app):
    db.session.add(Word(language="yo", word="ile", part_of_speech="Noun"))
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_sense_check_constraint_rejects_non_canonical_pos(db_app):
    word = Word(language="yo", word="ile")
    db.session.add(word)
    db.session.flush()
    db.session.add(Sense(word_id=word.w_id, part_of_speech="bogus_pos"))
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_sense_accepts_null_part_of_speech(db_app):
    word = Word(language="yo", word="ile")
    db.session.add(word)
    db.session.flush()
    db.session.add(Sense(word_id=word.w_id))
    db.session.commit()
    assert Sense.query.one().part_of_speech is None
