import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(ROOT / ".env")


class Settings:
    db_host: str = os.environ.get("DB_HOST", "127.0.0.1")
    db_port: int = int(os.environ.get("DB_PORT", "3306"))
    db_name: str = os.environ.get("DB_NAME", "snapandtrack")
    db_user: str = os.environ["DB_USER"]
    db_password: str = os.environ["DB_PASSWORD"]
    secret_key: str = os.environ["SECRET_KEY"]
    gemini_api_key: str = os.environ.get("GEMINI_API_KEY", "")
    gemini_model: str = os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite")
    ai_daily_cap: int = int(os.environ.get("AI_DAILY_CAP", "200"))
    session_max_age: int = 60 * 60 * 24 * 14


settings = Settings()
