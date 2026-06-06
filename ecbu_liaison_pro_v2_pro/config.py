import os
from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

class Config:
    APP_NAME = "ECBU Liaison Pro V2"
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
    raw_db = os.environ.get("DATABASE_URL", "").strip()
    if raw_db.startswith("postgres://"):
        raw_db = raw_db.replace("postgres://", "postgresql+psycopg://", 1)
    elif raw_db.startswith("postgresql://") and "+psycopg" not in raw_db:
        raw_db = raw_db.replace("postgresql://", "postgresql+psycopg://", 1)
    SQLALCHEMY_DATABASE_URI = raw_db or f"sqlite:///{BASE_DIR / 'ecbu_liaison_pro_v2.db'}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 280}
    WTF_CSRF_TIME_LIMIT = None
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Strict"
    SESSION_COOKIE_SECURE = os.environ.get("SECURE_COOKIES", "true").lower() == "true"
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = SESSION_COOKIE_SECURE
    REMEMBER_COOKIE_SAMESITE = "Strict"
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    RATELIMIT_STORAGE_URI = os.environ.get("REDIS_URL") or "memory://"
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024
    MAIL_SERVER = os.environ.get("MAIL_SERVER")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", "587"))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", MAIL_USERNAME)
    APP_BASE_URL = os.environ.get("APP_BASE_URL", "http://127.0.0.1:5000")
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@hopital.cd")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "ChangeMeStrongPassword123!")

class ProductionConfig(Config):
    @classmethod
    def validate(cls):
        missing = [k for k in ("SECRET_KEY", "DATABASE_URL", "ADMIN_EMAIL", "ADMIN_PASSWORD") if not os.environ.get(k)]
        if missing:
            raise RuntimeError("Variables d'environnement manquantes: " + ", ".join(missing))
