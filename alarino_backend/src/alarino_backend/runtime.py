import logging
import os
from pathlib import Path
from datetime import date
from typing import Dict, Tuple

LOG_FILE_PATH = Path(__file__).resolve().parents[2] / "seed.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(processName)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE_PATH),
        logging.StreamHandler(),
    ],
)

logger: logging.Logger = logging.getLogger("alarino_backend")
_daily_word_cache: Dict[date, Tuple[str, str]] = {}


def get_allowed_origins() -> list[str]:
    return [
        origin.strip()
        for origin in os.getenv(
            "CORS_ALLOWED_ORIGINS",
            "http://localhost:3000,http://127.0.0.1:3000,https://alarino.com,https://www.alarino.com",
        ).split(",")
        if origin.strip()
    ]
