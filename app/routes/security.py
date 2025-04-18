"""
Security routes for the application.
This module contains routes for PDF security features.
"""

from flask import Blueprint

# Create blueprint
security_bp = Blueprint('security', __name__, url_prefix='/security')

# Import routes from the main routes.py file
# This is a temporary solution until we fully migrate all routes
from app.routes import security_routes
