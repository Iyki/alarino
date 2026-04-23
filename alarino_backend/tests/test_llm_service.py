from types import SimpleNamespace

import pytest

import alarino_backend.llm_service as llm_service
from alarino_backend.llm_service import GradientLLMService, get_llm_service


@pytest.fixture(autouse=True)
def clear_llm_service_cache():
    get_llm_service.cache_clear()
    yield
    get_llm_service.cache_clear()


def test_get_llm_service_caches_client(monkeypatch):
    created = []

    class StubGradient:
        def __init__(self, **kwargs):
            created.append(kwargs)

    monkeypatch.setenv("GRADIENT_MODEL_ACCESS_KEY", "test-key")
    monkeypatch.setattr(llm_service, "Gradient", StubGradient)

    first = get_llm_service()
    second = get_llm_service()

    assert first is second
    assert len(created) == 1


def test_gradient_service_uses_configured_timeout_and_retries(monkeypatch):
    created = []

    class StubGradient:
        def __init__(self, **kwargs):
            created.append(kwargs)

    monkeypatch.setattr(llm_service, "Gradient", StubGradient)

    GradientLLMService(access_key="test-key", max_retries=5, timeout=7.5)

    assert created == [
        {
            "model_access_key": "test-key",
            "max_retries": 5,
            "timeout": 7.5,
        }
    ]


def test_prompt_uses_requested_languages(monkeypatch):
    monkeypatch.setattr(llm_service, "is_valid_yoruba_word", lambda text: True)

    service = GradientLLMService(access_key="test-key")
    service.client = SimpleNamespace()
    prompts = []

    def fake_call(prompt, text):
        prompts.append(prompt)
        return '["ọrẹ"]'

    service.call_translate_llm = fake_call

    result = service.get_translation("friend", "en", "yo")

    assert result == ["ọrẹ"]
    assert "English word to Yoruba" in prompts[0]


def test_invalid_json_retries_until_success(monkeypatch):
    monkeypatch.setattr(llm_service, "is_valid_yoruba_word", lambda text: True)

    service = GradientLLMService(access_key="test-key", max_retries=3)
    service.client = SimpleNamespace()
    responses = iter([
        "not json",
        '{"oops": true}',
        '["ọrẹ"]',
    ])

    service.call_translate_llm = lambda prompt, text: next(responses)

    result = service.get_translation("friend", "en", "yo")

    assert result == ["ọrẹ"]


def test_call_translate_llm_sends_supported_message_shape():
    captured = {}

    class StubCompletions:
        def create(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content='["ọrẹ"]'))]
            )

    service = GradientLLMService(access_key="test-key")
    service.client = SimpleNamespace(chat=SimpleNamespace(completions=StubCompletions()))

    content = service.call_translate_llm("translate this", "friend")

    assert content == '["ọrẹ"]'
    assert captured == {
        "messages": [
            {
                "role": "user",
                "content": "translate this",
            }
        ],
        "model": "openai-gpt-oss-120b",
    }
