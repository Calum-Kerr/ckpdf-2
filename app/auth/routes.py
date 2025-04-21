"""
Authentication routes for the application.
This module contains routes for authentication features.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app, jsonify
import logging

# Configure logging
logger = logging.getLogger(__name__)
from .utils import login_user, register_user, logout_user, get_current_user, login_required, get_user_profile, track_file_usage
from app.forms import LoginForm, RegisterForm

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
    profile = get_user_profile(user['id']) if user else None

    return render_template('auth/dashboard.html', user=user, profile=profile)

@auth_bp.route('/profile')
@login_required
def profile():
    """
    Display the user profile.

    Returns:
        The rendered profile page.
    """
    user = get_current_user()
    profile = get_user_profile(user['id']) if user else None

    return render_template('auth/profile.html', user=user, profile=profile)

@auth_bp.route('/profile/debug')
@login_required
def profile_debug():
    """
    Display debug information about the user profile.

    Returns:
        JSON with profile information.
    """
    user = get_current_user()
    profile = get_user_profile(user['id']) if user else None

    return jsonify({
        'user': user,
        'profile': profile
    })

@auth_bp.route('/profile/update-storage', methods=['POST'])
@login_required
def update_storage():
    """
    Manually update storage usage for testing.

    Returns:
        Redirect to profile page.
    """
    user = get_current_user()
    if not user:
        flash('You must be logged in to update storage usage.', 'danger')
        return redirect(url_for('auth.login'))

    # Get or create profile
    profile = get_user_profile(user['id'])
    if not profile:
        logger.warning(f"No profile found for user {user['id']}, creating one")
        from .utils import create_user_profile
        profile = create_user_profile(user['id'])
        if profile:
            flash('Created a new profile for you.', 'success')
        else:
            flash('Failed to create a profile. Please try again.', 'danger')
            return redirect(url_for('auth.profile'))

    # Add 1MB to storage usage for testing
    test_file_size = 1 * 1024 * 1024  # 1MB in bytes
    success = track_file_usage(user['id'], test_file_size)

    if success:
        flash('Added 1MB to your storage usage for testing.', 'success')
    else:
        flash('Failed to update storage usage.', 'danger')

    return redirect(url_for('auth.profile'))

@auth_bp.route('/profile/create', methods=['GET', 'POST'])
@login_required
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
