import os

from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))

class Config:
    """Base configuration with environment-based defaults."""

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production-123")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret-key-change-in-production-456")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", f"sqlite:///{os.path.join(basedir, 'pos_system_v01.db')}"
    )

    USD_TO_LBP_EXCHANGE_RATE = float(os.getenv("USD_TO_LBP_EXCHANGE_RATE", "90000.0"))
    PRIMARY_CURRENCY_CODE = os.getenv("PRIMARY_CURRENCY_CODE", "LBP")
    SECONDARY_CURRENCY_CODE = os.getenv("SECONDARY_CURRENCY_CODE", "USD")
    LBP_ROUNDING_FACTOR = int(os.getenv("LBP_ROUNDING_FACTOR", "5000"))

    @staticmethod
    def warn_if_default_keys():
        if not os.getenv("SECRET_KEY"):
            print("[WARNING] Using default SECRET_KEY. Set it in .env for production.")
        if not os.getenv("JWT_SECRET_KEY"):
            print(
                "[WARNING] Using default JWT_SECRET_KEY. Set it in .env for production."
            )

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = True

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "TEST_DATABASE_URL",
        f"sqlite:///{os.path.join(basedir, 'pos_system_v01_test.db')}",
    )

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_ECHO = False

config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}

def get_config_name():
    return os.getenv("FLASK_CONFIG", "default")

current_config = config_by_name[get_config_name()]
current_config.warn_if_default_keys()