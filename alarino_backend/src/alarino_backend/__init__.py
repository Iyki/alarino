"""Backend package namespace for the Alarino Flask API."""

from importlib.metadata import PackageNotFoundError, version
from typing import Any

__all__ = ["__version__", "_daily_word_cache", "create_app", "db", "logger", "migrate"]

try:
    __version__ = version("alarino-backend")
except PackageNotFoundError:
    __version__ = "0.0.0"


def __getattr__(name: str) -> Any:
    if name == "create_app":
        from alarino_backend.app import create_app

        return create_app
    if name in {"db", "migrate"}:
        from alarino_backend.flask_extensions import db, migrate

        return {"db": db, "migrate": migrate}[name]
    if name in {"_daily_word_cache", "logger"}:
        from alarino_backend.runtime import _daily_word_cache, logger

        return {"_daily_word_cache": _daily_word_cache, "logger": logger}[name]
    raise AttributeError(f"module 'alarino_backend' has no attribute {name!r}")
