"""
Organize routes for the application.
This module contains routes for PDF organization features.
"""

from flask import Blueprint

# Create blueprint
organize_bp = Blueprint('organize', __name__, url_prefix='/organize')

# Import routes from the main routes.py file
# This is a temporary solution until we fully migrate all routes
from app.routes import organize_routes
