import os
from functools import wraps
from typing import Any, Dict

from dotenv import load_dotenv
from flask import Blueprint, Flask, jsonify, request
from flask_cors import CORS

from main.flask_extensions import db, migrate
from main.languages import Language
from main.response import APIResponse
from main.runtime import _daily_word_cache, get_allowed_origins, logger
from main.translation_service import (
    bulk_upload_words,
    get_random_proverb,
    get_word_of_the_day,
    translate,
    translate_llm,
)

api_bp = Blueprint("api", __name__)


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        admin_api_key = os.getenv("ADMIN_API_KEY")
        if not admin_api_key:
            return APIResponse.error("Admin API key not configured.", 500).as_response()

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return APIResponse.error("Authorization header is missing or invalid.", 401).as_response()

        provided_key = auth_header.split(" ")[1]
        if provided_key != admin_api_key:
            return APIResponse.error("Invalid API key.", 401).as_response()

        return f(*args, **kwargs)

    return decorated_function


def require_translation_params(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        data: Dict[str, Any] | None = request.get_json(silent=True)
        if not data or not all(k in data for k in ["text", "source_lang", "target_lang"]):
            return APIResponse.error("Invalid request body.", 400).as_response()

        try:
            kwargs["text"] = data["text"]
            kwargs["source_language"] = Language(data["source_lang"])
            kwargs["target_language"] = Language(data["target_lang"])
        except ValueError:
            return APIResponse.error("Unsupported language.", 400).as_response()

        return f(*args, **kwargs)

    return decorated_function


@api_bp.route("/api/translate", methods=["POST"])
@require_translation_params
def get_translation(text: str, source_language: Language, target_language: Language):
    logger.info("got translation request: \t%s", text)

    response: Dict[str, Any]
    status: int
    response, status = translate(
        db,
        text,
        source_language,
        target_language,
        request.remote_addr,
        request.headers.get("User-Agent", "unknown"),
    )

    return jsonify(response), status


@api_bp.route("/api/translate/llm", methods=["POST"])
@require_translation_params
def get_llm_translation(text: str, source_language: Language, target_language: Language):
    logger.info("got llm translation request: \t%s", text)

    response: Dict[str, Any]
    status: int
    response, status = translate_llm(text, source_language, target_language)

    return jsonify(response), status


@api_bp.route("/api/daily-word", methods=["GET"])
def word_of_day():
    logger.info("Word of the day request received")

    response, status = get_word_of_the_day(db, _daily_word_cache)
    return jsonify(response), status


@api_bp.route("/api/proverb", methods=["GET"])
def get_proverb():
    logger.info("Proverb request received")
    response, status = get_random_proverb(db)
    return jsonify(response), status


@api_bp.route("/api/admin/bulk-upload", methods=["POST"])
@admin_required
def admin_bulk_upload():
    data: Dict[str, Any] | None = request.get_json()
    if not data or "text_input" not in data:
        return APIResponse.error("Invalid request body, 'text_input' is required.", 400).as_response()

    text_input = data["text_input"]
    dry_run = data.get("dry_run", True)

    response, status = bulk_upload_words(db, text_input, dry_run)
    return jsonify(response), status


@api_bp.route("/api/health", methods=["GET"])
def health():
    return jsonify(
        {
            "success": True,
            "status": 200,
            "message": "ok",
            "data": None,
        }
    ), 200


def register_routes(app: Flask) -> None:
    if api_bp.name not in app.blueprints:
        app.register_blueprint(api_bp)


def create_app() -> Flask:
    load_dotenv()

    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    CORS(app, origins=get_allowed_origins())

    db.init_app(app)
    migrate.init_app(app, db)

    with app.app_context():
        import main.db_models  # noqa: F401

    register_routes(app)
    return app


if __name__ == "__main__":
    port = int(os.getenv("MAIN_PORT", "5001"))
    app = create_app()
    app.run(host="0.0.0.0", port=port, threaded=True)
