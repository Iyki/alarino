import sys
import os

# Add the parent of the current script (the repo root) to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from alarino_backend import app, logger
from flask import request, jsonify
from alarino_backend.shared_utils import Language
from alarino_backend.translate import translate, APIResponse

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
        return APIResponse.error("Invalid request body"), 400

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
