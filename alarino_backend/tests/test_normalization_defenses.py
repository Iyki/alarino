"""Phase 3b — TypeDecorator + integrity-audit defenses.

These tests guard the *structural* normalization defense (the NFCWord and
NFCText TypeDecorators on canonical text columns) and the
``audit_normalization_integrity`` smoke check. They complement the per-path
property tests in ``test_normalization.py`` (which exercise every API
surface with NFC and NFD inputs); the tests here specifically prove that
the column type itself does the work, even when the call site bypasses
the explicit ``normalize_word_text`` helper."""

import unicodedata

import pytest

import alarino_backend.app as app_module
from alarino_backend import db
from alarino_backend.db_models import (
    MissingTranslation,
    NFCText,
    NFCWord,
    Proverb,
    Word,
)
from alarino_backend.normalization import (
    audit_normalization_integrity,
    normalize_text,
    normalize_word_text,
)


NFC_OMO = unicodedata.normalize("NFC", "ọmọ")
NFD_OMO = unicodedata.normalize("NFD", "ọmọ")


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


# ---- TypeDecorators are wired onto the right columns ----


def test_word_text_column_uses_nfcword():
    assert isinstance(Word.__table__.c.text.type, NFCWord)


def test_missing_translation_text_column_uses_nfcword():
    assert isinstance(MissingTranslation.__table__.c.text.type, NFCWord)


def test_proverb_text_columns_use_nfctext():
    assert isinstance(Proverb.__table__.c.yoruba_text.type, NFCText)
    assert isinstance(Proverb.__table__.c.english_text.type, NFCText)


# ---- TypeDecorators normalize on bind even when the call site does not ----


def test_nfcword_normalizes_on_bind_without_explicit_normalize_call(db_app):
    # Bypass the explicit add_word() pre-normalization. Construct Word
    # directly with NFD input. The NFCWord TypeDecorator must convert it
    # to NFC at SQL bind time.
    db.session.add(Word(language="yo", text=NFD_OMO))
    db.session.commit()

    stored = Word.query.filter_by(language="yo").one()
    assert stored.text == NFC_OMO
    # And byte-level: the stored value must match NFC bytes, not NFD bytes.
    assert stored.text.encode() == NFC_OMO.encode()
    assert stored.text.encode() != NFD_OMO.encode()


def test_nfctext_normalizes_on_bind_without_explicit_normalize_call(db_app):
    # Bypass add_proverb()'s pre-normalization. Construct Proverb directly
    # with NFD inputs. The NFCText TypeDecorator must convert.
    db.session.add(
        Proverb(yoruba_text=f"  {NFD_OMO} mi  ", english_text="  my child  ")
    )
    db.session.commit()

    p = Proverb.query.one()
    assert p.yoruba_text == f"{NFC_OMO} mi"
    assert p.english_text == "my child"


def test_nfcword_normalizes_on_query_parameters_too(db_app):
    # Storage is NFC. Query with NFD input. The NFCWord type normalizes
    # parameters at bind time, so the WHERE clause sees NFC bytes and
    # finds the row.
    db.session.add(Word(language="yo", text=NFC_OMO))
    db.session.commit()

    found = Word.query.filter_by(text=NFD_OMO).first()
    assert found is not None
    assert found.text == NFC_OMO


# ---- audit_normalization_integrity ----


def test_audit_returns_empty_dict_for_clean_db(db_app):
    db.session.add_all([
        Word(language="yo", text="ile"),
        Word(language="en", text="house"),
        Proverb(yoruba_text="ile mi", english_text="my house"),
        MissingTranslation(
            text="hello",
            source_language="en",
            target_language="yo",
            user_agent="pytest",
        ),
    ])
    db.session.commit()

    assert audit_normalization_integrity(db) == {}


def test_audit_detects_smuggled_nfd_in_words(db_app):
    # Bypass both the TypeDecorator (which normalizes on bind) and the
    # service helpers, by using a raw SQL INSERT that the DBAPI driver
    # writes verbatim. The audit must report the violation.
    db.session.add(Word(language="yo", text="dummy"))  # placeholder so table exists
    db.session.commit()

    db.session.execute(
        db.text("INSERT INTO words (language, text) VALUES (:lang, :text_val)"),
        {"lang": "yo", "text_val": NFD_OMO},
    )
    db.session.commit()

    smuggled_w_id = db.session.execute(
        db.text("SELECT w_id FROM words WHERE text = :text_val"),
        {"text_val": NFD_OMO},
    ).scalar()

    violations = audit_normalization_integrity(db)
    assert violations == {"words.text": [smuggled_w_id]}


def test_audit_detects_smuggled_nfd_in_proverb_columns(db_app):
    db.session.execute(
        db.text(
            "INSERT INTO proverbs (yoruba_text, english_text) "
            "VALUES (:y, :e)"
        ),
        {"y": NFD_OMO + " mi", "e": "  my child  "},
    )
    db.session.commit()

    p_id = db.session.execute(db.text("SELECT p_id FROM proverbs")).scalar()
    violations = audit_normalization_integrity(db)
    assert "proverbs.yoruba_text" in violations
    assert "proverbs.english_text" in violations
    assert violations["proverbs.yoruba_text"] == [p_id]
    assert violations["proverbs.english_text"] == [p_id]
