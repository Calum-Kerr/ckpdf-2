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
# Service role key for admin operations (should be kept secure)
SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_KEY', '')

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
        # Create the Supabase client with the simplest possible initialization
        # This should work with all versions of the Supabase client library
        from flask import current_app
        import os

        # Check if we're in production (Heroku)
        if os.environ.get('DYNO'):
            # We're on Heroku, use the production URL
            site_url = "https://www.revisepdf.com"
            logger.info(f"Running on Heroku, using production URL: {site_url}")
        else:
            # We're in development, use the local URL
            site_url = current_app.config.get('SITE_URL', 'http://127.0.0.1:5002')
            logger.info(f"Running locally, using development URL: {site_url}")

        redirect_url = f"{site_url}/auth/oauth-callback"
        logger.info(f"Setting redirect URL for Supabase auth: {redirect_url}")

        # Log Supabase configuration
        logger.info(f"Initializing Supabase client with URL: {SUPABASE_URL[:20]}... (truncated)")
        logger.info(f"Supabase key length: {len(SUPABASE_KEY)} characters")

        # Use the most basic initialization possible
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Supabase client initialized successfully with basic initialization.")

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

def get_service_supabase():
    """
    Get a Supabase client with service role permissions.
    This should only be used for server-side operations that require admin privileges.

    Returns:
        Client: The Supabase client with service role permissions.
    """
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        logger.warning("Supabase service role credentials not found. Admin operations will not work.")
        return None

    try:
        # Create a new Supabase client with the service role key
        service_supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        logger.info("Supabase service role client created successfully.")
        return service_supabase
    except Exception as e:
        logger.error(f"Error creating Supabase service role client: {str(e)}")
        return None
