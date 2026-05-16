from __future__ import annotations

import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-change-me")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///chess_behavioral.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    LICHESS_CLIENT_ID = os.getenv("LICHESS_CLIENT_ID", "")
    LICHESS_PERSONAL_TOKEN = os.getenv("LICHESS_PERSONAL_TOKEN", "")
    LICHESS_OAUTH_AUTHORIZE_URL = os.getenv("LICHESS_OAUTH_AUTHORIZE_URL", "https://lichess.org/oauth")
    LICHESS_OAUTH_TOKEN_URL = os.getenv("LICHESS_OAUTH_TOKEN_URL", "https://lichess.org/api/token")
    LICHESS_API_BASE = os.getenv("LICHESS_API_BASE", "https://lichess.org/api")

    REDIS_URL = os.getenv("REDIS_URL", "")
    ENABLE_BACKGROUND_JOBS = os.getenv("ENABLE_BACKGROUND_JOBS", "0") == "1"

    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "0") == "1"
    REMEMBER_COOKIE_SECURE = os.getenv("REMEMBER_COOKIE_SECURE", "0") == "1"


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}
