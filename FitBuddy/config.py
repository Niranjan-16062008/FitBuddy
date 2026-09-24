import os
from pathlib import Path

from dotenv import load_dotenv


# Always load .env from the FitBuddy project directory.
BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_FILE)


class Config:
    """Application configuration."""

    SECRET_KEY = os.getenv("SECRET_KEY", "").strip()
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

    SQLALCHEMY_DATABASE_URI = (
        f"sqlite:///{BASE_DIR / 'instance' / 'fitbuddy.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False

    MAX_CONTENT_LENGTH = 2 * 1024 * 1024