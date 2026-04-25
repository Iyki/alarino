from types import SimpleNamespace

import pytest

import alarino_backend.app as app_module
import alarino_backend.translation_service as translation_service
from alarino_backend import db
from alarino_backend.db_models import MissingTranslation, Word
from alarino_backend.languages import Language


class QueryStub:
    """Minimal chainable query stand-in for translation service tests."""

    def __init__(self, first_result=None, all_result=None):
        self.first_result = first_result
        self.all_result = [] if all_result is None else all_result
        self.filter_by_calls = []
        self.join_calls = []
        self.filter_calls = []

    def filter_by(self, **kwargs):
        self.filter_by_calls.append(kwargs)
        return self

    def first(self):
        return self.first_result

    def join(self, *args, **kwargs):
        self.join_calls.append((args, kwargs))
        return self

    def filter(self, *args, **kwargs):
        self.filter_calls.append((args, kwargs))
        return self

    def all(self):
        return self.all_result


def test_translate_returns_400_for_empty_text():
    response, status = translation_service.translate(
        db=SimpleNamespace(),
        text="   ",
        source=Language.ENGLISH,
        target=Language.YORUBA,
        user_agent="pytest-agent",
    )

    assert status == 400
    assert response["message"] == "Text must not be empty."


def test_translate_logs_missing_word_when_source_word_does_not_exist(monkeypatch):
    word_query = QueryStub(first_result=None)
    missing_logs = []
    fake_db = SimpleNamespace()

    monkeypatch.setattr(
        translation_service,
        "Word",
        SimpleNamespace(query=word_query, language=object(), w_id=object()),
    )
    monkeypatch.setattr(
        translation_service,
        "log_missing_translation",
        lambda *args: missing_logs.append(args),
    )

    response, status = translation_service.translate(
        db=fake_db,
        text=" Hello ",
        source=Language.ENGLISH,
        target=Language.YORUBA,
        user_agent="pytest-agent",
    )

    assert status == 404
    assert response["message"] == "Word not found."
    assert word_query.filter_by_calls == [{"language": Language.ENGLISH, "text": "hello"}]
    assert missing_logs == [
        (
            fake_db,
            "hello",
            Language.ENGLISH,
            Language.YORUBA,
            "pytest-agent",
        )
    ]


def test_translate_logs_missing_when_translation_is_unavailable(db_app):
    # Word exists but no Translation row in either direction.
    db.session.add(Word(language="en", text="hello"))
    db.session.commit()

    response, status = translation_service.translate(
        db, "hello", Language.ENGLISH, Language.YORUBA, "pytest-agent"
    )

    assert status == 404
    assert response["message"] == "Word found but translation not available."

    rows = MissingTranslation.query.all()
    assert len(rows) == 1
    assert rows[0].text == "hello"
    assert rows[0].source_language == Language.ENGLISH.value
    assert rows[0].target_language == Language.YORUBA.value


def test_translate_returns_successful_translation_payload(db_app):
    from alarino_backend.data.seed_data_utils import create_translation

    hello = Word(language="en", text="hello")
    bawo = Word(language="yo", text="bawo")
    db.session.add_all([hello, bawo])
    db.session.flush()
    create_translation(hello, bawo)
    db.session.commit()

    response, status = translation_service.translate(
        db, " Hello ", Language.ENGLISH, Language.YORUBA, "pytest-agent"
    )

    assert status == 200
    assert response["success"] is True
    assert response["status"] == 200
    assert response["message"] == "Translation successful."
    assert response["data"]["translation"] == ["bawo"]
    assert response["data"]["source_word"] == "hello"
    assert response["data"]["to_language"] == Language.YORUBA.value
    # Phase 6c: senses field is additive. The seeded Translation didn't go
    # through create_translation so its sense FKs are NULL — expect a single
    # default-bucket group with empty metadata.
    assert response["data"]["senses"] == [
        {
            "label": None,
            "definition": None,
            "register": None,
            "domain": None,
            "part_of_speech": None,
            "translations": [
                {
                    "word": "bawo",
                    "note": None,
                    "provenance": None,
                    "examples": [],
                }
            ],
        }
    ]


def test_translate_llm_returns_400_for_empty_text():
    response, status = translation_service.translate_llm(
        text="   ",
        source=Language.ENGLISH,
        target=Language.YORUBA,
    )

    assert status == 400
    assert response["message"] == "Text must not be empty."


def test_translate_llm_returns_500_when_service_is_unconfigured(monkeypatch):
    monkeypatch.setattr(translation_service, "get_llm_service", lambda: None)

    response, status = translation_service.translate_llm(
        text="hello",
        source=Language.ENGLISH,
        target=Language.YORUBA,
    )

    assert status == 500
    assert response["message"] == "LLM service not configured."


def test_translate_llm_returns_successful_translation_payload(monkeypatch):
    class StubLLMService:
        def get_translation(self, text, source_lang, target_lang):
            assert text == "hello"
            assert source_lang == Language.ENGLISH.value
            assert target_lang == Language.YORUBA.value
            return ["bawo"]

    monkeypatch.setattr(translation_service, "get_llm_service", lambda: StubLLMService())

    response, status = translation_service.translate_llm(
        text=" Hello ",
        source=Language.ENGLISH,
        target=Language.YORUBA,
    )

    assert status == 200
    # translate_llm doesn't query the DB; senses field defaults to empty.
    assert response["success"] is True
    assert response["status"] == 200
    assert response["message"] == "Translation successful."
    assert response["data"]["translation"] == ["bawo"]
    assert response["data"]["source_word"] == "hello"
    assert response["data"]["to_language"] == Language.YORUBA.value
    assert response["data"]["senses"] == []


def test_translate_llm_returns_404_when_no_translation_is_found(monkeypatch):
    class StubLLMService:
        def get_translation(self, text, source_lang, target_lang):
            return []

    monkeypatch.setattr(translation_service, "get_llm_service", lambda: StubLLMService())

    response, status = translation_service.translate_llm(
        text="hello",
        source=Language.ENGLISH,
        target=Language.YORUBA,
    )

    assert status == 404
    assert response["message"] == "Translation not found."


def test_translate_llm_returns_500_when_service_raises(monkeypatch):
    class StubLLMService:
        def get_translation(self, text, source_lang, target_lang):
            raise RuntimeError("boom")

    monkeypatch.setattr(translation_service, "get_llm_service", lambda: StubLLMService())

    response, status = translation_service.translate_llm(
        text="hello",
        source=Language.ENGLISH,
        target=Language.YORUBA,
    )

    assert status == 500
    assert response["message"] == "An error occurred during translation."


def test_word_created_at_default_is_callable():
    # Regression: default was previously datetime.now() (called once at import),
    # so every Word row received the same timestamp. Must be a callable.
    default = Word.__table__.c.created_at.default
    assert default is not None
    assert callable(default.arg), (
        f"Word.created_at default must be a callable, got {default.arg!r}"
    )


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


def test_log_missing_translation_inserts_on_first_call(db_app):
    translation_service.log_missing_translation(
        db, "ile", Language.YORUBA, Language.ENGLISH, "pytest-agent"
    )

    rows = MissingTranslation.query.all()
    assert len(rows) == 1
    row = rows[0]
    assert row.text == "ile"
    assert row.source_language == Language.YORUBA.value
    assert row.target_language == Language.ENGLISH.value
    assert row.user_agent == "pytest-agent"
    assert row.hit_count == 1


def test_log_missing_translation_increments_hit_count_on_conflict(db_app):
    translation_service.log_missing_translation(
        db, "ile", Language.YORUBA, Language.ENGLISH, "first-agent"
    )
    translation_service.log_missing_translation(
        db, "ile", Language.YORUBA, Language.ENGLISH, "second-agent"
    )
    translation_service.log_missing_translation(
        db, "ile", Language.YORUBA, Language.ENGLISH, "third-agent"
    )

    rows = MissingTranslation.query.all()
    assert len(rows) == 1
    row = rows[0]
    assert row.hit_count == 3
    # First reporter's user_agent is preserved; subsequent values do not overwrite.
    assert row.user_agent == "first-agent"


def test_log_missing_translation_distinct_tuples_create_separate_rows(db_app):
    translation_service.log_missing_translation(
        db, "ile", Language.YORUBA, Language.ENGLISH, "pytest-agent"
    )
    translation_service.log_missing_translation(
        db, "house", Language.ENGLISH, Language.YORUBA, "pytest-agent"
    )
    translation_service.log_missing_translation(
        db, "ile", Language.YORUBA, Language.ENGLISH, "pytest-agent"
    )

    rows = MissingTranslation.query.order_by(MissingTranslation.text).all()
    assert len(rows) == 2
    assert {row.text: row.hit_count for row in rows} == {"house": 1, "ile": 2}


# ---- Phase 4: bidirectional lookup ----
# A Translation row is stored as a directed edge (curator added it as
# source→target). Lookups in *either* direction must succeed if either
# direction is curated.


def _seed_one_directional_pair(en_text: str, yo_text: str):
    """Seed a single curated en→yo Translation. Returns (en_word, yo_word)."""
    from alarino_backend.data.seed_data_utils import create_translation

    en = Word(language="en", text=en_text)
    yo = Word(language="yo", text=yo_text)
    db.session.add_all([en, yo])
    db.session.flush()
    create_translation(en, yo)
    db.session.commit()
    return en, yo


def test_translate_finds_curated_forward_direction(db_app):
    _seed_one_directional_pair("hello", "bawo")

    response, status = translation_service.translate(
        db, "hello", Language.ENGLISH, Language.YORUBA, "pytest-agent"
    )
    assert status == 200
    assert response["data"]["translation"] == ["bawo"]


def test_translate_finds_reverse_direction_via_bidirectional_lookup(db_app):
    # Only the en→yo direction was curated, but yo→en lookup should succeed.
    _seed_one_directional_pair("hello", "bawo")

    response, status = translation_service.translate(
        db, "bawo", Language.YORUBA, Language.ENGLISH, "pytest-agent"
    )
    assert status == 200
    assert response["data"]["translation"] == ["hello"]


def test_translate_dedupes_when_both_directions_curated(db_app):
    # Curating both directions must not return duplicate results — the bidirectional
    # lookup deduplicates by w_id of the opposite-side word.
    from alarino_backend.data.seed_data_utils import create_translation

    en, yo = _seed_one_directional_pair("hello", "bawo")
    create_translation(yo, en)
    db.session.commit()

    forward, status_f = translation_service.translate(
        db, "hello", Language.ENGLISH, Language.YORUBA, "pytest-agent"
    )
    reverse, status_r = translation_service.translate(
        db, "bawo", Language.YORUBA, Language.ENGLISH, "pytest-agent"
    )
    assert status_f == 200 and forward["data"]["translation"] == ["bawo"]
    assert status_r == 200 and reverse["data"]["translation"] == ["hello"]


def test_translate_returns_all_target_language_translations_in_either_direction(db_app):
    # Multiple Yoruba synonyms for "child", each curated en→yo. yo→en lookup of
    # any one must return ["child"]; en→yo lookup of "child" must return all
    # Yoruba synonyms.
    from alarino_backend.data.seed_data_utils import create_translation

    child = Word(language="en", text="child")
    omo = Word(language="yo", text="ọmọ")
    egbon = Word(language="yo", text="ẹgbọn")
    db.session.add_all([child, omo, egbon])
    db.session.flush()
    create_translation(child, omo)
    create_translation(child, egbon)
    db.session.commit()

    response, status = translation_service.translate(
        db, "child", Language.ENGLISH, Language.YORUBA, "pytest-agent"
    )
    assert status == 200
    assert sorted(response["data"]["translation"]) == sorted(["ọmọ", "ẹgbọn"])

    response_yo, status_yo = translation_service.translate(
        db, "ọmọ", Language.YORUBA, Language.ENGLISH, "pytest-agent"
    )
    assert status_yo == 200
    assert response_yo["data"]["translation"] == ["child"]


def test_translate_returns_404_when_no_curated_translation_in_either_direction(db_app):
    # Word exists in source language but no Translation row at all.
    db.session.add(Word(language="en", text="lonely"))
    db.session.commit()

    response, status = translation_service.translate(
        db, "lonely", Language.ENGLISH, Language.YORUBA, "pytest-agent"
    )
    assert status == 404
    assert response["message"] == "Word found but translation not available."
