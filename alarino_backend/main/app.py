# app.py
import os
from typing import Any, Dict
from functools import wraps
from flask import request, jsonify

from main import app, db, _daily_word_cache, logger
from main.languages import Language
from main.translation_service import translate, get_word_of_the_day, APIResponse, get_random_proverb, bulk_upload_words


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        admin_api_key = os.getenv('ADMIN_API_KEY')
        if not admin_api_key:
            return APIResponse.error("Admin API key not configured.", 500).as_response()

        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return APIResponse.error("Authorization header is missing or invalid.", 401).as_response()

        provided_key = auth_header.split(' ')[1]
        if provided_key != admin_api_key:
            return APIResponse.error("Invalid API key.", 401).as_response()
        
        return f(*args, **kwargs)
    return decorated_function


@app.route('/api/translate', methods=['POST'])
def get_translation():
    """
    Receives JSON data with:
    {
      "text": "Hello",
      "source_lang": "en",
      "target_lang": "yo"
    }
    and returns a JSON response with:
    of type APIResponse, status
    """
    # Extract JSON payload
    data: Dict[str, Any] | None = request.get_json()
    logger.info("got translation request: \t%s", data)

    # Validate the required fields
    if not data or not all(k in data for k in ['text', 'source_lang', 'target_lang']):
        return APIResponse.error("Invalid request body.", 400).as_response()

    try:
        text: str = data['text']
        source_language: Language = Language(data['source_lang'])
        target_language: Language = Language(data['target_lang'])
    except ValueError:
        return APIResponse.error("Unsupported language.", 400).as_response()

    # Call translation
    response: Dict[str, Any]
    status: int
    response, status = translate(
        db, text, source_language, target_language,
        request.remote_addr, request.headers.get("User-Agent", "unknown")
    )

    return jsonify(response), status


@app.route('/api/daily-word', methods=['GET'])
def word_of_day():
    """
    Returns the word of the day in Yoruba with its English translation.
    The word changes daily and is cached to prevent redundant database queries.
    """
    logger.info("Word of the day request received")

    response, status = get_word_of_the_day(db, _daily_word_cache)
    return jsonify(response), status


@app.route('/api/proverb', methods=['GET'])
def get_proverb():
    """
    Returns a random proverb from the database.
    """
    logger.info("Proverb request received")
    response, status = get_random_proverb(db)
    return jsonify(response), status


@app.route('/api/admin/bulk-upload', methods=['POST'])
@admin_required
def admin_bulk_upload():
    """
    Admin endpoint for bulk uploading word pairs.
    Requires a secret API key for authorization.
    """
    # Extract JSON payload
    data: Dict[str, Any] | None = request.get_json()
    if not data or 'text_input' not in data:
        return APIResponse.error("Invalid request body, 'text_input' is required.", 400).as_response()

    text_input = data['text_input']
    dry_run = data.get('dry_run', True)

    response, status = bulk_upload_words(db, text_input, dry_run)
    return jsonify(response), status


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        "success": True,
        "status": 200,
        "message": "ok",
        "data": None
    }), 200


if __name__ == '__main__':
    port = int(os.getenv("MAIN_PORT", "5001"))
    app.run(host="0.0.0.0", port=port, threaded=True)
