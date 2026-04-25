"""Integration tests for translation_service.bulk_upload_words.

Previously the bulk-upload path was only exercised end-to-end via Docker
against real Postgres. These tests cover the unit/integration boundary so
regressions in input parsing, validation, and persistence are caught
under pytest."""

import pytest

import alarino_backend.app as app_module
import alarino_backend.translation_service as translation_service
from alarino_backend import db
from alarino_backend.db_models import Sense, Translation, Word


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


# ---- Dry-run path: validation only, nothing persisted ----


def test_dry_run_reports_successful_pairs_without_persisting(db_app):
    response, status = translation_service.bulk_upload_words(
        db, "hello,bawo\nhouse,ile", dry_run=True
    )
    assert status == 200
    assert response["message"] == "Bulk upload validation completed"
    assert response["data"]["dry_run"] is True
    assert response["data"]["successful_pairs"] == [
        {"english": "hello", "yoruba": "bawo"},
        {"english": "house", "yoruba": "ile"},
    ]
    assert response["data"]["failed_pairs"] == []
    # Nothing committed.
    assert Word.query.count() == 0
    assert Translation.query.count() == 0


def test_dry_run_reports_invalid_pairs_without_persisting(db_app):
    response, status = translation_service.bulk_upload_words(
        db,
        "hello,bawo\nbad@@@english,bawo\nhouse,bad@@@yoruba",
        dry_run=True,
    )
    assert status == 200
    assert response["data"]["successful_pairs"] == [
        {"english": "hello", "yoruba": "bawo"},
    ]
    failed = response["data"]["failed_pairs"]
    assert len(failed) == 2
    assert any("Invalid English word" in f["reason"] for f in failed)
    assert any("Invalid Yoruba word" in f["reason"] for f in failed)
    assert Word.query.count() == 0


# ---- Live run path: validation + persistence ----


def test_live_run_persists_words_and_translations(db_app):
    response, status = translation_service.bulk_upload_words(
        db, "hello,bawo\nhouse,ile", dry_run=False
    )
    assert status == 200
    assert response["message"] == "Bulk upload process completed."
    assert response["data"]["dry_run"] is False
    assert len(response["data"]["successful_pairs"]) == 2

    assert Word.query.filter_by(language="en", text="hello").one()
    assert Word.query.filter_by(language="en", text="house").one()
    assert Word.query.filter_by(language="yo", text="bawo").one()
    assert Word.query.filter_by(language="yo", text="ile").one()

    translations = Translation.query.all()
    assert len(translations) == 2
    # Each Translation has its sense FKs populated by the create_translation
    # path (Phase 6b cutover).
    for t in translations:
        assert t.source_sense_id is not None
        assert t.target_sense_id is not None


def test_live_run_creates_one_default_sense_per_word(db_app):
    translation_service.bulk_upload_words(
        db, "hello,bawo", dry_run=False
    )
    assert Sense.query.count() == 2  # one per word
    for word in Word.query.all():
        assert (
            Sense.query.filter_by(word_id=word.w_id).count() == 1
        ), "create_translation should attach exactly one default sense per word"


def test_live_run_skips_invalid_pairs_but_commits_valid_ones(db_app):
    response, status = translation_service.bulk_upload_words(
        db,
        "hello,bawo\nbad@@@english,bawo\nhouse,ile",
        dry_run=False,
    )
    assert status == 200
    assert len(response["data"]["successful_pairs"]) == 2
    assert len(response["data"]["failed_pairs"]) == 1
    # Valid ones persisted.
    assert Word.query.count() == 4  # hello, house, bawo, ile
    assert Translation.query.count() == 2


def test_live_run_is_idempotent_on_repeated_input(db_app):
    translation_service.bulk_upload_words(
        db, "hello,bawo", dry_run=False
    )
    # Re-run: words and the translation already exist; no duplicates.
    response, status = translation_service.bulk_upload_words(
        db, "hello,bawo", dry_run=False
    )
    assert status == 200
    assert Word.query.count() == 2
    assert Translation.query.count() == 1


# ---- Input shape edge cases ----


def test_skips_empty_rows(db_app):
    response, status = translation_service.bulk_upload_words(
        db, "\nhello,bawo\n\nhouse,ile\n", dry_run=False
    )
    assert status == 200
    assert len(response["data"]["successful_pairs"]) == 2
    assert response["data"]["failed_pairs"] == []


def test_rejects_rows_with_wrong_column_count(db_app):
    response, status = translation_service.bulk_upload_words(
        db, "hello,bawo\nonly_one_column\nhello,bawo,extra", dry_run=False
    )
    assert status == 200
    assert len(response["data"]["successful_pairs"]) == 1
    failed = response["data"]["failed_pairs"]
    assert len(failed) == 2
    assert all(
        "exactly two values" in f["reason"] for f in failed
    )


def test_strips_and_lowercases_input(db_app):
    response, status = translation_service.bulk_upload_words(
        db, "  HELLO  ,  BAWO  ", dry_run=False
    )
    assert status == 200
    # Stored canonical form is lowercased + stripped.
    assert Word.query.filter_by(language="en", text="hello").one()
    assert Word.query.filter_by(language="yo", text="bawo").one()


def test_empty_input_returns_empty_response(db_app):
    response, status = translation_service.bulk_upload_words(
        db, "", dry_run=False
    )
    assert status == 200
    assert response["data"]["successful_pairs"] == []
    assert response["data"]["failed_pairs"] == []
    assert Word.query.count() == 0
