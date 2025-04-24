#app.py
import os
from typing import Any, Dict

from main import app, db, _daily_word_cache, logger
from flask import request, jsonify, send_file, abort
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

@app.route('/')
def serve_index():
    """Serve the main index.html file"""
    homepage = 'homepage.html'
    file_path = find_file(homepage)
    if file_path:
        return send_file(file_path)
    else:
        logger.error("Error serving homepage: Could not find homepage.html file")
        return "Homepage file not found", 404

@app.route('/word/<word>')
def word_page(word):
    """
    Route to handle individual English word pages.
    Simply serve the main index.html file and let JavaScript handle
    the word lookup based on the URL.
    Args:
        word: The English word to display
    Returns:
        The main index.html file
    """
    return serve_index()

# Route for static files with known extensions for rendering
@app.route('/<filename>')
def serve_root_static_file(filename):
    """Serve static files from the root directory with extension checking"""
    # List of allowed file extensions for security
    allowed_extensions = [
        '.js', '.css', '.svg', '.png', '.jpg',
        '.jpeg', '.ico', '.gif', '.woff', '.woff2'
    ]

    # Check if the filename has an allowed extension
    if not any(filename.endswith(ext) for ext in allowed_extensions):
        return "Not found", 404

    file_path = find_file(filename)
    if file_path:
        return send_file(file_path)
    else:
        return "File not found", 404

@app.route('/sitemap.xml')
def serve_sitemap():
    """Serve the sitemap.xml file"""
    file_path = find_file('sitemap.xml')
    if file_path:
        return send_file(file_path)
    else:
        return "Sitemap not found", 404

# Catch-all route for any other URLs
@app.route('/<path:path>')
def catch_all(path):
    """Catch-all route that handles any other paths"""
    # Handle API routes properly
    if path.startswith('api/'):
        abort(404)  # Let the API routes handle these

    # For any other routes, serve the homepage
    return serve_index()

@app.route('/robots.txt')
def serve_robots():
    """Serve the robots.txt file"""
    file_path = find_file('robots.txt')
    if file_path:
        return send_file(file_path)
    else:
        return "Robots.txt not found", 404



# Define paths to look for static files
def get_static_file_paths():
    """Returns ordered list of paths to check for static files"""
    return [
        os.path.join(app.root_path, '../static'),  # /main/static/ or /app/static
        app.root_path,  # alarino_backend/main/
        os.path.join(app.root_path, '../../alarino_frontend')  # project root
    ]

def find_file(filename:str, paths=None):
    """Search for a file in multiple directories"""
    if paths is None:
        paths = get_static_file_paths()

    for path in paths:
        file_path = os.path.join(path, filename)
        if os.path.isfile(file_path):
            return file_path
    return None

if __name__ == '__main__':
    port = int(os.getenv("MAIN_PORT", "5001"))
    app.run(host="0.0.0.0", port=port, threaded=True)
