from types import SimpleNamespace

import alarino_backend.translation_service as translation_service
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
        addr="203.0.113.10",
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
        addr="203.0.113.10",
        user_agent="pytest-agent",
    )

    assert status == 404
    assert response["message"] == "Word not found."
    assert word_query.filter_by_calls == [{"language": Language.ENGLISH, "word": "hello"}]
    assert missing_logs == [
        (
            fake_db,
            "hello",
            Language.ENGLISH,
            Language.YORUBA,
            "203.0.113.10",
            "pytest-agent",
        )
    ]


def test_translate_logs_missing_when_translation_is_unavailable(monkeypatch):
    source_word = SimpleNamespace(w_id=7, word="hello")
    word_query = QueryStub(first_result=source_word)
    translation_query = QueryStub(all_result=[])
    missing_logs = []
    fake_db = SimpleNamespace()

    monkeypatch.setattr(
        translation_service,
        "Word",
        SimpleNamespace(query=word_query, language=object(), w_id=object()),
    )
    monkeypatch.setattr(
        translation_service,
        "Translation",
        SimpleNamespace(query=translation_query, target_word_id=object()),
    )
    monkeypatch.setattr(
        translation_service,
        "log_missing_translation",
        lambda *args: missing_logs.append(args),
    )

    response, status = translation_service.translate(
        db=fake_db,
        text="hello",
        source=Language.ENGLISH,
        target=Language.YORUBA,
        addr="203.0.113.10",
        user_agent="pytest-agent",
    )

    assert status == 404
    assert response["message"] == "Word found but translation not available."
    assert translation_query.filter_by_calls == [{"source_word_id": 7}]
    assert missing_logs == [
        (
            fake_db,
            "hello",
            Language.ENGLISH,
            Language.YORUBA,
            "203.0.113.10",
            "pytest-agent",
        )
    ]


def test_translate_returns_successful_translation_payload(monkeypatch):
    source_word = SimpleNamespace(w_id=7, word="hello")
    translated_word = SimpleNamespace(word="bawo")
    translation = SimpleNamespace(target_word=translated_word)
    word_query = QueryStub(first_result=source_word)
    translation_query = QueryStub(all_result=[translation])

    monkeypatch.setattr(
        translation_service,
        "Word",
        SimpleNamespace(query=word_query, language=object(), w_id=object()),
    )
    monkeypatch.setattr(
        translation_service,
        "Translation",
        SimpleNamespace(query=translation_query, target_word_id=object()),
    )
    monkeypatch.setattr(
        translation_service,
        "log_missing_translation",
        lambda *args: (_ for _ in ()).throw(AssertionError("should not log missing translation")),
    )

    response, status = translation_service.translate(
        db=SimpleNamespace(),
        text=" Hello ",
        source=Language.ENGLISH,
        target=Language.YORUBA,
        addr="203.0.113.10",
        user_agent="pytest-agent",
    )

    assert status == 200
    assert response == {
        "success": True,
        "status": 200,
        "message": "Translation successful.",
        "data": {
            "translation": ["bawo"],
            "source_word": "hello",
            "to_language": Language.YORUBA.value,
        },
    }


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
    assert response == {
        "success": True,
        "status": 200,
        "message": "Translation successful.",
        "data": {
            "translation": ["bawo"],
            "source_word": "hello",
            "to_language": Language.YORUBA.value,
        },
    }


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
