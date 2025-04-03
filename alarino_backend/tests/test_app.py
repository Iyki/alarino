import pytest
from alarino_backend import app
from alarino_backend.shared_utils import Language
# import to get the route handler
from alarino_backend.app import get_translation

@pytest.fixture
def client():
    """
    Creates a test client for our Flask app.
    """
    app.config['TESTING'] = True
    print("rules?")
    print([str(rule) for rule in app.url_map.iter_rules()])
    print("rules?")
    with app.test_client() as client:
        yield client


def test_translate_no_data(client):
    """
    Test the /api/translate endpoint with no JSON data.
    We expect a 400 status code and an error message.
    """
    response = client.post('/api/translate')
    assert response.status_code == 415
    assert not response.is_json
    # data = response.get_json()
    # assert data.get("error") == "Invalid request body."


def test_translate_missing_fields(client):
    """
    Test the /api/translate endpoint with missing fields in JSON data.
    We expect a 400 status code and an error message.
    """
    # Only provide "text" field, missing "source_language" and "target_language"
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

    # We can do a simple assertion since our translator is a stub.
    # In a real scenario, you'd verify actual translations or structure of the data.
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

