"""
Authentication routes for the application.
This module contains routes for authentication features.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
import logging
import datetime
import urllib.parse
import os

# Configure logging
logger = logging.getLogger(__name__)
from .utils import (
    login_user, register_user, logout_user, get_current_user, login_required,
    get_user_profile, demo_profiles, csrf_exempt, change_user_password,
    get_reset_token, verify_reset_token, send_reset_email, reset_password
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
@login_required
def dashboard():
    """
    Display the user dashboard.

    Returns:
        The rendered dashboard page.
    """
    user = get_current_user()

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
    Initiate Google OAuth login.

    Returns:
        Redirect to Google OAuth login page.
    """
    supabase = get_supabase()
    if not supabase:
        logger.warning("Supabase client not initialized. Cannot use Google login.")
        flash("Google login is not available at this time. Please use email and password.", "warning")
        return redirect(url_for('auth.login'))

    try:
        # Get the base URL from request or config
        base_url = request.host_url.rstrip('/')
        if base_url.startswith('http://') and not current_app.debug:
            # Force HTTPS in production
            base_url = 'https://' + base_url[7:]

        # Get the redirect URL for OAuth callback
        redirect_url = f"{base_url}/auth/oauth-callback"
        logger.info(f"Using redirect URL: {redirect_url}")

        # Log Supabase configuration for debugging
        logger.info(f"Supabase URL: {current_app.config.get('SUPABASE_URL', 'Not configured')}")
        logger.info(f"Google Client ID: {current_app.config.get('GOOGLE_CLIENT_ID', 'Not configured')}")
        logger.info(f"Site URL: {current_app.config.get('SITE_URL', 'Not configured')}")

        # Use the Supabase sign_in_with_oauth method to get the OAuth URL
        try:
            # For production, specify the redirect_to parameter explicitly
            # This ensures Supabase redirects back to our application

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
            logger.info(f"Using redirect URL: {redirect_url}")

            oauth_data = {
                'provider': 'google',
                'redirect_to': redirect_url  # Specify the redirect URL for production
            }

            # Log the OAuth data for debugging
            logger.info(f"OAuth data: {oauth_data}")
            oauth_response = supabase.auth.sign_in_with_oauth(oauth_data)

            if not oauth_response or not hasattr(oauth_response, 'url'):
                logger.error("Failed to get OAuth URL from Supabase")
                flash("Google login is not available at this time. Please use email and password.", "warning")
                return redirect(url_for('auth.login'))

            supabase_oauth_url = oauth_response.url
            logger.info(f"Got OAuth URL from Supabase: {supabase_oauth_url}")

            # Store the OAuth URL in the session for the callback
            session['supabase_oauth_url'] = supabase_oauth_url

            # Store the expected redirect URL in the session for verification
            session['expected_redirect_url'] = redirect_url

            # Redirect directly to the Supabase OAuth URL
            # The PKCE flow will handle the state and code verifier
            logger.info(f"Redirecting to Supabase OAuth URL: {supabase_oauth_url}")
            return redirect(supabase_oauth_url)
        except Exception as e:
            logger.error(f"Error getting OAuth URL from Supabase: {str(e)}")
            flash("An error occurred while trying to log in with Google. Please try again or use email and password.", "danger")
            return redirect(url_for('auth.login'))
    except Exception as e:
        logger.error(f"Error initiating Google OAuth: {str(e)}")
        flash("An error occurred while trying to log in with Google. Please try again or use email and password.", "danger")
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


@auth_bp.route('/oauth-callback')
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

    # Check if we have the expected redirect URL in session
    expected_redirect_url = session.get('expected_redirect_url')
    if expected_redirect_url:
        logger.info(f"Expected redirect URL from session: {expected_redirect_url}")
        # Clear it from session
        session.pop('expected_redirect_url', None)
    else:
        logger.warning("No expected redirect URL in session")

    # Check for error
    error = request.args.get('error')
    if error:
        logger.error(f"OAuth error: {error}")
        error_description = request.args.get('error_description', 'Unknown error')
        logger.error(f"OAuth error description: {error_description}")
        flash(f"Authentication error: {error}. {error_description}", "danger")
        return redirect(url_for('auth.login'))

    # Log all query parameters for debugging
    logger.info(f"OAuth callback query parameters: {request.args}")

    # Check for various parameters that might be returned
    auth_code = request.args.get('code')
    access_token = request.args.get('access_token')
    refresh_token = request.args.get('refresh_token')
    provider_token = request.args.get('provider_token')

    # Log all possible authentication parameters
    if auth_code:
        logger.info(f"Received authorization code: {auth_code[:10]}... (truncated)")
    if access_token:
        logger.info("Received access token (not shown for security)")
    if refresh_token:
        logger.info("Received refresh token (not shown for security)")
    if provider_token:
        logger.info("Received provider token (not shown for security)")

    # Check if we have any authentication parameters
    if not (auth_code or access_token or refresh_token or provider_token):
        logger.warning("No authentication parameters in OAuth callback")
        # Check for other authentication methods
        if not request.args:
            logger.error("No query parameters in OAuth callback")
            flash("Authentication failed. No response received from the authentication provider.", "danger")
            return redirect(url_for('auth.login'))

    try:
        # Get the Supabase client
        supabase = get_supabase()
        if not supabase:
            logger.error("Supabase client not initialized")
            flash("Authentication failed due to configuration error. Please try again later.", "danger")
            return redirect(url_for('auth.login'))

        # If we have an authorization code, try to exchange it for a token
        if auth_code:
            try:
                # Exchange the code for a token
                logger.info("Attempting to exchange authorization code for token")

                # Try to exchange the code for a token directly
                try:
                    # Get the redirect URL that was used
                    redirect_url = request.base_url
                    logger.info(f"Using callback URL for token exchange: {redirect_url}")

                    # Exchange the code for a token
                    session_response = supabase.auth.exchange_code_for_session({
                        'auth_code': auth_code
                    })

                    if session_response and hasattr(session_response, 'session'):
                        logger.info("Successfully exchanged code for session")
                        session_data = session_response.session
                        user_data = session_data.user

                        # Store the session in Flask session
                        session['user'] = {
                            'id': user_data.id,
                            'email': user_data.email,
                            'access_token': session_data.access_token,
                            'refresh_token': session_data.refresh_token
                        }

                        # Check if the user has a profile, create one if not
                        get_user_profile(user_data.id)

                        logger.info(f"Successfully authenticated user with code exchange: {user_data.email}")

                        # Redirect to the dashboard or next page
                        next_page = request.args.get('next')
                        if next_page:
                            return redirect(next_page)
                        return redirect(url_for('auth.dashboard'))
                except Exception as exchange_error:
                    logger.warning(f"Could not exchange code for session: {str(exchange_error)}")
                    # Continue with other authentication methods
            except Exception as code_error:
                logger.error(f"Error exchanging authorization code: {str(code_error)}")

        # Try to get the current user - they might already be authenticated
        try:
            # Get the current user
            user = supabase.auth.get_user()

            if user and hasattr(user, 'user'):
                user_data = user.user

                # Store the session in Flask session
                session['user'] = {
                    'id': user_data.id,
                    'email': user_data.email,
                    'access_token': getattr(user, 'access_token', None),
                    'refresh_token': getattr(user, 'refresh_token', None)
                }

                # Check if the user has a profile, create one if not
                get_user_profile(user_data.id)

                logger.info(f"Successfully authenticated user: {user_data.email}")

                # Redirect to the dashboard or next page
                next_page = request.args.get('next')
                if next_page:
                    return redirect(next_page)
                return redirect(url_for('auth.dashboard'))
        except Exception as user_error:
            logger.warning(f"Could not get current user: {str(user_error)}")

        # If we get here, we need to try a different approach
        # Let's try to get the session from the cookies
        try:
            # Get the session from the cookies
            session_data = supabase.auth.get_session()

            if session_data and hasattr(session_data, 'user'):
                user_data = session_data.user

                # Store the session in Flask session
                session['user'] = {
                    'id': user_data.id,
                    'email': user_data.email,
                    'access_token': getattr(session_data, 'access_token', None),
                    'refresh_token': getattr(session_data, 'refresh_token', None)
                }

                # Check if the user has a profile, create one if not
                get_user_profile(user_data.id)

                logger.info(f"Successfully authenticated user from session: {user_data.email}")

                # Redirect to the dashboard or next page
                next_page = request.args.get('next')
                if next_page:
                    return redirect(next_page)
                return redirect(url_for('auth.dashboard'))
        except Exception as session_error:
            logger.warning(f"Could not get session: {str(session_error)}")

        # If we still don't have a user, we need to try one more approach
        # Let's try to sign in with the provider token if available
        provider_token = request.args.get('provider_token')
        if provider_token:
            try:
                # Sign in with the provider token
                auth_response = supabase.auth.sign_in_with_idp({
                    'provider': 'google',
                    'access_token': provider_token
                })

                if auth_response and hasattr(auth_response, 'user'):
                    user_data = auth_response.user

                    # Store the session in Flask session
                    session['user'] = {
                        'id': user_data.id,
                        'email': user_data.email,
                        'access_token': getattr(auth_response, 'access_token', None),
                        'refresh_token': getattr(auth_response, 'refresh_token', None)
                    }

                    # Check if the user has a profile, create one if not
                    get_user_profile(user_data.id)

                    logger.info(f"Successfully authenticated user with provider token: {user_data.email}")

                    # Redirect to the dashboard or next page
                    next_page = request.args.get('next')
                    if next_page:
                        return redirect(next_page)
                    return redirect(url_for('auth.dashboard'))
            except Exception as provider_error:
                logger.warning(f"Could not sign in with provider token: {str(provider_error)}")

        # If we still don't have a user, we need to redirect to login
        logger.error("Could not authenticate user with any method")
        flash("Authentication failed. Please try again.", "danger")
        return redirect(url_for('auth.login'))
    except Exception as e:
        logger.error(f"Error in OAuth callback: {str(e)}")
        flash("An error occurred during authentication. Please try again.", "danger")
        return redirect(url_for('auth.login'))


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
