"""
Authentication routes for the application.
This module contains routes for authentication features.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import logging
import datetime

# Configure logging
logger = logging.getLogger(__name__)
from .utils import login_user, register_user, logout_user, get_current_user, login_required, get_user_profile, demo_profiles, csrf_exempt
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

    # Try to get profile from Supabase
    profile = get_user_profile(user['id']) if user else None

    # If Supabase fails, use demo profile or create one
    if not profile and user:
        if user['id'] in demo_profiles:
            profile = demo_profiles[user['id']]
            logger.info(f"Using existing demo profile for user {user['id']}")
        else:
            # Create a new demo profile
            demo_profiles[user['id']] = {
                'user_id': user['id'],
                'email': user.get('email', 'unknown@example.com'),
                'account_type': 'free',
                'storage_used': 0,
                'storage_limit': 50 * 1024 * 1024,  # 50MB for free users
                'created_at': datetime.datetime.now().isoformat()
            }
            profile = demo_profiles[user['id']]
            logger.info(f"Created new demo profile for user {user['id']}")

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

    # Try to get profile from Supabase
    profile = get_user_profile(user['id']) if user else None

    # If Supabase fails, use demo profile or create one
    if not profile and user:
        if user['id'] in demo_profiles:
            profile = demo_profiles[user['id']]
            logger.info(f"Using existing demo profile for user {user['id']}")
        else:
            # Create a new demo profile
            demo_profiles[user['id']] = {
                'user_id': user['id'],
                'email': user.get('email', 'unknown@example.com'),
                'account_type': 'free',
                'storage_used': 0,
                'storage_limit': 50 * 1024 * 1024,  # 50MB for free users
                'created_at': datetime.datetime.now().isoformat()
            }
            profile = demo_profiles[user['id']]
            logger.info(f"Created new demo profile for user {user['id']}")

    return render_template('auth/profile.html', user=user, profile=profile)



@auth_bp.route('/profile/update-storage', methods=['GET'])
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

    # Add 5MB to storage usage for testing
    test_file_size = 5 * 1024 * 1024  # 5MB in bytes

    # Force demo mode for testing
    try:
        # Create a new demo profile if it doesn't exist
        if user['id'] not in demo_profiles:
            demo_profiles[user['id']] = {
                'user_id': user['id'],
                'email': user.get('email', 'unknown@example.com'),
                'account_type': 'free',
                'storage_used': 0,
                'storage_limit': 50 * 1024 * 1024,  # 50MB for free users
                'created_at': datetime.datetime.now().isoformat()
            }
            logger.info(f"Created new demo profile for user {user['id']}")

        # Update storage usage
        current_usage = demo_profiles[user['id']].get('storage_used', 0)
        new_usage = current_usage + test_file_size
        demo_profiles[user['id']]['storage_used'] = new_usage
        logger.info(f"Updated demo profile storage usage for user {user['id']}: {test_file_size} bytes, new total: {new_usage} bytes")
        success = True
    except Exception as e:
        logger.error(f"Error updating storage usage: {str(e)}")
        success = False

    if success:
        flash(f'Added {test_file_size / 1024 / 1024:.0f}MB to your storage usage.', 'success')
    else:
        flash('Failed to update storage usage.', 'danger')

    # Add a flash message with the current storage usage
    updated_profile = demo_profiles.get(user['id'])
    if updated_profile:
        used_mb = updated_profile.get('storage_used', 0) / 1024 / 1024
        limit_mb = updated_profile.get('storage_limit', 0) / 1024 / 1024
        usage_percent = (used_mb / limit_mb * 100) if limit_mb > 0 else 0
        flash(f"Current storage usage: {used_mb:.1f} MB of {limit_mb:.0f} MB ({usage_percent:.0f}%)", 'success')

    return redirect(url_for('auth.profile'))



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
