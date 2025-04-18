"""
Security package for the application.
This package provides security features for the application.
"""

import os
import logging
from flask import Flask
from .middleware import SecurityMiddleware
from .data_protection import initialize_secure_storage
from .auth import generate_csrf_token
from .monitoring import SecurityMonitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def init_app(app):
    """
    Initialize security features for the application.

    Args:
        app: The Flask application.
    """
    # Create security log directory
    log_dir = os.path.join(app.instance_path, 'logs', 'security')
    app.config['SECURITY_LOG_DIR'] = log_dir
    os.makedirs(log_dir, exist_ok=True)

    # Initialize security middleware
    SecurityMiddleware(app)

    # Initialize secure storage
    initialize_secure_storage(app)

    # Initialize security monitoring
    SecurityMonitor(app)

    # Add CSRF token to template context
    @app.context_processor
    def inject_csrf_token():
        return {'csrf_token': generate_csrf_token}

    # Log initialization
    logger.info("Security features initialized")

    return app
