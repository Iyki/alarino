"""Tests for Phase 6a/6b — sense-layer scaffolding and write-path cutover.

Phase 6a (additive only) adds the senses table, sense FKs and metadata
columns on translations, and backfills one Sense per Word.

Phase 6b adds source_sense_id and target_sense_id columns to examples
(backfilled from the parent Translation) and updates the create_translation
write path so every new Translation has its sense FKs populated.

Phases 6c (read cutover, API change) and 6d (drop legacy) build on these."""

import pytest

import alarino_backend.app as app_module
from alarino_backend import db
from alarino_backend.data.seed_data_utils import (
    add_word,
    create_translation,
)
from alarino_backend.db_models import Example, Sense, Translation, Word
from alarino_backend.languages import Language


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


# ---- Model shape ----


def test_sense_table_columns():
    columns = {c.name for c in Sense.__table__.columns}
    assert columns == {
        "sense_id",
        "word_id",
        "part_of_speech",
        "sense_label",
        "definition",
        "register",
        "domain",
        "created_at",
    }


def test_translation_has_new_metadata_columns():
    columns = {c.name for c in Translation.__table__.columns}
    for new_col in (
        "source_sense_id",
        "target_sense_id",
        "note",
        "confidence",
        "provenance",
    ):
        assert new_col in columns, f"Translation must have new column {new_col!r}"


def test_word_part_of_speech_still_present():
    # Phase 6a keeps Word.part_of_speech for read-path compatibility.
    # Phase 6d drops it after the cutover.
    assert "part_of_speech" in {c.name for c in Word.__table__.columns}


def test_translation_sense_fk_columns_are_nullable_in_phase_6a():
    # Phase 6a leaves source_sense_id and target_sense_id nullable so the
    # backfill can run incrementally and so existing write paths that
    # don't yet set them keep working. Phase 6d makes them NOT NULL.
    assert Translation.__table__.c.source_sense_id.nullable is True
    assert Translation.__table__.c.target_sense_id.nullable is True


# ---- Sense behavior under db.create_all (model-only, no migration backfill) ----


def test_sense_can_be_created_for_a_word(db_app):
    word = Word(language="yo", word="ile")
    db.session.add(word)
    db.session.flush()
    sense = Sense(
        word_id=word.w_id,
        part_of_speech="n",
        sense_label="building",
        definition="a structure for shelter",
        register="formal",
        domain=None,
    )
    db.session.add(sense)
    db.session.commit()

    refreshed = Sense.query.one()
    assert refreshed.word_id == word.w_id
    assert refreshed.sense_label == "building"
    assert refreshed.created_at is not None


def test_word_to_senses_relationship(db_app):
    # Word.senses backref returns a list, supporting polysemy from Phase 6b on.
    word = Word(language="en", word="bank")
    db.session.add(word)
    db.session.flush()
    db.session.add_all([
        Sense(word_id=word.w_id, sense_label="financial"),
        Sense(word_id=word.w_id, sense_label="river"),
    ])
    db.session.commit()

    refreshed = Word.query.filter_by(word="bank").one()
    assert {s.sense_label for s in refreshed.senses} == {"financial", "river"}


def test_translation_can_carry_metadata(db_app):
    en = Word(language="en", word="hello")
    yo = Word(language="yo", word="bawo")
    db.session.add_all([en, yo])
    db.session.flush()
    en_sense = Sense(word_id=en.w_id, sense_label="greeting")
    yo_sense = Sense(word_id=yo.w_id, sense_label="greeting")
    db.session.add_all([en_sense, yo_sense])
    db.session.flush()

    db.session.add(
        Translation(
            source_word_id=en.w_id,
            target_word_id=yo.w_id,
            source_sense_id=en_sense.sense_id,
            target_sense_id=yo_sense.sense_id,
            note="informal greeting; common in casual contexts",
            confidence=0.95,
            provenance="curated",
        )
    )
    db.session.commit()

    t = Translation.query.one()
    assert t.source_sense_id == en_sense.sense_id
    assert t.target_sense_id == yo_sense.sense_id
    assert t.note.startswith("informal greeting")
    assert t.confidence == 0.95
    assert t.provenance == "curated"


# ---- Phase 6b: write-path cutover + Example sense columns ----


def test_example_has_sense_fk_columns():
    columns = {c.name for c in Example.__table__.columns}
    assert "source_sense_id" in columns
    assert "target_sense_id" in columns


def test_example_translation_id_still_present_in_phase_6b():
    # Phase 6b keeps translation_id on Example so the legacy relationship
    # and read paths keep working through 6c. Phase 6d drops it.
    assert "translation_id" in {c.name for c in Example.__table__.columns}


def test_example_sense_columns_nullable_in_phase_6b():
    # 6b adds the columns nullable so the backfill can run incrementally.
    # 6d tightens to NOT NULL.
    assert Example.__table__.c.source_sense_id.nullable is True
    assert Example.__table__.c.target_sense_id.nullable is True


def test_create_translation_populates_sense_fks(db_app):
    en = add_word(language=Language.ENGLISH, word_text="hello")
    yo = add_word(language=Language.YORUBA, word_text="bawo")
    db.session.flush()

    create_translation(en, yo)
    db.session.commit()

    t = Translation.query.one()
    assert t.source_sense_id is not None
    assert t.target_sense_id is not None
    # The sense FKs point at senses owned by the source/target words.
    assert t.source_sense.word_id == en.w_id
    assert t.target_sense.word_id == yo.w_id


# ---- Phase 6c: sense-grouped response on /api/translate ----


def test_translate_response_includes_senses_field_with_default_metadata(db_app):
    import alarino_backend.translation_service as translation_service

    en = add_word(language=Language.ENGLISH, word_text="hello")
    yo = add_word(language=Language.YORUBA, word_text="bawo")
    db.session.flush()
    create_translation(en, yo)
    db.session.commit()

    response, status = translation_service.translate(
        db, "hello", Language.ENGLISH, Language.YORUBA, "pytest-agent"
    )
    assert status == 200
    senses = response["data"]["senses"]
    assert len(senses) == 1
    group = senses[0]
    # Default sense from create_translation has no curated metadata.
    assert group["label"] is None
    assert group["definition"] is None
    assert group["register"] is None
    assert group["domain"] is None
    assert group["translations"] == [
        {"word": "bawo", "note": None, "provenance": None, "examples": []}
    ]


def test_translate_response_groups_polysemous_word_into_multiple_senses(db_app):
    """The product story for the sense layer: a polysemous word like "bank"
    surfaces multiple sense groups, each with its own translations."""
    import alarino_backend.translation_service as translation_service
    from alarino_backend.db_models import Sense, Translation

    bank = add_word(language=Language.ENGLISH, word_text="bank")
    ile_ifo = add_word(language=Language.YORUBA, word_text="ifowopamo")  # financial
    bebe = add_word(language=Language.YORUBA, word_text="bebe")  # river
    db.session.flush()

    financial = Sense(
        word_id=bank.w_id,
        sense_label="financial",
        definition="A financial institution",
        part_of_speech="n",
    )
    river = Sense(
        word_id=bank.w_id,
        sense_label="river",
        definition="Land alongside a river",
        part_of_speech="n",
    )
    ife_sense = Sense(word_id=ile_ifo.w_id, sense_label="financial", part_of_speech="n")
    bebe_sense = Sense(word_id=bebe.w_id, sense_label="river", part_of_speech="n")
    db.session.add_all([financial, river, ife_sense, bebe_sense])
    db.session.flush()

    db.session.add_all([
        Translation(
            source_word_id=bank.w_id,
            target_word_id=ile_ifo.w_id,
            source_sense_id=financial.sense_id,
            target_sense_id=ife_sense.sense_id,
            note="financial sense",
            provenance="curated",
        ),
        Translation(
            source_word_id=bank.w_id,
            target_word_id=bebe.w_id,
            source_sense_id=river.sense_id,
            target_sense_id=bebe_sense.sense_id,
            note="river sense",
            provenance="curated",
        ),
    ])
    db.session.commit()

    response, status = translation_service.translate(
        db, "bank", Language.ENGLISH, Language.YORUBA, "pytest-agent"
    )
    assert status == 200
    # Flat list still surfaces both translations (backward compat).
    assert sorted(response["data"]["translation"]) == sorted(["ifowopamo", "bebe"])
    # The new senses field separates them.
    senses = response["data"]["senses"]
    assert len(senses) == 2
    by_label = {s["label"]: s for s in senses}
    assert "financial" in by_label and "river" in by_label
    assert by_label["financial"]["definition"] == "A financial institution"
    assert by_label["financial"]["translations"][0]["word"] == "ifowopamo"
    assert by_label["financial"]["translations"][0]["note"] == "financial sense"
    assert by_label["river"]["translations"][0]["word"] == "bebe"
    assert by_label["river"]["translations"][0]["note"] == "river sense"


def test_translate_response_carries_examples_attached_to_sense_pair(db_app):
    import alarino_backend.translation_service as translation_service
    from alarino_backend.db_models import Example, Translation

    en = add_word(language=Language.ENGLISH, word_text="hello")
    yo = add_word(language=Language.YORUBA, word_text="bawo")
    db.session.flush()
    create_translation(en, yo)
    db.session.commit()
    t = Translation.query.one()
    db.session.add(
        Example(
            translation_id=t.t_id,
            source_sense_id=t.source_sense_id,
            target_sense_id=t.target_sense_id,
            example_source="Hello there",
            example_target="Bawo nibe",
        )
    )
    db.session.commit()

    response, status = translation_service.translate(
        db, "hello", Language.ENGLISH, Language.YORUBA, "pytest-agent"
    )
    assert status == 200
    examples = response["data"]["senses"][0]["translations"][0]["examples"]
    assert examples == [{"source": "Hello there", "target": "Bawo nibe"}]


def test_create_translation_reuses_existing_default_sense(db_app):
    en = add_word(language=Language.ENGLISH, word_text="hello")
    yo = add_word(language=Language.YORUBA, word_text="bawo")
    db.session.flush()
    # Pre-create a sense for the English word; create_translation must reuse it
    # rather than creating a duplicate "default" sense.
    pre_existing_en_sense = Sense(word_id=en.w_id, sense_label="greeting")
    db.session.add(pre_existing_en_sense)
    db.session.flush()

    create_translation(en, yo)
    db.session.commit()

    t = Translation.query.one()
    assert t.source_sense_id == pre_existing_en_sense.sense_id
    # English word should have just the one sense, not a duplicate.
    assert Sense.query.filter_by(word_id=en.w_id).count() == 1


def test_sense_word_id_fk_uses_db_level_cascade(db_app):
    # The model declares ondelete='CASCADE' on senses.word_id. Verify the
    # constraint is wired at the DB level via a raw SQL DELETE (bypassing
    # SQLAlchemy's ORM cascade, which has its own pre-delete NULL-out
    # behavior that would interfere). On SQLite, foreign keys must be
    # enabled per-connection.
    word = Word(language="yo", word="ile")
    db.session.add(word)
    db.session.flush()
    db.session.add(Sense(word_id=word.w_id, sense_label="building"))
    db.session.commit()
    assert Sense.query.count() == 1

    db.session.execute(db.text("PRAGMA foreign_keys = ON"))
    db.session.execute(
        db.text("DELETE FROM words WHERE w_id = :id"), {"id": word.w_id}
    )
    db.session.commit()
    assert Sense.query.count() == 0
