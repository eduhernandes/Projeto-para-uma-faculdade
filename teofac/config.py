from dotenv import load_dotenv
load_dotenv()

from datetime import timedelta
import os
import secrets

class BaseConfig:
    APP_NAME = "TéoFac Acadêmico"
    SECRET_KEY = os.getenv("SECRET_KEY") or secrets.token_hex(32)
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///teologia.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=int(os.getenv("SESSION_LIFETIME_MINUTES", "30")))
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
    SESSION_COOKIE_SAMESITE = "Lax"
    WTF_CSRF_TIME_LIMIT = 3600
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")
    RATELIMIT_HEADERS_ENABLED = True
    RATELIMIT_DEFAULT = []
    TRUSTED_HOSTS = [h.strip() for h in os.getenv("TRUSTED_HOSTS", "").split(",") if h.strip()] or None

class DevelopmentConfig(BaseConfig):
    DEBUG = True
    TESTING = False

class TestingConfig(BaseConfig):
    TESTING = True
    DEBUG = False
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    RATELIMIT_ENABLED = False
    SECRET_KEY = secrets.token_hex(32)

class TestDatabaseConfig(TestingConfig):
    SQLALCHEMY_DATABASE_URI = "sqlite:///test_teologia.db"

class ProductionConfig(BaseConfig):
    SECRET_KEY = os.getenv("SECRET_KEY")
    SESSION_COOKIE_NAME = "__Host-teofac_session"
    SESSION_COOKIE_PATH = "/"
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    @classmethod
    def validate(cls):
        if not cls.SECRET_KEY or len(cls.SECRET_KEY) < 32:
            raise RuntimeError("SECRET_KEY deve ter pelo menos 32 caracteres em produção.")

def get_config(name):
    config = {
        "development": DevelopmentConfig,
        "testing": TestingConfig,
        "testdb": TestDatabaseConfig,
        "production": ProductionConfig,
    }.get(name.lower(), DevelopmentConfig)
    if config is ProductionConfig:
        config.validate()
    return config
