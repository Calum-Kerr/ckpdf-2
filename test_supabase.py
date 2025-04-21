"""
Test Supabase connection.
This script tests the connection to Supabase and verifies that the credentials are working.
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client

def test_supabase_connection():
    """
    Test the connection to Supabase.
    
    Returns:
        bool: True if the connection is successful, False otherwise.
    """
    # Load environment variables
    load_dotenv()
    
    # Get Supabase credentials
    supabase_url = os.environ.get('SUPABASE_URL')
    supabase_key = os.environ.get('SUPABASE_KEY')
    
    # Check if credentials are set
    if not supabase_url or not supabase_key:
        print("Error: Supabase credentials not found in .env file.")
        print("Please set SUPABASE_URL and SUPABASE_KEY in your .env file.")
        return False
    
    # Check if credentials are default values
    if supabase_url == 'your_project_url_here' or supabase_key == 'your_anon_key_here':
        print("Error: Supabase credentials are still set to default values.")
        print("Please update SUPABASE_URL and SUPABASE_KEY in your .env file with your actual credentials.")
        return False
    
    try:
        # Initialize Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)
        
        # Test authentication by getting the current user (should be None since we're not authenticated)
        response = supabase.auth.get_user()
        
        print("Supabase connection successful!")
        print(f"Supabase URL: {supabase_url}")
        print("Supabase API Key: [REDACTED]")
        return True
    except Exception as e:
        print(f"Error connecting to Supabase: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_supabase_connection()
    sys.exit(0 if success else 1)
