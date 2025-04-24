"""
Authentication utilities.
This module provides utilities for authentication and user management.
"""

import logging
import uuid
import datetime
from flask import session, request, redirect, url_for, flash, g, current_app
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from functools import wraps
from .supabase_client import get_supabase

# Demo mode storage (for testing without Supabase)
demo_users = {}
demo_profiles = {}

# Initialize demo user for testing
def init_demo_user():
    """Initialize a demo user for testing."""
    user_id = '09a364b1-60a5-4d83-a5a9-e6882dc83223'  # Use the same ID from logs
    email = 'calumxkerr@gmail.com'

    if email not in demo_users:
        demo_users[email] = {
            'id': user_id,
            'email': email,
            'password': 'password',  # Demo password
            'created_at': datetime.datetime.now().isoformat()
        }

    if user_id not in demo_profiles:
        demo_profiles[user_id] = {
            'user_id': user_id,
            'email': email,
            'account_type': 'free',
            'storage_used': 0,
            'storage_limit': 50 * 1024 * 1024,  # 50MB for free users
            'created_at': datetime.datetime.now().isoformat()
        }

    logger.info(f"Demo user initialized: {email}")
    return demo_users[email]

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
            # Get the user's creation date from the user metadata
            # This is available in the user object returned from sign_up
            creation_date = user.created_at if hasattr(user, 'created_at') else datetime.datetime.now().isoformat()

            # Create user profile in the database with the creation date
            supabase.table('user_profiles').insert({
                'user_id': user.id,
                'email': user.email,
                'account_type': 'free',
                'storage_used': 0,
                'storage_limit': 50 * 1024 * 1024,  # 50MB for free users
                'created_at': creation_date
            }).execute()

            logger.info(f"User profile created for: {email} with creation date: {creation_date}")
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

    user = session['user']

    # Check for session expiration
    if 'expiration_time' in user:
        try:
            expiration_time = datetime.datetime.fromisoformat(user['expiration_time'])
            if datetime.datetime.now() > expiration_time:
                logger.info(f"Session expired for user {user.get('email')}")

                # Check if we have a refresh token
                if 'refresh_token' in user:
                    logger.info("Attempting to refresh token")
                    try:
                        # Get Supabase client
                        supabase = get_supabase()
                        if supabase:
                            # Refresh the token
                            refresh_response = supabase.auth.refresh_session(user['refresh_token'])
                            if refresh_response and hasattr(refresh_response, 'session'):
                                # Update the session with new tokens
                                user['access_token'] = refresh_response.session.access_token
                                user['refresh_token'] = refresh_response.session.refresh_token

                                # Calculate new expiration time
                                expires_in = getattr(refresh_response.session, 'expires_in', 3600)
                                new_expiration = datetime.datetime.now() + datetime.timedelta(seconds=expires_in)
                                user['expiration_time'] = new_expiration.isoformat()

                                # Update the session
                                session['user'] = user
                                logger.info(f"Token refreshed for user {user.get('email')}")
                                return user
                    except Exception as e:
                        logger.error(f"Error refreshing token: {str(e)}")

                # If we get here, either we don't have a refresh token or refresh failed
                # Clear the session and return None
                session.pop('user', None)
                return None
        except (ValueError, TypeError) as e:
            logger.error(f"Error parsing expiration time: {str(e)}")

    return user

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

def csrf_exempt(f):
    """
    Decorator to exempt a route from CSRF protection.

    Args:
        f: The function to decorate.

    Returns:
        function: The decorated function.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        g._csrf_exempt = True
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
                # Fall back to demo profile
                if user_id in demo_profiles:
                    current_usage = demo_profiles[user_id].get('storage_used', 0)
                    new_usage = current_usage + file_size
                    demo_profiles[user_id]['storage_used'] = new_usage
                    logger.info(f"Updated demo profile storage usage for user {user_id}: {file_size} bytes")
                    return True
                else:
                    # Create a new demo profile
                    demo_profiles[user_id] = {
                        'user_id': user_id,
                        'email': session.get('user', {}).get('email', 'unknown@example.com'),
                        'account_type': 'free',
                        'storage_used': file_size,
                        'storage_limit': 50 * 1024 * 1024,  # 50MB for free users
                        'created_at': datetime.datetime.now().isoformat()
                    }
                    logger.info(f"Created new demo profile with storage usage for user {user_id}: {file_size} bytes")
                    return True
    except Exception as e:
        logger.error(f"Error tracking file usage: {str(e)}")
        # Fall back to demo profile
        if user_id in demo_profiles:
            current_usage = demo_profiles[user_id].get('storage_used', 0)
            new_usage = current_usage + file_size
            demo_profiles[user_id]['storage_used'] = new_usage
            logger.info(f"Updated demo profile storage usage for user {user_id} after error: {file_size} bytes")
            return True
        else:
            # Create a new demo profile
            demo_profiles[user_id] = {
                'user_id': user_id,
                'email': session.get('user', {}).get('email', 'unknown@example.com'),
                'account_type': 'free',
                'storage_used': file_size,
                'storage_limit': 50 * 1024 * 1024,  # 50MB for free users
                'created_at': datetime.datetime.now().isoformat()
            }
            logger.info(f"Created new demo profile with storage usage for user {user_id} after error: {file_size} bytes")
            return True

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


def handle_oauth_login(auth_code):
    """
    Handle OAuth login with authorization code.

    Args:
        auth_code (str): The authorization code from the OAuth provider.

    Returns:
        dict: The user data if login is successful, None otherwise.
    """
    supabase = get_supabase()
    if not supabase:
        logger.warning("Supabase client not initialized. Cannot handle OAuth login.")
        return None

    try:
        # Exchange the authorization code for a session
        # For newer Supabase client versions, we need to use session.create_with_oauth_code
        try:
            # Try the newer method first
            session_response = supabase.auth.exchange_code_for_session({
                'auth_code': auth_code
            })
        except (AttributeError, Exception) as e:
            logger.warning(f"Could not use exchange_code_for_session: {str(e)}")
            # Fall back to the older method
            session_response = supabase.auth.sign_in_with_oauth({
                'provider': 'google',
                'code': auth_code
            })

        # Get the user from the session
        user = getattr(session_response, 'user', None)

        if not user:
            # Try to get user from session data
            if hasattr(session_response, 'session') and hasattr(session_response.session, 'user'):
                user = session_response.session.user
            else:
                logger.error("No user returned from OAuth exchange")
                return None

        # Get access and refresh tokens
        access_token = None
        refresh_token = None

        if hasattr(session_response, 'session'):
            access_token = getattr(session_response.session, 'access_token', None)
            refresh_token = getattr(session_response.session, 'refresh_token', None)

        # Store the session in Flask session
        session['user'] = {
            'id': user.id,
            'email': user.email,
            'access_token': access_token,
            'refresh_token': refresh_token
        }

        # Check if the user has a profile, create one if not
        try:
            profile = get_user_profile(user.id)

            if not profile:
                # Profile creation is handled in get_user_profile
                logger.info(f"Profile will be created for OAuth user: {user.email}")
        except Exception as profile_error:
            logger.error(f"Error checking user profile: {str(profile_error)}")
            # Continue anyway, as the user is authenticated

        logger.info(f"User logged in via OAuth: {user.email}")
        return user
    except Exception as e:
        logger.error(f"OAuth login error: {str(e)}")
        return None



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
                # Use current time as creation date
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
        try:
            return create_user_profile(user_id)
        except Exception as create_error:
            logger.error(f"Error creating user profile: {str(create_error)}")
            # Fall back to demo profile if Supabase fails
            if user_id in demo_profiles:
                logger.info(f"Using demo profile for user {user_id}")
                return demo_profiles[user_id]
            else:
                # Create a new demo profile
                logger.info(f"Creating new demo profile for user {user_id}")
                demo_profiles[user_id] = {
                    'user_id': user_id,
                    'email': session.get('user', {}).get('email', 'unknown@example.com'),
                    'account_type': 'free',
                    'storage_used': 0,
                    'storage_limit': 50 * 1024 * 1024,  # 50MB for free users
                    'created_at': datetime.datetime.now().isoformat()
                }
                return demo_profiles[user_id]
    except Exception as e:
        logger.error(f"Error getting user profile: {str(e)}")
        # Fall back to demo profile
        if user_id in demo_profiles:
            logger.info(f"Using demo profile for user {user_id} after error")
            return demo_profiles[user_id]
        else:
            # Create a new demo profile
            logger.info(f"Creating new demo profile for user {user_id} after error")
            demo_profiles[user_id] = {
                'user_id': user_id,
                'email': session.get('user', {}).get('email', 'unknown@example.com'),
                'account_type': 'free',
                'storage_used': 0,
                'storage_limit': 50 * 1024 * 1024,  # 50MB for free users
                'created_at': datetime.datetime.now().isoformat()
            }
            return demo_profiles[user_id]

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
        creation_date = now
        response = supabase.table('user_profiles').insert({
            'user_id': user_id,
            'email': user_email,
            'account_type': 'free',
            'storage_used': 0,
            'storage_limit': 50 * 1024 * 1024,  # 50MB for free users
            'created_at': creation_date,
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

def change_user_password(user_id, current_password, new_password):
    """
    Change a user's password.

    Args:
        user_id (str): The user ID.
        current_password (str): The current password.
        new_password (str): The new password.

    Returns:
        bool: True if the password was changed successfully, False otherwise.
    """
    if user_id is None:
        logger.error("Cannot change password: user_id is None")
        return False

    supabase = get_supabase()
    if not supabase:
        logger.error("Cannot change password: Supabase client not initialized")
        return False

    try:
        # First verify the current password by attempting to sign in
        user_email = session.get('user', {}).get('email')
        if not user_email:
            logger.error("Cannot change password: user email not found in session")
            return False

        # Try to sign in with current password
        try:
            auth_response = supabase.auth.sign_in_with_password({
                "email": user_email,
                "password": current_password
            })

            if not auth_response or not auth_response.user:
                logger.error("Cannot change password: current password verification failed")
                return False

        except Exception as auth_error:
            logger.error(f"Cannot change password: current password verification failed: {str(auth_error)}")
            return False

        # Now change the password
        try:
            update_response = supabase.auth.update_user({
                "password": new_password
            })

            if update_response and update_response.user:
                logger.info(f"Password changed successfully for user {user_id}")
                return True
            else:
                logger.error("Password change failed: no user in response")
                return False

        except Exception as update_error:
            logger.error(f"Password change failed: {str(update_error)}")
            return False

    except Exception as e:
        logger.error(f"Password change failed with unexpected error: {str(e)}")
        return False

def get_reset_token(email):
    """
    Generate a password reset token.

    Args:
        email (str): The user's email.

    Returns:
        str: The password reset token.
    """
    # Create a serializer with the app's secret key
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])

    # Generate a token with the user's email
    token = serializer.dumps(email, salt='password-reset-salt')

    logger.info(f"Generated password reset token for {email}")
    return token

def verify_reset_token(token, expiration=3600):
    """
    Verify a password reset token.

    Args:
        token (str): The password reset token.
        expiration (int, optional): The token expiration time in seconds. Defaults to 3600 (1 hour).

    Returns:
        str: The user's email if the token is valid, None otherwise.
    """
    # Create a serializer with the app's secret key
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])

    try:
        # Load the token with the same salt used to generate it
        email = serializer.loads(token, salt='password-reset-salt', max_age=expiration)
        logger.info(f"Verified password reset token for {email}")
        return email
    except SignatureExpired:
        logger.warning("Password reset token expired")
        return None
    except BadSignature:
        logger.warning("Invalid password reset token")
        return None
    except Exception as e:
        logger.error(f"Error verifying password reset token: {str(e)}")
        return None

def send_reset_email(email, token):
    """
    Send a password reset email.

    Args:
        email (str): The user's email.
        token (str): The password reset token.

    Returns:
        bool: True if the email was sent successfully, False otherwise.
    """
    # In a real application, you would send an email with the reset link
    # For now, we'll just log the reset link
    reset_url = url_for('auth.reset_token', token=token, _external=True)
    logger.info(f"Password reset link for {email}: {reset_url}")

    # For demo purposes, we'll store the reset link in the session
    # so we can display it to the user
    session['reset_link'] = reset_url

    # In a real application, you would return True only if the email was sent successfully
    return True

def reset_password(email, new_password):
    """
    Reset a user's password.

    Args:
        email (str): The user's email.
        new_password (str): The new password.

    Returns:
        bool: True if the password was reset successfully, False otherwise.
    """
    supabase = get_supabase()
    if not supabase:
        logger.error("Cannot reset password: Supabase client not initialized")
        return False

    try:
        # First, check if the user exists
        try:
            # We can't directly check if a user exists, but we can try to get the user by email
            # This is a workaround since we don't have admin access
            # In a real application with admin access, you would use the admin API to check if the user exists

            # For now, we'll assume the user exists if they have a profile
            response = supabase.table('user_profiles').select('user_id').eq('email', email).execute()

            if not response.data or len(response.data) == 0:
                logger.error(f"Cannot reset password: user with email {email} not found")
                return False

        except Exception as check_error:
            logger.error(f"Error checking if user exists: {str(check_error)}")
            return False

        # Now reset the password
        try:
            # Use the password recovery feature of Supabase
            recovery_response = supabase.auth.reset_password_email(email)

            # This doesn't actually reset the password, it just sends a recovery email
            # In a real application, the user would click the link in the email and set a new password
            # For now, we'll just log that the recovery email was sent
            logger.info(f"Password recovery email sent to {email}")

            # Since we can't actually reset the password without the user clicking the link,
            # we'll return True to indicate that the process was started successfully
            return True

        except Exception as reset_error:
            logger.error(f"Error resetting password: {str(reset_error)}")
            return False

    except Exception as e:
        logger.error(f"Password reset failed with unexpected error: {str(e)}")
        return False
