"""
RevisePDF Application Entry Point

This module serves as the entry point for the RevisePDF application.
It imports the Flask application instance and runs it when executed directly.
"""

from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
