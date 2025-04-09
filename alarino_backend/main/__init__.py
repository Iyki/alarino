import logging
import os

from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

allowed_origins = os.getenv("CORS_ALLOWED_ORIGINS").split(",")
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
logger = logging.getLogger(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy()
db.init_app(app)

migrate = Migrate()
migrate.init_app(app, db)
