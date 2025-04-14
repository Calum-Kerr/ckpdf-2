"""
RevisePDF Configuration Module

This module contains configuration settings for the RevisePDF application.
It includes settings for different environments (development, testing, production).
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration class with settings common to all environments."""

    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-for-development-only')

    # File upload settings
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'uploads')
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max upload size
    ALLOWED_EXTENSIONS = {
        'pdf', 'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'tif',
        'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'html', 'zip'
    }

    # Ghostscript settings
    GHOSTSCRIPT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ghostscript')

    # OCR settings
    OCR_ENGINE_CMD = os.environ.get('TESSERACT_CMD', 'tesseract')  # Keep env var name for compatibility

    # LibreOffice settings
    LIBREOFFICE_CMD = os.environ.get('LIBREOFFICE_CMD', 'libreoffice')

    # Temporary directory
    TEMP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'temp')


class DevelopmentConfig(Config):
    """Configuration for development environment."""

    DEBUG = True
    TESTING = False


class TestingConfig(Config):
    """Configuration for testing environment."""

    DEBUG = False
    TESTING = True
    # Use a separate upload folder for testing
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'test_uploads')
    TEMP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'test_temp')


class ProductionConfig(Config):
    """Configuration for production environment."""

    DEBUG = False
    TESTING = False
    # In production, use a strong secret key
    SECRET_KEY = os.environ.get('SECRET_KEY')

    # In production, we might use different paths for external tools
    GHOSTSCRIPT_PATH = os.environ.get('GHOSTSCRIPT_PATH', Config.GHOSTSCRIPT_PATH)
    OCR_ENGINE_CMD = os.environ.get('TESSERACT_CMD', 'tesseract')  # Keep env var name for compatibility
    LIBREOFFICE_CMD = os.environ.get('LIBREOFFICE_CMD', 'libreoffice')


# Dictionary mapping environment names to config classes
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

# Get the current configuration based on the environment
current_config = config[os.environ.get('FLASK_ENV', 'default')]
