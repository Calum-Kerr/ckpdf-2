"""
RevisePDF Application Runner

This script runs the RevisePDF application with debug mode enabled.
It's a convenience script for development purposes.
"""

import os
from dotenv import load_dotenv
from app import create_app

# Load environment variables from .env file
load_dotenv()

if __name__ == '__main__':
    # Print environment variables for debugging
    print(f"SUPABASE_URL: {os.environ.get('SUPABASE_URL', 'Not set')}")
    print(f"GOOGLE_CLIENT_ID: {os.environ.get('GOOGLE_CLIENT_ID', 'Not set')}")

    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5002)
