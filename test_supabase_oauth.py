"""
Test script for Supabase OAuth configuration.
"""

import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables from .env file
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', '')

print(f"SUPABASE_URL: {SUPABASE_URL}")
print(f"SUPABASE_KEY: {SUPABASE_KEY[:10]}...")

# Create the Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Get the OAuth URL
redirect_url = "http://127.0.0.1:5002/auth/oauth-callback"

# Check if the method exists
print(f"Available methods: {dir(supabase.auth)}")

# Try to get the OAuth URL using the sign_in_with_oauth method
try:
    oauth_data = {
        'provider': 'google',
        'redirect_to': redirect_url
    }
    oauth_url = supabase.auth.sign_in_with_oauth(oauth_data)
    print(f"OAuth URL from sign_in_with_oauth: {oauth_url}")
except Exception as e:
    print(f"Error getting OAuth URL: {str(e)}")
    oauth_url = None

if oauth_url:
    print(f"OAuth URL: {oauth_url}")
