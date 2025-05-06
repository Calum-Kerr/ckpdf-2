"""
Authentication routes for the application.
This module contains routes for authentication features.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app, jsonify
import logging
import datetime
import urllib.parse
import os
import base64
import json
import jwt

# Configure logging
logger = logging.getLogger(__name__)
from .utils import (
    login_user, register_user, logout_user, get_current_user, login_required,
    get_user_profile, demo_profiles, csrf_exempt, change_user_password,
    get_reset_token, verify_reset_token, send_reset_email, reset_password,
    create_user_profile
)
from app.forms import LoginForm, RegisterForm
from .forms import ChangePasswordForm, RequestPasswordResetForm, ResetPasswordForm
from .supabase_client import get_supabase

# Create blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handle user login.

    Returns:
        The rendered login page or a redirect.
    """
    # If user is already logged in, redirect to dashboard
    if 'user' in session:
        return redirect(url_for('auth.dashboard'))

    form = LoginForm()

    if request.method == 'POST':
        logger.info(f"Login form submitted: {form.email.data}")

        if form.validate_on_submit():
            email = form.email.data
            password = form.password.data

            user = login_user(email, password)

            if user:
                next_page = request.args.get('next')
                if next_page:
                    return redirect(next_page)
                return redirect(url_for('auth.dashboard'))
            else:
                flash('Invalid email or password. Please try again.', 'danger')
        else:
            logger.warning(f"Form validation failed: {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"{field}: {error}", 'danger')

    return render_template('auth/login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    Handle user registration.

    Returns:
        The rendered registration page or a redirect.
    """
    # If user is already logged in, redirect to dashboard
    if 'user' in session:
        return redirect(url_for('auth.dashboard'))

    form = RegisterForm()

    if request.method == 'POST':
        logger.info(f"Registration form submitted: {form.email.data}")

        if form.validate_on_submit():
            email = form.email.data
            password = form.password.data

            user = register_user(email, password)

            if user:
                # The flash message is now handled in the register_user function
                # to provide more specific information about email verification
                return redirect(url_for('auth.login'))
            else:
                flash('Registration failed. Please try again.', 'danger')
        else:
            logger.warning(f"Form validation failed: {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"{field}: {error}", 'danger')

    return render_template('auth/register.html', form=form)

@auth_bp.route('/logout')
def logout():
    """
    Handle user logout.

    Returns:
        A redirect to the home page.
    """
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('/dashboard')
def dashboard():
    """
    Display the user dashboard.

    Returns:
        The rendered dashboard page.
    """
    # Check if the user is logged in via session
    user = get_current_user()

    # If not logged in via session, check for access token in query parameters
    if not user:
        logger.info("User not logged in via session, checking for token in query parameters")
        access_token = request.args.get('access_token')

        if access_token:
            logger.info(f"Access token found in query parameters: {access_token[:10]}... (truncated)")

            # Handle test token for development/testing
            if access_token == 'test_token':
                logger.info("Using test token for development")
                # Create a test user session
                session['user'] = {
                    'id': 'test-user-id',
                    'email': 'test@example.com',
                    'access_token': 'test_token',
                    'is_test_user': True
                }
                flash("Logged in with test account", "success")
                # Update user for the rest of the function
                user = get_current_user()
            else:
                try:
                    # Get the Supabase client
                    supabase = get_supabase()
                    if supabase:
                        # Get user data from token
                        user_response = supabase.auth.get_user(access_token)
                        if user_response and hasattr(user_response, 'user'):
                            user_data = user_response.user

                            # Store in session
                            session['user'] = {
                                'id': user_data.id,
                                'email': user_data.email,
                                'access_token': access_token
                            }

                            # Update user for the rest of the function
                            user = get_current_user()
                            logger.info(f"Successfully authenticated user with token: {user_data.email}")
                            flash("You have successfully logged in!", "success")
                except Exception as e:
                    logger.error(f"Error authenticating with token: {str(e)}")

    # If still not logged in, redirect to login page
    if not user:
        logger.warning("User not logged in and no valid token found")
        flash("Please log in to access your dashboard", "warning")
        return redirect(url_for('auth.login'))

    # Handle test user or Google user
    if user.get('is_test_user', False) or user.get('is_google_user', False):
        # For test users or Google users, use dummy profile data
        profile = {
            'user_id': user['id'],
            'email': user['email'],
            'account_type': 'free',
            'storage_used': 0,
            'storage_limit': 100 * 1024 * 1024,  # 100MB for test/Google users
            'created_at': datetime.datetime.now().isoformat()
        }
        if user.get('is_test_user', False):
            logger.info(f"Using test profile for test user")
        else:
            logger.info(f"Using test profile for Google user")
    else:
        # Try to get profile from Supabase
        profile = get_user_profile(user['id']) if user else None

        # If Supabase fails, use demo profile or create one
        if not profile and user:
            if user['id'] in demo_profiles:
                profile = demo_profiles[user['id']]
                logger.info(f"Using existing demo profile for user {user['id']}")
            else:
                # Create a new demo profile
                creation_date = datetime.datetime.now().isoformat()

                demo_profiles[user['id']] = {
                    'user_id': user['id'],
                    'email': user.get('email', 'unknown@example.com'),
                    'account_type': 'free',
                    'storage_used': 0,
                    'storage_limit': 50 * 1024 * 1024,  # 50MB for free users
                    'created_at': creation_date
                }
                profile = demo_profiles[user['id']]
                logger.info(f"Created new demo profile for user {user['id']}")

    return render_template('auth/account.html', user=user, profile=profile)

@auth_bp.route('/profile')
@login_required
def profile():
    """
    Redirect to the dashboard.

    Returns:
        Redirect to the dashboard page.
    """
    return redirect(url_for('auth.dashboard'))


@auth_bp.route('/google-login')
@csrf_exempt
def google_login():
    """
    Initiate direct Google OAuth login.

    Returns:
        Redirect to Google OAuth login page.
    """
    # Check if we're already authenticated
    if 'user' in session:
        logger.info(f"User already authenticated: {session['user'].get('email')}")
        return redirect(url_for('auth.dashboard'))

    try:
        # Import the Google OAuth module
        from .google_oauth import get_google_auth_url

        # Get the Google OAuth URL
        auth_url = get_google_auth_url()

        # Log the Google OAuth URL
        logger.info(f"Got Google OAuth URL: {auth_url[:100]}... (truncated)")

        # Redirect to the Google OAuth URL
        logger.info("Redirecting to Google OAuth URL")
        return redirect(auth_url)
    except Exception as e:
        logger.error(f"Error initiating Google OAuth: {str(e)}")
        flash("An error occurred while trying to log in with Google. Please try again or use email and password.", "danger")
        return redirect(url_for('auth.login'))


# Add a special route to handle the Google OAuth callback
@auth_bp.route('/google-callback')
@auth_bp.route('/auth/google-callback')
@csrf_exempt
def google_callback():
    """
    Handle Google OAuth callback.
    This route processes the response from Google's OAuth service.
    """
    logger.info("Received Google callback")
    logger.info(f"Query parameters: {request.args}")

    # Check for error
    error = request.args.get('error')
    if error:
        logger.error(f"Google OAuth error: {error}")
        error_description = request.args.get('error_description', 'Unknown error')
        logger.error(f"Google OAuth error description: {error_description}")
        flash(f"Authentication error: {error}. {error_description}", "danger")
        return redirect(url_for('auth.login'))

    # Check for state parameter to prevent CSRF
    state = request.args.get('state')
    if not state or state != session.get('google_oauth_state'):
        logger.error("Invalid state parameter in Google callback")
        flash("Authentication failed: Invalid state parameter", "danger")
        return redirect(url_for('auth.login'))

    # Check for code parameter
    code = request.args.get('code')
    if code:
        logger.info(f"Google authorization code found: {code[:10]}... (truncated)")

        try:
            # Import the Google OAuth module
            from .google_oauth import exchange_code_for_token, get_user_info, create_user_session

            # Exchange the code for a token
            try:
                token_info = exchange_code_for_token(code)
                if not token_info:
                    logger.error("Failed to exchange code for token")
                    flash("Authentication failed: Could not get access token. Please try again.", "danger")
                    return redirect(url_for('auth.login'))
            except Exception as token_error:
                logger.error(f"Error exchanging code for token: {str(token_error)}")
                flash(f"Authentication failed: Error getting access token - {str(token_error)}", "danger")
                return redirect(url_for('auth.login'))

            # Get the user info
            try:
                access_token = token_info.get('access_token')
                user_info = get_user_info(access_token)
                if not user_info:
                    logger.error("Failed to get user info")
                    flash("Authentication failed: Could not get user information. Please try again.", "danger")
                    return redirect(url_for('auth.login'))
            except Exception as user_info_error:
                logger.error(f"Error getting user info: {str(user_info_error)}")
                flash(f"Authentication failed: Error getting user information - {str(user_info_error)}", "danger")
                return redirect(url_for('auth.login'))

            # Create a user session
            try:
                user_session = create_user_session(user_info, token_info)

                # Set session expiration based on token expiration
                if token_info.get('expires_in'):
                    # Calculate expiration time
                    expires_in = int(token_info.get('expires_in', 3600))
                    expiration_time = datetime.datetime.now() + datetime.timedelta(seconds=expires_in)
                    user_session['expiration_time'] = expiration_time.isoformat()
                    logger.info(f"Session will expire at: {expiration_time}")

                # Store the session
                session['user'] = user_session

                # Set permanent session with a lifetime of 30 days if refresh token is available
                if token_info.get('refresh_token'):
                    session.permanent = True
                    current_app.permanent_session_lifetime = datetime.timedelta(days=30)
                    logger.info("Set permanent session with 30-day lifetime")
            except Exception as session_error:
                logger.error(f"Error creating user session: {str(session_error)}")
                flash(f"Authentication failed: Error creating user session - {str(session_error)}", "danger")
                return redirect(url_for('auth.login'))

            logger.info(f"Created Google user session for: {user_session.get('email')}")
            flash(f"Welcome, {user_session.get('name')}! You have successfully logged in with Google.", "success")
            return redirect(url_for('auth.dashboard'))

        except Exception as e:
            logger.error(f"Error processing Google authorization code: {str(e)}")
            flash(f"Authentication failed: {str(e)}", "danger")
            return redirect(url_for('auth.login'))

    # If we get here, there was no code parameter
    logger.error("No authorization code found in Google callback")
    flash("Authentication failed: No authorization code received from Google", "danger")
    return redirect(url_for('auth.login'))


# Add a special route to handle the case where Supabase might redirect to a different URL structure
@auth_bp.route('/auth/callback')
@csrf_exempt
def auth_callback():
    """
    Handle OAuth callback from Supabase with a different URL structure.
    This is a fallback route in case Supabase redirects to a different URL.
    """
    logger.info("Received callback at /auth/callback")
    logger.info(f"Query parameters: {request.args}")

    # Redirect to the main OAuth callback route
    return redirect(url_for('auth.oauth_callback', **request.args))


@auth_bp.route('/google-one-tap', methods=['POST'])
@csrf_exempt
def google_one_tap():
    """
    Handle Google One Tap sign-in.
    This route processes the JWT token from Google One Tap.
    """
    logger.info("Received Google One Tap sign-in request")

    # Get the credential (JWT token) from the request
    credential = request.form.get('credential')
    if not credential:
        logger.error("No credential provided in Google One Tap request")
        flash("Authentication failed: No credential provided", "danger")
        return redirect(url_for('auth.login'))

    try:
        # Decode the JWT token (without verification, as we'll verify with Google)
        # The JWT contains user information directly from Google
        decoded = jwt.decode(credential, options={"verify_signature": False})

        # Extract user information
        user_info = {
            'sub': decoded.get('sub'),  # Google's unique user ID
            'email': decoded.get('email'),
            'name': decoded.get('name'),
            'picture': decoded.get('picture'),
            'email_verified': decoded.get('email_verified', False)
        }

        # Check if email is verified
        if not user_info['email_verified']:
            logger.warning(f"Google account email not verified: {user_info['email']}")
            flash("Authentication failed: Email not verified", "danger")
            return redirect(url_for('auth.login'))

        # Create a unique user ID based on the Google sub (subject) ID
        user_id = f"google-{user_info['sub']}"

        # Check if user exists in Supabase
        supabase = get_supabase()
        user_exists = False

        if supabase:
            try:
                # Try to find the user in Supabase
                response = supabase.table('user_profiles').select('*').eq('user_id', user_id).execute()
                user_exists = response.data and len(response.data) > 0
            except Exception as e:
                logger.error(f"Error checking if user exists in Supabase: {str(e)}")

        # Create user session
        user_session = {
            'id': user_id,
            'email': user_info['email'],
            'name': user_info['name'],
            'picture': user_info['picture'],
            'is_google_user': True,
            'provider': 'google',
            'login_time': datetime.datetime.now().isoformat()
        }

        # Store the session
        session['user'] = user_session

        # If user doesn't exist, create a profile
        if not user_exists:
            profile = create_user_profile(user_id, user_info['email'])
            if profile:
                logger.info(f"Created profile for Google One Tap user: {user_info['email']}")
            else:
                logger.warning(f"Failed to create profile for Google One Tap user: {user_info['email']}")

        logger.info(f"Google One Tap sign-in successful for: {user_info['email']}")
        flash(f"Welcome, {user_info['name']}! You have successfully signed in with Google.", "success")
        return redirect(url_for('auth.dashboard'))

    except Exception as e:
        logger.error(f"Error processing Google One Tap credential: {str(e)}")
        flash(f"Authentication failed: {str(e)}", "danger")
        return redirect(url_for('auth.login'))


@auth_bp.route('/oauth-callback')
@auth_bp.route('/auth/oauth-callback')  # Add this route to match the redirect URL
@csrf_exempt
def oauth_callback():
    """
    Handle OAuth callback.

    Returns:
        Redirect to dashboard or login page.
    """
    # This is the callback from Supabase OAuth
    # Supabase will handle the OAuth flow and redirect back here

    # Log request details for debugging
    logger.info(f"OAuth callback received from: {request.referrer}")
    logger.info(f"OAuth callback full URL: {request.url}")
    logger.info(f"OAuth callback headers: {dict(request.headers)}")
    logger.info(f"OAuth callback query parameters: {request.args}")
    logger.info(f"OAuth callback form data: {request.form}")

    # Log environment information
    logger.info(f"SITE_URL: {os.environ.get('SITE_URL', 'Not set in environment')}")
    logger.info(f"DYNO: {os.environ.get('DYNO', 'Not running on Heroku')}")

    # Check for error
    error = request.args.get('error')
    if error:
        logger.error(f"OAuth error: {error}")
        error_description = request.args.get('error_description', 'Unknown error')
        logger.error(f"OAuth error description: {error_description}")
        flash(f"Authentication error: {error}. {error_description}", "danger")
        return redirect(url_for('auth.login'))

    # Check for code parameter (authorization code flow)
    code = request.args.get('code')
    if code:
        logger.info(f"Authorization code found: {code[:10]}... (truncated)")

        try:
            # Get the Supabase client
            supabase = get_supabase()
            if not supabase:
                logger.error("Supabase client not initialized")
                flash("Authentication service unavailable", "danger")
                return redirect(url_for('auth.login'))

            # Exchange the code for a session
            # This is handled automatically by Supabase when using their OAuth flow
            # The session should already be set up at this point

            # Check if we're already authenticated
            if 'user' in session:
                logger.info(f"User already authenticated: {session['user'].get('email')}")
                return redirect(url_for('auth.dashboard'))

            # If not authenticated yet, render the callback page which will check auth status
            logger.info("User not authenticated yet, rendering callback page")

            # Generate a nonce for CSP
            if not hasattr(request, 'csp_nonce'):
                request.csp_nonce = base64.b64encode(os.urandom(16)).decode('utf-8')

            return render_template('auth/oauth_callback.html')

        except Exception as e:
            logger.error(f"Error processing authorization code: {str(e)}")
            flash(f"Authentication failed: {str(e)}", "danger")
            return redirect(url_for('auth.login'))

    # Check for access token in query parameters (some OAuth providers might use this)
    access_token = request.args.get('access_token')
    if access_token:
        logger.info(f"Access token found in query parameters, redirecting to dashboard")
        return redirect(url_for('auth.dashboard', access_token=access_token))

    # Generate a nonce for CSP
    if not hasattr(request, 'csp_nonce'):
        request.csp_nonce = base64.b64encode(os.urandom(16)).decode('utf-8')

    # Render the OAuth callback template
    # This template contains JavaScript to handle the access token in the URL fragment
    return render_template('auth/oauth_callback.html')


@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_request():
    """
    Handle password reset request.

    Returns:
        The rendered reset request page or a redirect.
    """
    # If user is already logged in, redirect to dashboard
    if 'user' in session:
        return redirect(url_for('auth.dashboard'))

    form = RequestPasswordResetForm()

    if request.method == 'POST':
        logger.info("Password reset request form submitted")

        if form.validate_on_submit():
            email = form.email.data

            # Generate a reset token
            token = get_reset_token(email)

            # Send the reset email
            if send_reset_email(email, token):
                flash('If an account with that email exists, a password reset link has been sent.', 'info')

                # For demo purposes, display the reset link
                if 'reset_link' in session:
                    flash(f'Demo mode: Reset link: {session["reset_link"]}', 'info')

                return redirect(url_for('auth.login'))
            else:
                flash('An error occurred while sending the password reset email. Please try again.', 'danger')
        else:
            logger.warning(f"Form validation failed: {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"{field}: {error}", 'danger')

    return render_template('auth/reset_request.html', form=form)

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_token(token):
    """
    Handle password reset with token.

    Args:
        token (str): The password reset token.

    Returns:
        The rendered reset password page or a redirect.
    """
    # If user is already logged in, redirect to dashboard
    if 'user' in session:
        return redirect(url_for('auth.dashboard'))

    # Verify the token
    email = verify_reset_token(token)
    if not email:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('auth.reset_request'))

    form = ResetPasswordForm()

    if request.method == 'POST':
        logger.info(f"Password reset form submitted for {email}")

        if form.validate_on_submit():
            new_password = form.password.data

            # Reset the password
            if reset_password(email, new_password):
                flash('Your password has been updated! You can now log in with your new password.', 'success')
                return redirect(url_for('auth.login'))
            else:
                flash('An error occurred while resetting your password. Please try again.', 'danger')
        else:
            logger.warning(f"Form validation failed: {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"{field}: {error}", 'danger')

    return render_template('auth/reset_password.html', form=form, token=token)

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """
    Handle password change.

    Returns:
        The rendered change password page or a redirect.
    """
    user = get_current_user()
    if not user:
        flash('You must be logged in to change your password.', 'danger')
        return redirect(url_for('auth.login'))

    form = ChangePasswordForm()

    if request.method == 'POST':
        logger.info(f"Change password form submitted for user {user['id']}")

        if form.validate_on_submit():
            current_password = form.current_password.data
            new_password = form.new_password.data

            success = change_user_password(user['id'], current_password, new_password)

            if success:
                flash('Your password has been changed successfully.', 'success')
                return redirect(url_for('auth.dashboard'))
            else:
                flash('Failed to change password. Please check your current password and try again.', 'danger')
        else:
            logger.warning(f"Form validation failed: {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"{field}: {error}", 'danger')

    return render_template('auth/change_password.html', form=form)

@auth_bp.route('/process-token', methods=['POST'])
def process_token():
    """
    Process the access token received from the OAuth provider.

    This endpoint is called by the client-side JavaScript when an access token
    is found in the URL fragment after OAuth authentication.

    Returns:
        JSON response with redirect URL on success, or error message on failure.
    """
    try:
        logger.info(f"Process token endpoint called with method: {request.method}")
        logger.info(f"Request content type: {request.content_type}")
        logger.info(f"Form data keys: {list(request.form.keys()) if request.form else 'No form data'}")
        logger.info(f"JSON data: {request.get_json(silent=True)}")

        # Get the token data from the request (either form data or JSON)
        if request.content_type and 'application/json' in request.content_type:
            token_data = request.json
        else:
            token_data = request.form

        logger.info(f"Processing token data keys: {list(token_data.keys()) if token_data else 'No token data'}")

        if not token_data or 'access_token' not in token_data:
            logger.error("No access token provided")
            return jsonify({
                'success': False,
                'message': 'Authentication failed: No access token provided',
                'redirect_url': url_for('auth.login')
            }), 400

        # Get the Supabase client
        supabase = get_supabase()
        if not supabase:
            logger.error("Supabase client not initialized")
            return jsonify({
                'success': False,
                'message': 'Authentication service unavailable',
                'redirect_url': url_for('auth.login')
            }), 500

        # Handle test token for development/testing
        access_token = token_data['access_token']
        if access_token == 'test_token':
            logger.info("Using test token for development")
            # Create a test user session
            session['user'] = {
                'id': 'test-user-id',
                'email': 'test@example.com',
                'access_token': 'test_token',
                'is_test_user': True
            }
            return jsonify({
                'success': True,
                'message': 'Logged in with test account',
                'redirect_url': url_for('auth.dashboard')
            })

        try:
            # Get the user data from the token
            logger.info(f"Using access token: {access_token[:10]}... (truncated)")

            # Extract additional token information
            refresh_token = token_data.get('refresh_token')
            expires_in = token_data.get('expires_in')
            provider_token = token_data.get('provider_token')

            logger.info(f"Additional token info - refresh_token: {'Present' if refresh_token else 'Not present'}, " +
                       f"expires_in: {expires_in if expires_in else 'Not present'}, " +
                       f"provider_token: {'Present' if provider_token else 'Not present'}")

            try:
                user = supabase.auth.get_user(access_token)
                logger.info(f"User data retrieved: {user}")
            except Exception as e:
                logger.error(f"Error getting user data from token: {str(e)}")
                # Try to exchange the token for a session
                try:
                    logger.info("Attempting to exchange token for session")
                    session_response = supabase.auth.set_session(access_token, refresh_token)
                    logger.info(f"Session response: {session_response}")
                    user = supabase.auth.get_user()
                    logger.info(f"User data retrieved after session exchange: {user}")
                except Exception as inner_e:
                    logger.error(f"Error exchanging token for session: {str(inner_e)}")
                    return jsonify({
                        'success': False,
                        'message': f'Authentication failed: Could not validate token: {str(e)}',
                        'redirect_url': url_for('auth.login')
                    }), 400

            if user and hasattr(user, 'user'):
                user_data = user.user
                logger.info(f"User data: {user_data}")

                # Store the session in Flask session
                session_data = {
                    'id': user_data.id,
                    'email': user_data.email,
                    'access_token': access_token
                }

                # Add additional token data if available
                if refresh_token:
                    session_data['refresh_token'] = refresh_token
                if expires_in:
                    session_data['expires_in'] = expires_in
                if provider_token:
                    session_data['provider_token'] = provider_token

                session['user'] = session_data

                # Check if the user has a profile, create one if not
                get_user_profile(user_data.id)

                logger.info(f"Successfully authenticated user: {user_data.email}")
                return jsonify({
                    'success': True,
                    'message': 'You have successfully logged in!',
                    'redirect_url': url_for('auth.dashboard')
                })
            else:
                logger.error("Invalid user data from token")
                return jsonify({
                    'success': False,
                    'message': 'Authentication failed: Invalid user data',
                    'redirect_url': url_for('auth.login')
                }), 400
        except Exception as e:
            logger.error(f"Error processing token: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'Authentication failed: {str(e)}',
                'redirect_url': url_for('auth.login')
            }), 400
    except Exception as e:
        logger.error(f"Error in process_token: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Authentication failed: {str(e)}',
            'redirect_url': url_for('auth.login')
        }), 500


@auth_bp.route('/check-auth', methods=['GET'])
def check_auth():
    """
    Check if the user is authenticated.

    Returns:
        JSON response with authentication status.
    """
    is_authenticated = 'user' in session
    user_data = None

    if is_authenticated:
        user_data = {
            'email': session['user'].get('email'),
            'id': session['user'].get('id')
        }
        logger.info(f"User is authenticated: {user_data['email']}")
    else:
        logger.info("User is not authenticated")

    return jsonify({
        'authenticated': is_authenticated,
        'user': user_data
    })


@auth_bp.route('/profile/create', methods=['GET', 'POST'])
@login_required
@csrf_exempt
def create_profile():
    """
    Create a user profile if it doesn't exist.

    Returns:
        Redirect to profile page.
    """
    user = get_current_user()
    if not user:
        flash('You must be logged in to create a profile.', 'danger')
        return redirect(url_for('auth.login'))

    # Check if profile already exists
    profile = get_user_profile(user['id'])
    if profile:
        flash('You already have a profile.', 'info')
        return redirect(url_for('auth.profile'))

    # Create profile
    from .utils import create_user_profile
    profile = create_user_profile(user['id'])

    if profile:
        flash('Created a new profile for you.', 'success')
    else:
        flash('Failed to create a profile. Please try again.', 'danger')

    return redirect(url_for('auth.profile'))
