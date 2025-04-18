"""
Edit routes for the application.
This module contains routes for PDF editing features.
"""

from flask import Blueprint

# Create blueprint
edit_bp = Blueprint('edit', __name__, url_prefix='/edit')

# Import routes from the main routes.py file
# This is a temporary solution until we fully migrate all routes
from app.routes import edit_routes
