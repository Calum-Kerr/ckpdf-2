"""
Test script for Supabase connection and user creation.
"""

import os
from dotenv import load_dotenv
from supabase import create_client
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', '')
# For service role operations, we need the service role key
# This should be loaded from environment variables, never hardcoded
SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_KEY', '')

print(f"SUPABASE_URL: {SUPABASE_URL}")
print(f"SUPABASE_KEY: {SUPABASE_KEY[:10]}...")
print(f"Using service role key for admin operations")

try:
    # Create the Supabase client
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("Supabase client created successfully")

    # Try to get the user count
    try:
        response = supabase.table('user_profiles').select('*').execute()
        print(f"User profiles count: {len(response.data)}")
        print(f"User profiles data: {response.data}")
    except Exception as e:
        print(f"Error querying user_profiles: {str(e)}")

    # Try to create a test user
    try:
        test_email = "test.user@gmail.com"
        test_password = "Test123456!"

        # Check if user already exists
        try:
            # Try to sign in with the test user credentials
            supabase.auth.sign_in_with_password({"email": test_email, "password": test_password})
            print(f"Test user {test_email} already exists")
        except Exception:
            # User doesn't exist, create a new one
            print(f"Creating test user {test_email}")
            response = supabase.auth.sign_up({
                "email": test_email,
                "password": test_password
            })
            print(f"User creation response: {response}")

            # Check if user was created
            if hasattr(response, 'user') and response.user:
                print(f"Test user created with ID: {response.user.id}")

                # Try to create a user profile using the service role key
                try:
                    # Create a new Supabase client with the service role key
                    service_supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
                    print("Created service role Supabase client for admin operations")

                    profile_response = service_supabase.table('user_profiles').insert({
                        'user_id': response.user.id,
                        'email': test_email,
                        'account_type': 'free',
                        'storage_used': 0,
                        'storage_limit': 50 * 1024 * 1024  # 50MB
                    }).execute()

                    print(f"User profile creation response: {profile_response}")
                except Exception as profile_error:
                    print(f"Error creating user profile: {str(profile_error)}")
            else:
                print("Failed to create test user")
    except Exception as e:
        print(f"Error creating test user: {str(e)}")

except Exception as e:
    print(f"Error creating Supabase client: {str(e)}")
