"""
RevisePDF Application Runner

This script runs the RevisePDF application with debug mode enabled.
It's a convenience script for development purposes.
"""

from app import create_app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5002)
