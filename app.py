from flask import Flask, request, jsonify
from translator.translation_service import translate

app = Flask(__name__)

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
    print("got request: ack")
    data = request.get_json()
    print("got request: \t", data)

    # Validate the required fields
    if not data or not all(k in data for k in ['text', 'source_lang', 'target_lang']):
        return jsonify({"error": "Invalid request body."}), 400

    text = data['text']
    source_language = data['source_lang']
    target_language = data['target_lang']

    # Call the translation service
    translation_result = translate(text, source_language, target_language)

    return jsonify({
        "translation": translation_result
    })

if __name__ == '__main__':
    app.run(port=5001, debug=True)
