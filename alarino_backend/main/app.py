from main import app, logger
from flask import request, jsonify
from shared_utils import Language
from translate import translate, APIResponse

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
    {
      "translation": "O nlo..."
    }
    """
    # Extract JSON payload
    data = request.get_json()
    logger.info("got translation request: \t", data)

    # Validate the required fields
    if not data or not all(k in data for k in ['text', 'source_lang', 'target_lang']):
        return APIResponse.error("Invalid request body.", 400).as_response()

    try:
        text = data['text']
        source_language = Language(data['source_lang'])
        target_language = Language(data['target_lang'])
    except ValueError:
        return APIResponse.error("Unsupported language.", 400).as_response()

    # Call translation
    response, status = translate(text, source_language, target_language, request.remote_addr, request.headers.get("User-Agent"))

    return jsonify(response), status

if __name__ == '__main__':
    app.run(port=5001, debug=True)
