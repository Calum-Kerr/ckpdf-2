"""
Security middleware module.
This module provides middleware functions for Flask applications.
"""

import time
import logging
import re
from flask import request, g, abort, current_app
from werkzeug.exceptions import HTTPException
from .auth import secure_headers

# Configure logging
logger = logging.getLogger(__name__)

class SecurityMiddleware:
    """Middleware for adding security features to a Flask application."""
    
    def __init__(self, app=None):
        """
        Initialize the middleware.
        
        Args:
            app: The Flask application.
        """
        self.app = app
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """
        Initialize the middleware with a Flask application.
        
        Args:
            app: The Flask application.
        """
        # Register before_request handlers
        app.before_request(self.log_request)
        app.before_request(self.check_request_method)
        app.before_request(self.check_content_type)
        app.before_request(self.check_request_size)
        app.before_request(self.check_suspicious_patterns)
        
        # Register after_request handlers
        app.after_request(self.add_security_headers)
        
        # Register errorhandler
        app.errorhandler(Exception)(self.handle_exception)
    
    def log_request(self):
        """Log the request details."""
        g.request_start_time = time.time()
        
        # Log basic request info
        logger.info(f"Request: {request.method} {request.path} from {request.remote_addr}")
        
        # Log headers (excluding sensitive ones)
        headers = {k: v for k, v in request.headers.items() 
                  if k.lower() not in ['authorization', 'cookie']}
        logger.debug(f"Headers: {headers}")
    
    def check_request_method(self):
        """Check if the request method is allowed."""
        allowed_methods = current_app.config.get('ALLOWED_METHODS', ['GET', 'POST', 'PUT', 'DELETE'])
        
        if request.method not in allowed_methods:
            logger.warning(f"Method not allowed: {request.method}")
            abort(405)
    
    def check_content_type(self):
        """Check the Content-Type header for potentially malicious types."""
        if request.method in ['POST', 'PUT', 'PATCH']:
            content_type = request.headers.get('Content-Type', '')
            
            # List of allowed content types
            allowed_types = [
                'application/x-www-form-urlencoded',
                'multipart/form-data',
                'application/json',
                'application/pdf'
            ]
            
            # Check if the content type starts with an allowed type
            if not any(content_type.startswith(allowed_type) for allowed_type in allowed_types):
                logger.warning(f"Unsupported Content-Type: {content_type}")
                abort(415)
    
    def check_request_size(self):
        """Check if the request size is within limits."""
        max_content_length = current_app.config.get('MAX_CONTENT_LENGTH', 50 * 1024 * 1024)  # 50MB default
        
        if request.content_length and request.content_length > max_content_length:
            logger.warning(f"Request too large: {request.content_length} bytes")
            abort(413)
    
    def check_suspicious_patterns(self):
        """Check for suspicious patterns in the request."""
        # Check URL for suspicious patterns
        url = request.url
        
        # Patterns to check for
        suspicious_patterns = [
            r'\.\./',  # Directory traversal
            r'%2e%2e/',  # URL-encoded directory traversal
            r'select.*from',  # SQL injection
            r'union.*select',  # SQL injection
            r'<script',  # XSS
            r'javascript:',  # XSS
            r'onload=',  # XSS
            r'onerror=',  # XSS
            r'eval\(',  # JavaScript injection
            r'document\.cookie',  # Cookie stealing
        ]
        
        # Check each pattern
        for pattern in suspicious_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                logger.warning(f"Suspicious pattern detected in URL: {pattern}")
                abort(400)
        
        # Check form data for suspicious patterns
        if request.form:
            for key, value in request.form.items():
                for pattern in suspicious_patterns:
                    if re.search(pattern, value, re.IGNORECASE):
                        logger.warning(f"Suspicious pattern detected in form data: {pattern}")
                        abort(400)
    
    def add_security_headers(self, response):
        """
        Add security headers to the response.
        
        Args:
            response: The Flask response.
            
        Returns:
            The modified response.
        """
        headers = secure_headers()
        
        for key, value in headers.items():
            response.headers[key] = value
        
        # Log response time
        if hasattr(g, 'request_start_time'):
            response_time = time.time() - g.request_start_time
            logger.info(f"Response time: {response_time:.3f}s")
        
        return response
    
    def handle_exception(self, e):
        """
        Handle exceptions.
        
        Args:
            e: The exception.
            
        Returns:
            The error response.
        """
        # Log the exception
        if isinstance(e, HTTPException):
            logger.warning(f"HTTP exception: {e}")
        else:
            logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
        
        # Let Flask handle HTTP exceptions
        if isinstance(e, HTTPException):
            return e
        
        # For other exceptions, return a generic error
        return "An unexpected error occurred", 500
