"""
Nexus AI – Application Configuration
=====================================
Environment-based configuration with support for Development,
Testing, and Production modes. All secrets loaded from .env file.
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class BaseConfig:
    """Base configuration shared across all environments."""

    # ── Flask Core ──────────────────────────────────────────────
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-fallback-secret-key")

    # ── JWT ─────────────────────────────────────────────────────
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-fallback-jwt-key")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        hours=int(os.getenv("JWT_ACCESS_TOKEN_HOURS", "24"))
    )
    JWT_TOKEN_LOCATION = ["headers"]

    # ── MongoDB Atlas ───────────────────────────────────────────
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/nexus_ai")

    # ── AI Service Keys ─────────────────────────────────────────
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

    # ── File Uploads ────────────────────────────────────────────
    UPLOAD_FOLDER = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "uploads"
    )
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", str(16 * 1024 * 1024)))
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "pdf", "txt"}

    # ── Google OAuth ────────────────────────────────────────────
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")

    # ── CORS ────────────────────────────────────────────────────
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")


class DevelopmentConfig(BaseConfig):
    """Development-specific overrides."""
    DEBUG = True
    TESTING = False


class TestingConfig(BaseConfig):
    """Testing-specific overrides."""
    DEBUG = False
    TESTING = True
    MONGO_URI = "mongodb://localhost:27017/nexus_ai_test"


class ProductionConfig(BaseConfig):
    """Production-specific overrides."""
    DEBUG = False
    TESTING = False


# ── Config selector ─────────────────────────────────────────────
config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config():
    """Return the configuration class for the current environment."""
    env = os.getenv("FLASK_ENV", "development").lower()
    return config_by_name.get(env, DevelopmentConfig)
