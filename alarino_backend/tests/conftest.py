import os


# App import currently reads configuration at module import time.
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
