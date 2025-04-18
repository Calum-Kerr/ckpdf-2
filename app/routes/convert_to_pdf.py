"""
Convert to PDF routes for the application.
This module contains routes for converting various formats to PDF.
"""

from flask import Blueprint

# Create blueprint
convert_to_pdf_bp = Blueprint('convert_to_pdf', __name__, url_prefix='/convert-to-pdf')

# Import routes from the main routes.py file
# This is a temporary solution until we fully migrate all routes
from app.routes import convert_to_pdf_routes
