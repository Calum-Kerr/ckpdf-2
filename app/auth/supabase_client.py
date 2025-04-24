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
        # Handle different versions of the Supabase client library
        try:
            # Try to create the client with the proxy parameter (newer versions)
            from flask import current_app
            site_url = current_app.config.get('SITE_URL', 'http://127.0.0.1:5002')
            redirect_url = f"{site_url}/auth/oauth-callback"
            logger.info(f"Setting redirect URL for Supabase auth: {redirect_url}")

            # First try with the proxy parameter (newer versions)
            try:
                supabase = create_client(SUPABASE_URL, SUPABASE_KEY, options={
                    'auth': {
                        'autoRefreshToken': True,
                        'persistSession': True,
                        'detectSessionInUrl': False
                    }
                })
                logger.info("Supabase client initialized successfully with newer API.")
            except TypeError as e:
                # If that fails, try without the proxy parameter (older versions)
                if "unexpected keyword argument 'proxy'" in str(e):
                    logger.info("Falling back to older Supabase client API without proxy parameter.")
                    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
                    logger.info("Supabase client initialized successfully with older API.")
                else:
                    raise e
        except Exception as inner_e:
            logger.warning(f"Error with advanced initialization: {str(inner_e)}. Falling back to basic initialization.")
            # Basic initialization as a last resort
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
