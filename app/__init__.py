"""
RevisePDF Application Package

This module initializes the Flask application and registers all necessary
components such as blueprints, extensions, and error handlers.
"""

import os
import datetime
from flask import Flask
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect()

def create_app(test_config=None):
    """
    Create and configure the Flask application.

    Args:
        test_config (dict, optional): Test configuration to override default configs.

    Returns:
        Flask: Configured Flask application instance.
    """
    # Create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    # Set default configuration
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
        UPLOAD_FOLDER=os.path.join(app.instance_path, 'uploads'),
        MAX_CONTENT_LENGTH=50 * 1024 * 1024,  # 50MB max upload size
        ALLOWED_EXTENSIONS={'pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'html', 'zip'},
    )

    if test_config is None:
        # Load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # Load the test config if passed in
        app.config.from_mapping(test_config)

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path, exist_ok=True)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    except OSError:
        pass

    # Initialize CSRF protection
    csrf.init_app(app)

    # Register blueprints
    from app.routes import main_bp, optimize_bp, convert_to_pdf_bp, edit_bp, organize_bp, convert_from_pdf_bp, security_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(optimize_bp)
    app.register_blueprint(convert_to_pdf_bp)
    app.register_blueprint(edit_bp)
    app.register_blueprint(organize_bp)
    app.register_blueprint(convert_from_pdf_bp)
    app.register_blueprint(security_bp)

    # Register error handlers
    from app.errors import register_error_handlers
    register_error_handlers(app)

    # Set up OCR engine
    with app.app_context():
        try:
            from tools.setup_tesseract import setup_tesseract_environment
            setup_tesseract_environment()
        except ImportError:
            app.logger.warning("OCR setup module not found. OCR functionality may be limited.")
        except Exception as e:
            app.logger.warning(f"Error setting up OCR engine: {str(e)}. OCR functionality may be limited.")

    # Register template filters
    @app.template_filter('basename')
    def basename_filter(path):
        """Extract the basename from a path."""
        return os.path.basename(path)

    # Add context processors
    @app.context_processor
    def inject_current_year():
        """Inject the current year into all templates."""
        return {'current_year': datetime.datetime.now().year}

    return app
