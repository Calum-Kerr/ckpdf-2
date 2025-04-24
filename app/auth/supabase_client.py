"""
Supabase client configuration.
This module provides a Supabase client for authentication and database operations.
"""

import os
import logging
from supabase import create_client, Client

# Configure logging
logger = logging.getLogger(__name__)

# Supabase configuration
SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', '')

# Initialize Supabase client
supabase: Client = None

def init_supabase():
    """
    Initialize the Supabase client.

    Returns:
        Client: The Supabase client.
    """
    global supabase

    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.warning("Supabase credentials not found. Authentication will not work.")
        return None

    if SUPABASE_URL == 'https://your-project-id.supabase.co':
        logger.warning("Using default Supabase URL. Authentication will be in demo mode.")
        return None

    try:
        # Create the Supabase client
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

        # Configure the auth client with the redirect URL
        # This ensures that the OAuth flow uses the correct redirect URL
        redirect_url = "http://127.0.0.1:5002/auth/oauth-callback"
        logger.info(f"Setting redirect URL for Supabase auth: {redirect_url}")

        logger.info("Supabase client initialized successfully.")
        return supabase
    except Exception as e:
        logger.error(f"Error initializing Supabase client: {str(e)}")
        return None

def get_supabase():
    """
    Get the Supabase client.

    Returns:
        Client: The Supabase client.
    """
    global supabase

    if supabase is None:
        return init_supabase()

    return supabase
