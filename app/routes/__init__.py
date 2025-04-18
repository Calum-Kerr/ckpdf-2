"""
Routes package for the application.
This package contains all the route blueprints for the application.
"""

# Re-export blueprints from the original routes.py file
from app.routes.main import main_bp
from app.routes.security_api import security_api_bp
from app.routes import optimize_bp, convert_to_pdf_bp, edit_bp, organize_bp, convert_from_pdf_bp, security_bp

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
