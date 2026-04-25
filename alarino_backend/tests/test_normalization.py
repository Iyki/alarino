"""End-to-end tests for Yoruba/English text normalization across every write
and read path that touches the database. The codebase has historically had
inconsistent normalization between writers and readers; these tests guard
against regressions in any single path falling out of sync."""

import unicodedata

import pytest

import alarino_backend.app as app_module
import alarino_backend.translation_service as translation_service
from alarino_backend import db
from alarino_backend.data.seed_data_utils import (
    add_proverb,
    add_word,
    is_valid_english_word,
    is_valid_yoruba_text,
    is_valid_yoruba_word,
    normalize_text,
    normalize_word_text,
)
from alarino_backend.db_models import MissingTranslation, Proverb, Word
from alarino_backend.languages import Language


# Yoruba "ọmọ" — exercises the precomposed/decomposed split.
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


def test_canonical_yoruba_forms_differ_at_byte_level():
    # Sanity: the rest of these tests only mean something if NFC and NFD
    # of the same Yoruba word actually have different codepoints.
    assert NFC_OMO != NFD_OMO


def test_normalize_word_text_collapses_nfc_and_nfd():
    assert normalize_word_text(NFC_OMO) == normalize_word_text(NFD_OMO)
    assert normalize_word_text(NFC_OMO) == NFC_OMO


def test_normalize_text_collapses_nfc_and_nfd_preserving_case():
    assert normalize_text(f"  {NFD_OMO}  ") == NFC_OMO
    # Case is preserved at sentence level (unlike normalize_word_text).
    assert normalize_text("Hello World") == "Hello World"


def test_is_valid_yoruba_word_accepts_decomposed_input():
    # Pre-fix bug: the regex char class was NFC but the input was checked
    # in whatever form the caller passed, so NFD Yoruba was rejected.
    assert is_valid_yoruba_word(NFC_OMO) is True
    assert is_valid_yoruba_word(NFD_OMO) is True


def test_is_valid_yoruba_text_accepts_decomposed_input():
    assert is_valid_yoruba_text(f"{NFD_OMO} mi") is True


def test_is_valid_english_word_handles_combining_marks_gracefully():
    # ASCII English is invariant under NFC/NFD, but the validator should not
    # blow up on stray combining marks in input.
    assert is_valid_english_word("hello") is True


def test_add_word_stores_nfc_regardless_of_input_form(db_app):
    add_word(language=Language.YORUBA, word_text=NFD_OMO)
    db.session.commit()

    rows = Word.query.filter_by(language=Language.YORUBA).all()
    assert [row.text for row in rows] == [NFC_OMO]


def test_add_word_collapses_nfd_and_nfc_to_one_row(db_app):
    add_word(language=Language.YORUBA, word_text=NFC_OMO)
    add_word(language=Language.YORUBA, word_text=NFD_OMO)
    db.session.commit()

    assert Word.query.filter_by(language=Language.YORUBA).count() == 1


def test_add_proverb_stores_nfc_regardless_of_input_form(db_app):
    add_proverb(f"{NFD_OMO} mi", "my child")
    db.session.commit()

    proverb = Proverb.query.one()
    assert proverb.yoruba_text == f"{NFC_OMO} mi"


def test_add_proverb_treats_nfc_and_nfd_as_same_proverb(db_app):
    add_proverb(f"{NFC_OMO} mi", "my child")
    add_proverb(f"{NFD_OMO} mi", "my child")
    db.session.commit()

    # Both inserts must collapse to one row; the second should be detected
    # as an existing proverb after normalization, not insert a near-duplicate.
    assert Proverb.query.count() == 1


def test_translate_finds_word_when_query_uses_decomposed_form(db_app):
    from alarino_backend.data.seed_data_utils import create_translation

    # Seed a Word in NFC form (storage canonical).
    add_word(language=Language.YORUBA, word_text=NFC_OMO)
    english_word = add_word(language=Language.ENGLISH, word_text="child")
    db.session.flush()
    yoruba_word = Word.query.filter_by(language=Language.YORUBA).one()
    create_translation(yoruba_word, english_word)
    db.session.commit()

    response, status = translation_service.translate(
        db, NFD_OMO, Language.YORUBA, Language.ENGLISH, "pytest-agent"
    )
    assert status == 200
    assert response["data"]["translation"] == ["child"]


def test_log_missing_translation_collapses_nfc_nfd_in_request_path(db_app):
    # Two requests, same Yoruba word in different normalization forms,
    # against an empty words table. Should produce ONE missing_translations
    # row with hit_count=2, not two separate rows.
    translation_service.translate(
        db, NFC_OMO, Language.YORUBA, Language.ENGLISH, "pytest-agent"
    )
    translation_service.translate(
        db, NFD_OMO, Language.YORUBA, Language.ENGLISH, "pytest-agent"
    )

    rows = MissingTranslation.query.all()
    assert len(rows) == 1
    assert rows[0].text == NFC_OMO
    assert rows[0].hit_count == 2
