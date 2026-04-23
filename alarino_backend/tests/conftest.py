import os


# Tests use create_app(), which requires a database URL unless a test overrides it.
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
