"""Backend package namespace for packaging and future module migration."""

from importlib.metadata import PackageNotFoundError, version

__all__ = ["__version__"]

try:
    __version__ = version("alarino-backend")
except PackageNotFoundError:
    __version__ = "0.0.0"
