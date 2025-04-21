"""
Authentication middleware.
This module provides middleware for authentication and file size validation.
"""

import logging
from functools import wraps
from flask import request, flash, redirect, url_for, session, current_app
from werkzeug.utils import secure_filename
from .utils import get_current_user, check_file_size_limit, track_file_usage

# Configure logging
logger = logging.getLogger(__name__)

def validate_file_size(f):
    """
    Decorator to validate file size based on user's account type.

    Args:
        f: The function to decorate.

    Returns:
        function: The decorated function.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method == 'POST' and 'file' in request.files:
            file = request.files['file']

            if file.filename != '':
                # Get current user ID if logged in
                user = get_current_user()
                user_id = user.get('id') if user else None

                # Check file size against user's limit
                file_size = request.content_length
                if not check_file_size_limit(file_size, user_id):
                    # Get the limit in MB for display
                    from .utils import get_file_size_limit
                    limit_mb = get_file_size_limit(user_id) / (1024 * 1024)

                    flash(f'File size exceeds your limit of {limit_mb:.1f} MB. Please upgrade your account to process larger files.', 'warning')

                    if user_id:
                        return redirect(url_for('auth.dashboard'))
                    else:
                        return redirect(url_for('auth.register'))

                # Track file usage for logged-in users
                if user_id:
                    track_file_usage(user_id, file_size)

        return f(*args, **kwargs)

    return decorated_function


def apply_file_size_validation(app):
    """
    Apply file size validation to all routes that handle file uploads.

    Args:
        app: The Flask application.
    """
    # Get all view functions
    for endpoint, view_func in app.view_functions.items():
        # Skip static and auth endpoints
        if endpoint.startswith('static') or endpoint.startswith('auth.'):
            continue

        # Apply the decorator to all other view functions
        if not hasattr(view_func, '_file_size_validated'):
            app.view_functions[endpoint] = validate_file_size(view_func)
            app.view_functions[endpoint]._file_size_validated = True

    logger.info("File size validation applied to all routes")
