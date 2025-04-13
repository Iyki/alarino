#__init__.py
import logging
import os
from typing import Dict
# import sys
# # Add the parent of the current script (the repo root) to the path
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from datetime import date
from dotenv import load_dotenv

load_dotenv()

app: Flask = Flask(__name__)

allowed_origins: list[str] = os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")
CORS(app, origins=allowed_origins)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(processName)s] %(message)s",
    handlers=[
        logging.FileHandler("../seed.log"),  # log to a file
        logging.StreamHandler()  # and to the console
    ]
)
logger: logging.Logger = logging.getLogger(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db: SQLAlchemy = SQLAlchemy()
db.init_app(app)

migrate: Migrate = Migrate()
migrate.init_app(app, db)

# In-memory cache
_daily_word_cache: Dict[date, str] = {}
