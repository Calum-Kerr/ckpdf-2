"""
Authentication and authorization module.
This module provides functions for user authentication and authorization.
"""

import os
import time
import uuid
import logging
import hashlib
import hmac
import base64
from functools import wraps
from flask import request, abort, session, current_app, g

# Configure logging
logger = logging.getLogger(__name__)

# Token expiration time (10 minutes)
TOKEN_EXPIRATION = 600

def generate_csrf_token():
    """
    Generate a CSRF token.

    Returns:
        str: The CSRF token.
    """
    if 'csrf_token' not in session:
        session['csrf_token'] = base64.b64encode(os.urandom(32)).decode('utf-8')

    return session['csrf_token']

def validate_csrf_token(token):
    """
    Validate a CSRF token.

    Args:
        token: The token to validate.

    Returns:
        bool: True if the token is valid, False otherwise.
    """
    if 'csrf_token' not in session:
        return False

    return hmac.compare_digest(session['csrf_token'], token)

def csrf_protected(func):
    """
    Decorator to protect a route from CSRF attacks.

    Args:
        func: The function to decorate.

    Returns:
        The decorated function.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Only check POST, PUT, PATCH, DELETE requests
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            token = request.form.get('csrf_token')
            if not token or not validate_csrf_token(token):
                logger.warning("CSRF token validation failed")
                abort(403)

        return func(*args, **kwargs)

    return wrapper

def generate_api_token():
    """
    Generate a secure API token.

    Returns:
        tuple: (token, expiration_time)
    """
    # Generate a random token
    token = base64.b64encode(os.urandom(32)).decode('utf-8')

    # Set expiration time
    expiration_time = time.time() + TOKEN_EXPIRATION

    return token, expiration_time

def validate_api_token(token):
    """
    Validate an API token.

    Args:
        token: The token to validate.

    Returns:
        bool: True if the token is valid, False otherwise.
    """
    # In a real application, this would check against a database
    # For this example, we'll use the session
    if 'api_token' not in session or 'token_expiration' not in session:
        return False

    # Check if the token matches
    if not hmac.compare_digest(session['api_token'], token):
        return False

    # Check if the token has expired
    if time.time() > session['token_expiration']:
        return False

    return True

def api_token_required(func):
    """
    Decorator to require a valid API token for a route.

    Args:
        func: The function to decorate.

    Returns:
        The decorated function.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Get the token from the request
        token = request.headers.get('X-API-Token')

        # Validate the token
        if not token or not validate_api_token(token):
            logger.warning("API token validation failed")
            abort(401)

        return func(*args, **kwargs)

    return wrapper

def check_origin():
    """
    Check if the request origin is allowed.

    Returns:
        bool: True if the origin is allowed, False otherwise.
    """
    origin = request.headers.get('Origin')

    if not origin:
        # No origin header, could be a direct request
        return True

    # Get allowed origins from app config
    allowed_origins = current_app.config.get('ALLOWED_ORIGINS', [])

    # Add the current host to allowed origins
    host_url = request.host_url.rstrip('/')
    allowed_origins.append(host_url)

    # Check if the origin is allowed
    return origin in allowed_origins

def origin_check_required(func):
    """
    Decorator to check the request origin.

    Args:
        func: The function to decorate.

    Returns:
        The decorated function.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not check_origin():
            logger.warning(f"Origin check failed: {request.headers.get('Origin')}")
            abort(403)

        return func(*args, **kwargs)

    return wrapper

def secure_headers():
    """
    Add security headers to the response.

    Returns:
        dict: Security headers.
    """
    headers = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'SAMEORIGIN',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        # Remove Content-Security-Policy as it's handled by Talisman
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Cache-Control': 'no-store, no-cache, must-revalidate, max-age=0',
        'Pragma': 'no-cache'
    }

    return headers
