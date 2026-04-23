import logging
import os
import sys
from datetime import date
from pathlib import Path
from typing import Dict, Tuple

LOG_FORMAT = "%(asctime)s [%(levelname)s] [%(processName)s] %(message)s"


logger: logging.Logger = logging.getLogger("alarino_backend")
_daily_word_cache: Dict[date, Tuple[str, str]] = {}


def configure_logging() -> None:
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    log_file_path = os.getenv("ALARINO_LOG_FILE")

    if log_file_path:
        try:
            path = Path(log_file_path).expanduser()
            path.parent.mkdir(parents=True, exist_ok=True)
            handlers.append(logging.FileHandler(path))
        except OSError as exc:
            print(f"Unable to configure ALARINO_LOG_FILE={log_file_path}: {exc}", file=sys.stderr)

    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, handlers=handlers)


def get_allowed_origins() -> list[str]:
    return [
        origin.strip()
        for origin in os.getenv(
            "CORS_ALLOWED_ORIGINS",
            "http://localhost:3000,http://127.0.0.1:3000,https://alarino.com,https://www.alarino.com",
        ).split(",")
        if origin.strip()
    ]


configure_logging()
