"""
Configuration settings for the Cafe24 POS Flask application.

This module defines different configuration classes for development, testing,
and production environments.
"""
import os

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base configuration class with common settings."""
    
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    
    # Database configuration
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    
    # JWT configuration
    JWT_ACCESS_TOKEN_EXPIRES = False
    
    # Currency settings
    DEFAULT_CURRENCY_USD = True
    DEFAULT_EXCHANGE_RATE_USD_TO_LBP = 90000.0
    
    @staticmethod
    def warn_if_default_keys():
        """Warn if default security keys are being used."""
        if Config.SECRET_KEY == 'dev-secret-key-change-in-production':
            print("WARNING: Using default SECRET_KEY. Change this in production!")
        if Config.JWT_SECRET_KEY == 'jwt-secret-key-change-in-production':
            print("WARNING: Using default JWT_SECRET_KEY. Change this in production!")


class DevelopmentConfig(Config):
    """Development environment configuration."""
    
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///cafe24_dev.db')
    
    @staticmethod
    def init_app(app):
        """Initialize development-specific app configuration."""
        Config.warn_if_default_keys()


class TestingConfig(Config):
    """Testing environment configuration."""
    
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """Production environment configuration."""
    
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///cafe24.db')
    
    @staticmethod
    def init_app(app):
        """Initialize production-specific app configuration."""
        # Import here to avoid circular imports
        import logging
        from logging.handlers import RotatingFileHandler
        
        # Set up file logging
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = RotatingFileHandler(
            'logs/cafe24.log', maxBytes=10240, backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Cafe24 POS startup')


# Configuration mapping
config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


def get_config_name():
    """Get the current configuration name from environment."""
    return os.getenv("FLASK_CONFIG", "default")


# Initialize current configuration
current_config = config_by_name[get_config_name()]
current_config.warn_if_default_keys()
