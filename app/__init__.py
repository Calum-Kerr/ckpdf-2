"""
RevisePDF Application Package

This module initializes the Flask application and registers all necessary
components such as blueprints, extensions, and error handlers.
"""

import os
import datetime
import logging
from flask import Flask
from flask_wtf.csrf import CSRFProtect
from flask_talisman import Talisman

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

csrf = CSRFProtect()
talisman = Talisman()

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
        SECURE_STORAGE_DIR=os.path.join(app.instance_path, 'secure_storage'),
        MAX_CONTENT_LENGTH=50 * 1024 * 1024,  # 50MB max upload size
        ALLOWED_EXTENSIONS={'pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'html', 'zip'},
        ALLOWED_ORIGINS=[f"https://{os.environ.get('DOMAIN', 'revisepdf.com')}"],
        SECURE_STORAGE_RETENTION=600,  # 10 minutes
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        PERMANENT_SESSION_LIFETIME=datetime.timedelta(hours=1),
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
        os.makedirs(app.config['SECURE_STORAGE_DIR'], exist_ok=True)
    except OSError as e:
        logger.error(f"Error creating directories: {str(e)}")

    # Initialize security features
    csrf.init_app(app)

    # Initialize Talisman for HTTPS and security headers
    csp = {
        'default-src': '\'self\'',
        'script-src': '\'self\'',
        'style-src': ['\'self\'', '\'unsafe-inline\''],  # Allow inline styles for Bootstrap
        'img-src': ['\'self\'', 'data:'],  # Allow data URLs for images
        'font-src': '\'self\'',
        'connect-src': '\'self\'',
        'object-src': '\'none\'',
    }

    talisman.init_app(
        app,
        content_security_policy=csp,
        content_security_policy_nonce_in=['script-src'],
        force_https=not app.debug,  # Don't force HTTPS in debug mode
        session_cookie_secure=app.config['SESSION_COOKIE_SECURE'],
        session_cookie_http_only=app.config['SESSION_COOKIE_HTTPONLY'],
        strict_transport_security=True,
        strict_transport_security_preload=True,
        referrer_policy='strict-origin-when-cross-origin'
    )

    # Initialize custom security features
    from app.security import init_app as init_security
    init_security(app)

    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.security_api import security_api_bp

    # Import blueprints directly from the original routes.py file
    from app.routes import main_bp as _  # Dummy import to avoid circular imports
    import sys
    import importlib.util

    # Load the routes.py module directly
    spec = importlib.util.spec_from_file_location("routes", "app/routes.py")
    routes = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(routes)

    # Get blueprints from the routes module
    optimize_bp = routes.optimize_bp
    convert_to_pdf_bp = routes.convert_to_pdf_bp
    edit_bp = routes.edit_bp
    organize_bp = routes.organize_bp
    convert_from_pdf_bp = routes.convert_from_pdf_bp
    security_bp = routes.security_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(optimize_bp)
    app.register_blueprint(convert_to_pdf_bp)
    app.register_blueprint(edit_bp)
    app.register_blueprint(organize_bp)
    app.register_blueprint(convert_from_pdf_bp)
    app.register_blueprint(security_bp)
    app.register_blueprint(security_api_bp)

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

    # Add request ID to all requests for tracking
    @app.before_request
    def assign_request_id():
        from flask import g
        import uuid
        g.request_id = str(uuid.uuid4())

    # Log all application startup information
    logger.info(f"Application initialized with environment: {os.environ.get('FLASK_ENV', 'production')}")

    return app
