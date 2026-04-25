"""Tests for the proverb-words connection introduced by Phase 3 of the schema
evolution plan."""

import pytest

import alarino_backend.app as app_module
import alarino_backend.translation_service as translation_service
from alarino_backend import db
from alarino_backend.data.seed_data_utils import add_proverb
from alarino_backend.db_models import Proverb, ProverbWord, Word
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


def test_add_proverb_populates_proverb_words(db_app):
    add_proverb("ile mi", "my house")

    proverb = Proverb.query.one()
    links = ProverbWord.query.filter_by(proverb_id=proverb.p_id).all()
    yoruba_links = [link for link in links if link.language == "yo"]
    english_links = [link for link in links if link.language == "en"]

    yoruba_words = {link.word.text for link in yoruba_links}
    english_words = {link.word.text for link in english_links}
    assert yoruba_words == {"ile", "mi"}
    assert english_words == {"my", "house"}


def test_get_proverbs_containing_returns_matching_proverb(db_app):
    add_proverb("ile mi", "my house")
    add_proverb("omi tutu", "cool water")

    matching = translation_service.get_proverbs_containing(
        db, Language.YORUBA, "ile"
    )
    assert {p.yoruba_text for p in matching} == {"ile mi"}

    matching_en = translation_service.get_proverbs_containing(
        db, Language.ENGLISH, "house"
    )
    assert {p.english_text for p in matching_en} == {"my house"}


def test_get_proverbs_containing_returns_empty_for_unknown_word(db_app):
    add_proverb("ile mi", "my house")

    assert translation_service.get_proverbs_containing(
        db, Language.YORUBA, "missing"
    ) == []
    assert translation_service.get_proverbs_containing(
        db, Language.YORUBA, ""
    ) == []


def test_get_proverbs_containing_normalizes_decomposed_input(db_app):
    # Yoruba "ọmọ" stored canonically (NFC). Querying with the same string in
    # NFD form (the ọ becomes 'o' + COMBINING DOT BELOW) must match.
    add_proverb("ọmọ mi", "my child")

    import unicodedata

    decomposed_query = unicodedata.normalize("NFD", "ọmọ")
    assert decomposed_query != "ọmọ"  # sanity: forms really differ

    matching = translation_service.get_proverbs_containing(
        db, Language.YORUBA, decomposed_query
    )
    assert {p.yoruba_text for p in matching} == {"ọmọ mi"}


def test_repeated_word_in_proverb_gets_distinct_position(db_app):
    add_proverb("ile ile mi", "house house mine")

    proverb = Proverb.query.one()
    yoruba_ile = (
        ProverbWord.query
        .join(Word, Word.w_id == ProverbWord.word_id)
        .filter(
            ProverbWord.proverb_id == proverb.p_id,
            ProverbWord.language == "yo",
            Word.text == "ile",
        )
        .all()
    )
    positions = sorted(link.position for link in yoruba_ile)
    assert positions == [0, 1]
