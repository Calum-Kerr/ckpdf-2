"""
Authentication utilities.
This module provides utilities for authentication and user management.
"""

import logging
import json
import uuid
import datetime
from flask import session, request, redirect, url_for, flash, current_app
from functools import wraps
from .supabase_client import get_supabase

# Demo mode storage (for testing without Supabase)
demo_users = {}
demo_profiles = {}

# Configure logging
logger = logging.getLogger(__name__)

def login_user(email, password):
    """
    Log in a user with email and password.

    Args:
        email (str): The user's email.
        password (str): The user's password.

    Returns:
        dict: The user data if login is successful, None otherwise.
    """
    supabase = get_supabase()
    if not supabase:
        logger.warning("Supabase client not initialized. Using demo mode for login.")
        # Demo mode login
        if email in demo_users and demo_users[email]['password'] == password:
            user_id = demo_users[email]['id']
            session['user'] = {
                'id': user_id,
                'email': email,
                'access_token': 'demo-token',
                'refresh_token': 'demo-refresh-token'
            }
            logger.info(f"Demo user logged in: {email}")
            return {
                'id': user_id,
                'email': email
            }
        else:
            logger.warning(f"Demo login failed for: {email}")
            return None

    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        user = response.user
        session['user'] = {
            'id': user.id,
            'email': user.email,
            'access_token': response.session.access_token,
            'refresh_token': response.session.refresh_token
        }
        logger.info(f"User logged in: {email}")
        return user
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return None

def register_user(email, password):
    """
    Register a new user with email and password.

    Args:
        email (str): The user's email.
        password (str): The user's password.

    Returns:
        dict: The user data if registration is successful, None otherwise.
    """
    supabase = get_supabase()
    if not supabase:
        logger.warning("Supabase client not initialized. Using demo mode for registration.")
        # Demo mode registration
        if email in demo_users:
            logger.warning(f"Demo registration failed: Email already exists: {email}")
            return None

        # Create a demo user
        user_id = str(uuid.uuid4())
        demo_users[email] = {
            'id': user_id,
            'email': email,
            'password': password,
            'created_at': datetime.datetime.now().isoformat()
        }

        # Create a demo profile
        demo_profiles[user_id] = {
            'user_id': user_id,
            'email': email,
            'account_type': 'free',
            'storage_used': 0,
            'storage_limit': 50 * 1024 * 1024,  # 50MB for free users
            'created_at': datetime.datetime.now().isoformat()
        }

        logger.info(f"Demo user registered: {email}")
        return {
            'id': user_id,
            'email': email
        }

    try:
        # Sign up the user
        response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        user = response.user

        # Check if email confirmation is required
        if not response.session:
            # Email confirmation is required
            logger.info(f"User registered but email confirmation is required: {email}")
            flash("Registration successful! Please check your email to confirm your account before logging in.", "success")
            return user

        # If we get here, email confirmation is not required
        # Log in the user to get a session token
        login_response = response  # Use the session from sign_up

        # Store the session in Flask session
        session['user'] = {
            'id': user.id,
            'email': user.email,
            'access_token': login_response.session.access_token,
            'refresh_token': login_response.session.refresh_token
        }

        try:
            # Create user profile in the database
            # Now that we're authenticated, this should work with RLS
            supabase.table('user_profiles').insert({
                'user_id': user.id,
                'email': user.email,
                'account_type': 'free',
                'storage_used': 0,
                'storage_limit': 50 * 1024 * 1024  # 50MB for free users
            }).execute()

            logger.info(f"User profile created for: {email}")
        except Exception as profile_error:
            logger.error(f"Error creating user profile: {str(profile_error)}")
            # Continue anyway, as the user is created
            # We can create the profile later when they log in

        logger.info(f"User registered: {email}")
        return user
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return None

def logout_user():
    """
    Log out the current user.

    Returns:
        bool: True if logout is successful, False otherwise.
    """
    supabase = get_supabase()
    if not supabase:
        logger.warning("Supabase client not initialized. Using demo mode for logout.")
        # Demo mode logout
        if 'user' in session:
            session.pop('user', None)
            logger.info("Demo user logged out")
        return True

    try:
        if 'user' in session:
            # Just sign out without passing the token
            supabase.auth.sign_out()
            session.pop('user', None)
            logger.info("User logged out")
        return True
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        # Even if there's an error with Supabase, clear the session
        if 'user' in session:
            session.pop('user', None)
            logger.info("Session cleared despite Supabase error")
        return True

def get_current_user():
    """
    Get the current logged-in user.

    Returns:
        dict: The user data if a user is logged in, None otherwise.
    """
    if 'user' not in session:
        return None

    return session['user']

def login_required(f):
    """
    Decorator to require login for a route.

    Args:
        f: The function to decorate.

    Returns:
        function: The decorated function.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def get_file_size_limit(user_id=None):
    """
    Get the file size limit for a user.

    Args:
        user_id (str, optional): The user ID. Defaults to None.

    Returns:
        int: The file size limit in bytes.
    """
    # Default limits
    ANONYMOUS_LIMIT = 10 * 1024 * 1024  # 10MB
    FREE_USER_LIMIT = 10 * 1024 * 1024  # 10MB
    PREMIUM_USER_LIMIT = 100 * 1024 * 1024  # 100MB

    if user_id is None:
        # Default limit for anonymous users
        return ANONYMOUS_LIMIT

    supabase = get_supabase()
    if not supabase:
        logger.warning("Supabase client not initialized. Using demo mode for file size limits.")
        # Demo mode get file size limit
        if user_id in demo_profiles:
            profile = demo_profiles[user_id]
            account_type = profile.get('account_type', 'free')

            # Use the storage_limit from the profile if available
            if 'storage_limit' in profile:
                return profile.get('storage_limit')

            # Otherwise, use the default limit based on account type
            if account_type == 'premium':
                return PREMIUM_USER_LIMIT
            else:
                return FREE_USER_LIMIT
        else:
            # Default to premium in demo mode for testing
            return PREMIUM_USER_LIMIT

    try:
        response = supabase.table('user_profiles').select('account_type, storage_limit').eq('user_id', user_id).execute()

        if response.data and len(response.data) > 0:
            user_profile = response.data[0]
            account_type = user_profile.get('account_type', 'free')

            # Use the storage_limit from the database if available
            if 'storage_limit' in user_profile:
                return user_profile.get('storage_limit')

            # Otherwise, use the default limit based on account type
            if account_type == 'premium':
                return PREMIUM_USER_LIMIT
            else:
                return FREE_USER_LIMIT

        return FREE_USER_LIMIT  # Default to free user limit
    except Exception as e:
        logger.error(f"Error getting file size limit: {str(e)}")
        return FREE_USER_LIMIT  # Default to free user limit

def track_file_usage(user_id, file_size):
    """
    Track file usage for a user.

    Args:
        user_id (str): The user ID.
        file_size (int): The file size in bytes.

    Returns:
        bool: True if tracking is successful, False otherwise.
    """
    if user_id is None:
        return True  # No tracking for anonymous users

    supabase = get_supabase()
    if not supabase:
        logger.warning("Supabase client not initialized. Using demo mode for file usage tracking.")
        # Demo mode tracking
        if user_id in demo_profiles:
            current_usage = demo_profiles[user_id].get('storage_used', 0)
            new_usage = current_usage + file_size
            demo_profiles[user_id]['storage_used'] = new_usage
            logger.info(f"Demo mode: File usage tracked for user {user_id}: {file_size} bytes")
            return True
        else:
            logger.warning(f"Demo mode: User profile not found for user {user_id}")
            return False

    try:
        # Update user profile with new storage used
        response = supabase.table('user_profiles').select('storage_used').eq('user_id', user_id).execute()

        if response.data and len(response.data) > 0:
            current_usage = response.data[0].get('storage_used', 0)
            new_usage = current_usage + file_size

            supabase.table('user_profiles').update({'storage_used': new_usage}).eq('user_id', user_id).execute()

            # Add usage record
            supabase.table('usage_tracking').insert({
                'user_id': user_id,
                'file_size': file_size,
                'operation_type': 'upload'
            }).execute()

            logger.info(f"File usage tracked for user {user_id}: {file_size} bytes")
            return True
        else:
            # User profile not found, create one
            try:
                supabase.table('user_profiles').insert({
                    'user_id': user_id,
                    'email': 'unknown@example.com',  # Will be updated later
                    'account_type': 'free',
                    'storage_used': file_size,
                    'storage_limit': 10 * 1024 * 1024  # 10MB for free users
                }).execute()

                # Add usage record
                supabase.table('usage_tracking').insert({
                    'user_id': user_id,
                    'file_size': file_size,
                    'operation_type': 'upload'
                }).execute()

                logger.info(f"Created new user profile and tracked file usage for user {user_id}: {file_size} bytes")
                return True
            except Exception as e:
                logger.error(f"Error creating user profile: {str(e)}")
                return False
    except Exception as e:
        logger.error(f"Error tracking file usage: {str(e)}")
        return False

def check_file_size_limit(file_size, user_id=None):
    """
    Check if a file size is within the user's limit.

    Args:
        file_size (int): The file size in bytes.
        user_id (str, optional): The user ID. Defaults to None.

    Returns:
        bool: True if the file size is within the limit, False otherwise.
    """
    limit = get_file_size_limit(user_id)
    return file_size <= limit

def get_user_profile(user_id):
    """
    Get a user's profile.

    Args:
        user_id (str): The user ID.

    Returns:
        dict: The user profile if found, None otherwise.
    """
    if user_id is None:
        return None

    supabase = get_supabase()
    if not supabase:
        logger.warning("Supabase client not initialized. Using demo mode for user profile.")
        # Demo mode get profile
        if user_id in demo_profiles:
            return demo_profiles[user_id]
        return None

    try:
        response = supabase.table('user_profiles').select('*').eq('user_id', user_id).execute()

        if response.data and len(response.data) > 0:
            profile = response.data[0]
            logger.info(f"Retrieved user profile: {profile}")

            # Ensure profile has created_at field
            if 'created_at' not in profile or not profile['created_at']:
                now = datetime.datetime.now().isoformat()
                profile['created_at'] = now
                logger.info(f"Added missing created_at field to profile: {profile}")

                # Update the profile in the database
                try:
                    supabase.table('user_profiles').update({'created_at': now}).eq('user_id', user_id).execute()
                    logger.info(f"Updated profile in database with created_at field")
                except Exception as update_error:
                    logger.error(f"Error updating profile with created_at field: {str(update_error)}")

            return profile

        # Profile doesn't exist, try to create one
        logger.info(f"User profile not found for user {user_id}, attempting to create one")
        return create_user_profile(user_id)
    except Exception as e:
        logger.error(f"Error getting user profile: {str(e)}")
        return None

def create_user_profile(user_id):
    """
    Create a user profile if it doesn't exist.

    Args:
        user_id (str): The user ID.

    Returns:
        dict: The created user profile if successful, None otherwise.
    """
    if user_id is None:
        return None

    supabase = get_supabase()
    if not supabase:
        logger.warning("Supabase client not initialized. Using demo mode for profile creation.")
        # Demo mode create profile
        if user_id not in demo_profiles:
            # Get user email from session
            user_email = session.get('user', {}).get('email', 'unknown@example.com')
            demo_profiles[user_id] = {
                'user_id': user_id,
                'email': user_email,
                'account_type': 'free',
                'storage_used': 0,
                'storage_limit': 50 * 1024 * 1024,  # 50MB for free users
                'created_at': datetime.datetime.now().isoformat()
            }
            logger.info(f"Created demo user profile for user {user_id}")
        return demo_profiles[user_id]

    try:
        # Get user email from session
        user_email = session.get('user', {}).get('email', 'unknown@example.com')

        # Create user profile
        now = datetime.datetime.now().isoformat()
        response = supabase.table('user_profiles').insert({
            'user_id': user_id,
            'email': user_email,
            'account_type': 'free',
            'storage_used': 0,
            'storage_limit': 50 * 1024 * 1024,  # 50MB for free users
            'created_at': now,
            'updated_at': now
        }).execute()

        if response.data and len(response.data) > 0:
            logger.info(f"Created user profile for user {user_id}")
            return response.data[0]

        logger.warning(f"Failed to create user profile for user {user_id}")
        return None
    except Exception as e:
        logger.error(f"Error creating user profile: {str(e)}")
        return None
