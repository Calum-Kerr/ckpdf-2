"""
Authentication routes for the application.
This module contains routes for authentication features.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import logging
import datetime

# Configure logging
logger = logging.getLogger(__name__)
from .utils import login_user, register_user, logout_user, get_current_user, login_required, get_user_profile, demo_profiles, csrf_exempt, change_user_password, get_reset_token, verify_reset_token, send_reset_email, reset_password
from app.forms import LoginForm, RegisterForm
from .forms import ChangePasswordForm, RequestPasswordResetForm, ResetPasswordForm

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
