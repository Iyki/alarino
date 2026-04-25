"""Tests for the PartOfSpeech enum + CHECK constraint on Sense.part_of_speech.

Phase 6b POS-check (revision c4b8e1a5d927) added CHECK constraints on both
Word.part_of_speech and Sense.part_of_speech. Phase 6d (d8a3f0b71e5c)
dropped Word.part_of_speech entirely — POS lives only on Sense now."""

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


def test_word_no_longer_has_part_of_speech_column():
    # Phase 6d removed it. Set POS on the Sense instead.
    assert "part_of_speech" not in {c.name for c in Word.__table__.columns}


@pytest.mark.parametrize("pos", list(PartOfSpeech))
def test_sense_check_constraint_accepts_every_canonical_pos_value(db_app, pos):
    word = Word(language="yo", text=f"w-{pos.value}")
    db.session.add(word)
    db.session.flush()
    db.session.add(Sense(word_id=word.w_id, part_of_speech=pos.value))
    db.session.commit()
    stored = Sense.query.filter_by(word_id=word.w_id).one()
    assert stored.part_of_speech == pos.value


def test_sense_check_constraint_rejects_non_canonical_pos(db_app):
    word = Word(language="yo", text="ile")
    db.session.add(word)
    db.session.flush()
    db.session.add(Sense(word_id=word.w_id, part_of_speech="bogus_pos"))
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_sense_accepts_null_part_of_speech(db_app):
    word = Word(language="yo", text="ile")
    db.session.add(word)
    db.session.flush()
    db.session.add(Sense(word_id=word.w_id))
    db.session.commit()
    assert Sense.query.one().part_of_speech is None


def test_add_word_no_longer_takes_part_of_speech_kwarg():
    # Sanity: passing part_of_speech to add_word should be a TypeError now.
    # POS is sense-scoped post-Phase-6d.
    with pytest.raises(TypeError):
        add_word(language=Language.YORUBA, word_text="ile", part_of_speech=PartOfSpeech.NOUN)
