"""
Convert from PDF routes for the application.
This module contains routes for converting PDF to various formats.
"""

from flask import Blueprint

# Create blueprint
convert_from_pdf_bp = Blueprint('convert_from_pdf', __name__, url_prefix='/convert-from-pdf')

# Import routes from the main routes.py file
# This is a temporary solution until we fully migrate all routes
from app.routes import convert_from_pdf_routes
