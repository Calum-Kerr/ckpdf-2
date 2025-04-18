"""
Routes package for the application.
This package contains all the route blueprints for the application.
"""

from flask import Blueprint

# Import blueprints
from app.routes.main import main_bp
from app.routes.optimize import optimize_bp
from app.routes.convert_to_pdf import convert_to_pdf_bp
from app.routes.edit import edit_bp
from app.routes.organize import organize_bp
from app.routes.convert_from_pdf import convert_from_pdf_bp
from app.routes.security import security_bp
from app.routes.security_api import security_api_bp

# Export blueprints
__all__ = [
    'main_bp',
    'optimize_bp',
    'convert_to_pdf_bp',
    'edit_bp',
    'organize_bp',
    'convert_from_pdf_bp',
    'security_bp',
    'security_api_bp'
]
