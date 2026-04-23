import logging
import os
from datetime import date
from typing import Dict, Tuple


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(processName)s] %(message)s",
    handlers=[
        logging.FileHandler("../seed.log"),
        logging.StreamHandler(),
    ],
)

logger: logging.Logger = logging.getLogger("main")
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
