#app.py
from typing import Any, Dict, Tuple

from main import app, db, _daily_word_cache, logger
from flask import request, jsonify
from main.languages import Language
from main.translation_service import translate, get_word_of_the_day, APIResponse

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

if __name__ == '__main__':
    app.run(port=5001, debug=True)
