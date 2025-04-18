"""
Optimize routes for the application.
This module contains routes for PDF optimization features.
"""

from flask import Blueprint

# Create blueprint
optimize_bp = Blueprint('optimize', __name__, url_prefix='/optimize')

# Import routes from the main routes.py file
# This is a temporary solution until we fully migrate all routes
from app.routes import optimize_routes
