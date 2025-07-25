# app.py
import os
from typing import Any, Dict
from functools import wraps
import markdown
from flask import request, jsonify, send_file, abort, render_template

from main import app, db, _daily_word_cache, logger
from main.languages import Language
from main.translation_service import translate, get_word_of_the_day, APIResponse, get_random_proverb, bulk_upload_words
from main.utils import find_file

app.template_folder = find_file("templates/about.html", get_dir=True)


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


@app.route('/')
def serve_index():
    """Serve the main index.html file"""
    homepage = 'homepage.html'
    file_path = find_file(homepage)
    if file_path:
        return render_template(homepage)
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


@app.route('/admin')
def admin_page():
    """Serve the admin.html file"""
    return render_template('admin.html')


@app.route("/about")
@app.route("/about.html")
def about():
    filepath = find_file("about.md")
    with open(filepath, 'r', encoding='utf-8') as f:
        md_content = f.read()
    html_content = markdown.markdown(md_content)
    template_path = "about.html"
    val = render_template(template_path, content=html_content)
    return val


# Route for static files with known extensions for rendering
@app.route('/<filename>')
def serve_root_static_file(filename):
    """Serve static files from the root directory with extension checking"""
    # List of allowed file extensions for security
    allowed_extensions = [
        '.js', '.css', '.svg', '.png', '.jpg', '.html', '.xml', '.md',
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


if __name__ == '__main__':
    port = int(os.getenv("MAIN_PORT", "5001"))
    app.run(host="0.0.0.0", port=port, threaded=True)
