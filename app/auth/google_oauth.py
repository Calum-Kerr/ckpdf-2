"""
Google OAuth integration for RevisePDF.
This module provides direct Google OAuth authentication without using Supabase.
"""

import os
import logging
import requests
import json
import datetime
from flask import current_app, session, redirect, url_for, request, flash
from urllib.parse import urlencode
import uuid

# Configure logging
logger = logging.getLogger(__name__)

def get_google_auth_url():
    """
    Get the Google OAuth authorization URL.
    
    Returns:
        str: The Google OAuth authorization URL.
    """
    # Get Google OAuth configuration
    client_id = current_app.config.get('GOOGLE_CLIENT_ID')
    
    # Determine the redirect URI based on environment
    if os.environ.get('DYNO'):
        # We're on Heroku, use the production URL
        site_url = "https://www.revisepdf.com"
        logger.info(f"Running on Heroku, using production URL: {site_url}")
    else:
        # We're in development, use the local URL
        site_url = current_app.config.get('SITE_URL', 'http://127.0.0.1:5002')
        logger.info(f"Running locally, using development URL: {site_url}")
    
    redirect_uri = f"{site_url}/auth/google-callback"
    logger.info(f"Using redirect URI: {redirect_uri}")
    
    # Generate a state parameter to prevent CSRF
    state = str(uuid.uuid4())
    session['google_oauth_state'] = state
    
    # Build the authorization URL
    auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': 'email profile',
        'state': state,
        'prompt': 'select_account'
    }
    
    return f"{auth_url}?{urlencode(params)}"

def exchange_code_for_token(code):
    """
    Exchange the authorization code for an access token.
    
    Args:
        code (str): The authorization code from Google.
        
    Returns:
        dict: The token response from Google, or None if there was an error.
    """
    # Get Google OAuth configuration
    client_id = current_app.config.get('GOOGLE_CLIENT_ID')
    client_secret = current_app.config.get('GOOGLE_CLIENT_SECRET')
    
    # Determine the redirect URI based on environment
    if os.environ.get('DYNO'):
        # We're on Heroku, use the production URL
        site_url = "https://www.revisepdf.com"
    else:
        # We're in development, use the local URL
        site_url = current_app.config.get('SITE_URL', 'http://127.0.0.1:5002')
    
    redirect_uri = f"{site_url}/auth/google-callback"
    
    # Exchange the code for a token
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'code': code,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code'
    }
    
    try:
        response = requests.post(token_url, data=data)
        response.raise_for_status()  # Raise an exception for 4XX/5XX responses
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error exchanging code for token: {str(e)}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"Response status: {e.response.status_code}")
            logger.error(f"Response body: {e.response.text}")
        return None

def get_user_info(access_token):
    """
    Get the user's information from Google.
    
    Args:
        access_token (str): The access token from Google.
        
    Returns:
        dict: The user information from Google, or None if there was an error.
    """
    try:
        response = requests.get(
            'https://www.googleapis.com/oauth2/v3/userinfo',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        response.raise_for_status()  # Raise an exception for 4XX/5XX responses
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error getting user info: {str(e)}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"Response status: {e.response.status_code}")
            logger.error(f"Response body: {e.response.text}")
        return None

def create_user_session(user_info, token_info):
    """
    Create a user session from Google user information.
    
    Args:
        user_info (dict): The user information from Google.
        token_info (dict): The token information from Google.
        
    Returns:
        dict: The user session data.
    """
    # Create a unique user ID based on the Google sub (subject) ID
    user_id = f"google-{user_info.get('sub')}"
    
    # Create the user session
    user_session = {
        'id': user_id,
        'email': user_info.get('email'),
        'name': user_info.get('name'),
        'picture': user_info.get('picture'),
        'access_token': token_info.get('access_token'),
        'refresh_token': token_info.get('refresh_token'),
        'expires_in': token_info.get('expires_in'),
        'token_type': token_info.get('token_type'),
        'is_google_user': True,
        'provider': 'google',
        'login_time': datetime.datetime.now().isoformat()
    }
    
    return user_session
