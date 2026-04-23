import importlib

import pytest

import alarino_backend.app as app_module
from alarino_backend import _daily_word_cache, db
from alarino_backend.languages import Language


@pytest.fixture
def app():
    app = app_module.create_app()
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    with app.test_client() as client:
        yield client


def test_app_module_import_succeeds():
    imported = importlib.import_module("alarino_backend.app")

    assert imported is app_module


def test_create_app_returns_flask_app(app):
    assert app.name == "alarino_backend.app"


def test_expected_routes_are_registered(app):
    rules = {rule.rule for rule in app.url_map.iter_rules()}

    assert {
        "/api/translate",
        "/api/translate/llm",
        "/api/daily-word",
        "/api/proverb",
        "/api/admin/bulk-upload",
        "/api/health",
    }.issubset(rules)


def test_sqlalchemy_is_initialized_on_app(app):
    assert "sqlalchemy" in app.extensions

    with app.app_context():
        assert db.session is not None


def test_translate_rejects_missing_body(client):
    response = client.post("/api/translate")

    assert response.status_code == 400
    assert response.get_json()["message"] == "Invalid request body."


def test_translate_rejects_missing_fields(client):
    response = client.post("/api/translate", json={"text": "hello"})

    assert response.status_code == 400
    assert response.get_json()["message"] == "Invalid request body."


def test_translate_rejects_unsupported_language(client):
    response = client.post(
        "/api/translate",
        json={"text": "hello", "source_lang": "xx", "target_lang": Language.YORUBA.value},
    )

    assert response.status_code == 400
    assert response.get_json()["message"] == "Unsupported language."


def test_translate_returns_service_response(client, monkeypatch):
    captured = {}
    payload = {
        "success": True,
        "status": 200,
        "message": "Translation successful.",
        "data": {
            "translation": ["bawo"],
            "source_word": "hello",
            "to_language": Language.YORUBA.value,
        },
    }

    def fake_translate(db_arg, text, source_language, target_language, addr, user_agent):
        captured.update(
            db_arg=db_arg,
            text=text,
            source_language=source_language,
            target_language=target_language,
            addr=addr,
            user_agent=user_agent,
        )
        return payload, 200

    monkeypatch.setattr(app_module, "translate", fake_translate)

    response = client.post(
        "/api/translate",
        json={
            "text": "hello",
            "source_lang": Language.ENGLISH.value,
            "target_lang": Language.YORUBA.value,
        },
        headers={"User-Agent": "pytest-agent"},
        environ_overrides={"REMOTE_ADDR": "203.0.113.10"},
    )

    assert response.status_code == 200
    assert response.get_json() == payload
    assert captured == {
        "db_arg": db,
        "text": "hello",
        "source_language": Language.ENGLISH,
        "target_language": Language.YORUBA,
        "addr": "203.0.113.10",
        "user_agent": "pytest-agent",
    }


def test_translate_llm_rejects_missing_fields(client):
    response = client.post("/api/translate/llm", json={"text": "hello"})

    assert response.status_code == 400
    assert response.get_json()["message"] == "Invalid request body."


def test_translate_llm_rejects_unsupported_language(client):
    response = client.post(
        "/api/translate/llm",
        json={"text": "hello", "source_lang": "xx", "target_lang": Language.YORUBA.value},
    )

    assert response.status_code == 400
    assert response.get_json()["message"] == "Unsupported language."


def test_translate_llm_returns_service_response(client, monkeypatch):
    payload = {
        "success": True,
        "status": 200,
        "message": "Translation successful.",
        "data": {
            "translation": ["bawo"],
            "source_word": "hello",
            "to_language": Language.YORUBA.value,
        },
    }

    monkeypatch.setattr(app_module, "translate_llm", lambda text, source, target: (payload, 200))

    response = client.post(
        "/api/translate/llm",
        json={
            "text": "hello",
            "source_lang": Language.ENGLISH.value,
            "target_lang": Language.YORUBA.value,
        },
    )

    assert response.status_code == 200
    assert response.get_json() == payload


def test_daily_word_returns_service_response(client, monkeypatch):
    payload = {
        "success": True,
        "status": 200,
        "message": "Word of the day fetched from cache.",
        "data": {"yoruba_word": "ore", "english_word": "friend"},
    }
    captured = {}

    def fake_get_word_of_the_day(db_arg, cache_arg):
        captured["db_arg"] = db_arg
        captured["cache_arg"] = cache_arg
        return payload, 200

    monkeypatch.setattr(app_module, "get_word_of_the_day", fake_get_word_of_the_day)

    response = client.get("/api/daily-word")

    assert response.status_code == 200
    assert response.get_json() == payload
    assert captured == {"db_arg": db, "cache_arg": _daily_word_cache}


def test_proverb_returns_service_response(client, monkeypatch):
    payload = {
        "success": True,
        "status": 200,
        "message": "Proverb fetched successfully.",
        "data": {"yoruba_text": "Ile la n wo", "english_text": "We look homeward"},
    }
    captured = {}

    def fake_get_random_proverb(db_arg):
        captured["db_arg"] = db_arg
        return payload, 200

    monkeypatch.setattr(app_module, "get_random_proverb", fake_get_random_proverb)

    response = client.get("/api/proverb")

    assert response.status_code == 200
    assert response.get_json() == payload
    assert captured == {"db_arg": db}


def test_admin_bulk_upload_requires_authorization_header(client, monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "test-key")

    response = client.post("/api/admin/bulk-upload", json={})

    assert response.status_code == 401
    assert "Authorization header is missing or invalid" in response.get_json()["message"]


def test_admin_bulk_upload_rejects_invalid_key(client, monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "test-key")

    response = client.post(
        "/api/admin/bulk-upload",
        headers={"Authorization": "Bearer wrong-key"},
        json={},
    )

    assert response.status_code == 401
    assert "Invalid API key" in response.get_json()["message"]


def test_admin_bulk_upload_rejects_missing_json_payload(client, monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "test-key")

    response = client.post(
        "/api/admin/bulk-upload",
        headers={"Authorization": "Bearer test-key"},
    )

    assert response.status_code == 415


def test_admin_bulk_upload_requires_text_input(client, monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "test-key")

    response = client.post(
        "/api/admin/bulk-upload",
        headers={"Authorization": "Bearer test-key"},
        json={"dry_run": True},
    )

    assert response.status_code == 400
    assert "Invalid request body, 'text_input' is required" in response.get_json()["message"]


def test_admin_bulk_upload_returns_service_response(client, monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "test-key")
    payload = {
        "success": True,
        "status": 200,
        "message": "Bulk upload validation completed",
        "data": {
            "successful_pairs": [{"english": "apple", "yoruba": "apulo"}],
            "failed_pairs": [],
            "dry_run": True,
        },
    }
    captured = {}

    def fake_bulk_upload_words(db_arg, text_input, dry_run):
        captured.update(db_arg=db_arg, text_input=text_input, dry_run=dry_run)
        return payload, 200

    monkeypatch.setattr(app_module, "bulk_upload_words", fake_bulk_upload_words)

    response = client.post(
        "/api/admin/bulk-upload",
        headers={"Authorization": "Bearer test-key"},
        json={"text_input": "apple,apulo", "dry_run": True},
    )

    assert response.status_code == 200
    assert response.get_json() == payload
    assert captured == {
        "db_arg": db,
        "text_input": "apple,apulo",
        "dry_run": True,
    }


def test_health_endpoint_contract(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.get_json() == {
        "success": True,
        "status": 200,
        "message": "ok",
        "data": None,
    }
