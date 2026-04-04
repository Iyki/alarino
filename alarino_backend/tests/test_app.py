import os
import importlib

import main.translation_service as translation_service
import pytest
from main import app as flask_app
from main.languages import Language

importlib.import_module("main.app")


# todo: make tests independent of database access


@pytest.fixture
def client():
    """
    Creates a test client for our Flask app.
    """
    flask_app.config['TESTING'] = True
    print("rules:")
    print([str(rule) for rule in flask_app.url_map.iter_rules()])
    print("rules?")
    with flask_app.test_client() as client:
        yield client


def test_translate_no_data(client):
    """
    Test the /api/translate endpoint with no JSON data.
    We expect a 400 status code and an error message.
    """
    response = client.post('/api/translate')
    assert response.status_code == 400
    assert response.is_json
    data = response.get_json()
    assert data.get("message") == "Invalid request body."


def test_translate_missing_fields(client):
    """
    Test the /api/translate endpoint with missing fields in JSON data.
    We expect a 400 status code and an error message.
    """
    payload = {"text": "Hello"}
    response = client.post('/api/translate', json=payload)

    assert response.status_code == 400
    assert response.is_json
    data = response.get_json()
    assert data.get("message") == "Invalid request body."


def test_translate_success(client):
    """
    Test the /api/translate endpoint with valid data.
    We expect a 200 status code and a valid translation result.
    """
    payload = {
        "text": "Hello",
        "source_lang": Language.ENGLISH.value,
        "target_lang": Language.YORUBA.value
    }
    response = client.post('/api/translate', json=payload)

    assert response.status_code == 200
    assert response.is_json
    data = response.get_json()
    assert "translation" in data.get("data")


def test_translate_custom_text(client):
    """
    Another test for variety:
    Provide a different text and confirm the response includes that text in the translation.
    """
    payload = {
        "text": "This is a test",
        "source_lang": Language.ENGLISH.value,
        "target_lang": Language.YORUBA.value
    }
    response = client.post('/api/translate', json=payload)
    assert response.status_code == 404


def test_translate_llm_missing_fields(client):
    payload = {"text": "Hello"}
    response = client.post('/api/translate/llm', json=payload)

    assert response.status_code == 400
    assert response.is_json
    data = response.get_json()
    assert data.get("message") == "Invalid request body."


def test_translate_llm_unsupported_language(client):
    payload = {
        "text": "Hello",
        "source_lang": "xx",
        "target_lang": Language.YORUBA.value
    }
    response = client.post('/api/translate/llm', json=payload)

    assert response.status_code == 400
    assert response.is_json
    data = response.get_json()
    assert data.get("message") == "Unsupported language."


def test_translate_llm_not_configured(client, monkeypatch):
    monkeypatch.setattr(translation_service, "get_llm_service", lambda: None)

    payload = {
        "text": "hello",
        "source_lang": Language.ENGLISH.value,
        "target_lang": Language.YORUBA.value
    }
    response = client.post('/api/translate/llm', json=payload)

    assert response.status_code == 500
    assert response.is_json
    data = response.get_json()
    assert data.get("message") == "LLM service not configured."


def test_translate_llm_success(client, monkeypatch):
    class StubLLMService:
        def get_translation(self, text, source_lang, target_lang):
            assert text == "hello"
            assert source_lang == Language.ENGLISH.value
            assert target_lang == Language.YORUBA.value
            return ["bawo"]

    monkeypatch.setattr(translation_service, "get_llm_service", lambda: StubLLMService())

    payload = {
        "text": "hello",
        "source_lang": Language.ENGLISH.value,
        "target_lang": Language.YORUBA.value
    }
    response = client.post('/api/translate/llm', json=payload)

    assert response.status_code == 200
    assert response.is_json
    data = response.get_json().get("data")
    assert data["source_word"] == "hello"
    assert data["translation"] == ["bawo"]
    assert data["to_language"] == Language.YORUBA.value


def test_translate_llm_not_found(client, monkeypatch):
    class StubLLMService:
        def get_translation(self, text, source_lang, target_lang):
            return []

    monkeypatch.setattr(translation_service, "get_llm_service", lambda: StubLLMService())

    payload = {
        "text": "hello",
        "source_lang": Language.ENGLISH.value,
        "target_lang": Language.YORUBA.value
    }
    response = client.post('/api/translate/llm', json=payload)

    assert response.status_code == 404
    assert response.is_json
    data = response.get_json()
    assert data.get("message") == "Translation not found."


def test_admin_bulk_upload_unauthorized(client):
    """Test bulk upload endpoint without API key."""
    os.environ['ADMIN_API_KEY'] = 'test-key'
    response = client.post('/api/admin/bulk-upload', json={})
    assert response.status_code == 401
    data = response.get_json()
    assert "Authorization header is missing or invalid" in data.get("message")


def test_admin_bulk_upload_invalid_key(client):
    """Test bulk upload endpoint with an invalid API key."""
    os.environ['ADMIN_API_KEY'] = 'test-key'
    headers = {'Authorization': 'Bearer invalid-key'}
    response = client.post('/api/admin/bulk-upload', headers=headers, json={})
    assert response.status_code == 401
    data = response.get_json()
    assert "Invalid API key" in data.get("message")


def test_admin_bulk_upload_no_payload(client):
    """Test bulk upload endpoint with no JSON payload."""
    os.environ['ADMIN_API_KEY'] = 'test-key'
    headers = {'Authorization': 'Bearer test-key'}
    response = client.post('/api/admin/bulk-upload', headers=headers)
    print(response)
    assert response.status_code == 415


def test_admin_bulk_upload_missing_text_input(client):
    """Test bulk upload endpoint with missing 'text_input' in payload."""
    os.environ['ADMIN_API_KEY'] = 'test-key'
    headers = {'Authorization': 'Bearer test-key'}
    payload = {"dry_run": True}
    response = client.post('/api/admin/bulk-upload', headers=headers, json=payload)
    assert response.status_code == 400
    data = response.get_json()
    assert "Invalid request body, 'text_input' is required" in data.get("message")


def test_admin_bulk_upload_dry_run_success(client):
    """Test a successful dry run bulk upload."""
    os.environ['ADMIN_API_KEY'] = 'test-key'
    headers = {'Authorization': 'Bearer test-key'}
    payload = {
        "text_input": "apple,àpùlò\nbanana,ọ̀gẹ̀dẹ̀",
        "dry_run": True
    }
    response = client.post('/api/admin/bulk-upload', headers=headers, json=payload)
    assert response.status_code == 200
    data = response.get_json().get('data')
    assert data['dry_run'] is True
    assert len(data['successful_pairs']) == 2
    assert len(data['failed_pairs']) == 0


# def test_admin_bulk_upload_live_run_success(client):
#     """Test a successful live run bulk upload."""
#     os.environ['ADMIN_API_KEY'] = 'test-key'
#     headers = {'Authorization': 'Bearer test-key'}
#     payload = {
#         "text_input": "dog,ajá\ncat,ológìnní",
#         "dry_run": False
#     }
#     response = client.post('/api/admin/bulk-upload', headers=headers, json=payload)
#     assert response.status_code == 200
#     data = response.get_json().get('data')
#     assert data['dry_run'] is False
#     assert len(data['successful_pairs']) == 2
#     assert len(data['failed_pairs']) == 0


def test_admin_bulk_upload_with_invalid_data(client):
    """Test bulk upload with a mix of valid and invalid data."""
    os.environ['ADMIN_API_KEY'] = 'test-key'
    headers = {'Authorization': 'Bearer test-key'}
    payload = {
        "text_input": "house,ilé\ninvalid-row\ncar,ọkọ̀ ayọ́kẹ́lẹ́\n,empty_yoruba\nenglish_only,",
        "dry_run": False
    }
    response = client.post('/api/admin/bulk-upload', headers=headers, json=payload)
    assert response.status_code == 200
    data = response.get_json().get('data')
    assert data['dry_run'] is False
    assert len(data['successful_pairs']) == 2
    assert len(data['failed_pairs']) == 3
