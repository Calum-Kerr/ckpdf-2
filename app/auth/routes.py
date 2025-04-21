"""
Authentication routes for the application.
This module contains routes for authentication features.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from .utils import login_user, register_user, logout_user, get_current_user, login_required, get_user_profile
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
    
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        
        user = register_user(email, password)
        
        if user:
            flash('Registration successful! Please check your email to verify your account.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Registration failed. Please try again.', 'danger')
    
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
