"""
Authentication package for the application.
This package provides authentication features using Supabase.
"""

import os
import logging
from flask import Flask

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def init_app(app):
    """
    Initialize authentication features for the application.

    Args:
        app: The Flask application.
    """
    # Create auth log directory
    log_dir = os.path.join(app.instance_path, 'logs', 'auth')
    app.config['AUTH_LOG_DIR'] = log_dir
    os.makedirs(log_dir, exist_ok=True)

    # Initialize Supabase client
    from .supabase_client import init_supabase
    init_supabase()

    # Apply file size validation to all routes
    from .middleware import apply_file_size_validation
    apply_file_size_validation(app)

    # Log initialization
    logger.info("Authentication features initialized")

    return app
