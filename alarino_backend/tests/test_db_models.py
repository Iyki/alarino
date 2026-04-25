"""Tests for db_models.py schema constraints introduced by the schema
evolution plan. These guard against regressions in column metadata; the
migrations themselves are exercised separately via `flask db upgrade`."""

import pytest
from sqlalchemy.exc import IntegrityError

import alarino_backend.app as app_module
from alarino_backend import db
from alarino_backend.db_models import (
    Example,
    MissingTranslation,
    Translation,
    Word,
)


TIMESTAMPED_MODELS = (Word, Translation, MissingTranslation, Example)


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


@pytest.mark.parametrize("model", TIMESTAMPED_MODELS, ids=lambda m: m.__name__)
def test_created_at_is_not_null_with_server_default(model):
    column = model.__table__.c.created_at
    assert column.nullable is False, (
        f"{model.__name__}.created_at must be NOT NULL"
    )
    assert column.server_default is not None, (
        f"{model.__name__}.created_at must have a server_default"
    )


def test_missing_translation_hit_count_is_not_null_with_default():
    column = MissingTranslation.__table__.c.hit_count
    assert column.nullable is False
    assert column.server_default is not None


def test_example_has_unique_constraint():
    constraint_names = {c.name for c in Example.__table__.constraints}
    assert "unique_example_per_translation" in constraint_names


def test_redundant_indexes_are_not_declared_on_models():
    # These indexes were redundant with their unique constraints (or unused
    # in the planner); Phase 1 dropped them and the model definitions must
    # not redeclare them.
    declared_indexes = (
        {idx.name for idx in Word.__table__.indexes}
        | {idx.name for idx in Translation.__table__.indexes}
        | {idx.name for idx in MissingTranslation.__table__.indexes}
    )
    assert "idx_words_language_word" not in declared_indexes
    assert "idx_words_language" not in declared_indexes
    assert "idx_missing_text_source_target" not in declared_indexes
    assert "idx_translations_source_word_id" not in declared_indexes


def test_inserting_word_without_created_at_uses_server_default(db_app):
    word = Word(language="yo", word="ile")
    db.session.add(word)
    db.session.commit()

    refreshed = Word.query.filter_by(language="yo", word="ile").one()
    assert refreshed.created_at is not None


def test_duplicate_example_is_rejected(db_app):
    yoruba = Word(language="yo", word="ile")
    english = Word(language="en", word="house")
    db.session.add_all([yoruba, english])
    db.session.flush()
    translation = Translation(
        source_word_id=yoruba.w_id, target_word_id=english.w_id
    )
    db.session.add(translation)
    db.session.flush()

    db.session.add(
        Example(
            translation_id=translation.t_id,
            example_source="ile mi",
            example_target="my house",
        )
    )
    db.session.commit()

    db.session.add(
        Example(
            translation_id=translation.t_id,
            example_source="ile mi",
            example_target="my house",
        )
    )
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()
