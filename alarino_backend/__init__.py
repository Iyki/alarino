import logging
import os

from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from dotenv import load_dotenv

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    # format="%(asctime)s [%(levelname)s] %(message)s",
    format="%(asctime)s [%(levelname)s] [%(processName)s] %(message)s",
    handlers=[
        logging.FileHandler("seed.log"),   # log to a file
        logging.StreamHandler()            # and to the console
    ]
)
logger = logging.getLogger(__name__)


load_dotenv()
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy()
db.init_app(app)

