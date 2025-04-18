"""
Routes package for the application.
This package contains all the route blueprints for the application.
"""

# Import the original routes.py file to make its blueprints available
from app.routes.main import main_bp
from app.routes.security_api import security_api_bp

# Export blueprints
__all__ = [
    'main_bp',
    'security_api_bp'
]
