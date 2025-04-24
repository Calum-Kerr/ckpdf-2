"""
Main routes for the application.
This module contains the main routes for the application.
"""

from flask import Blueprint, render_template, current_app, request, redirect, url_for
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """
    Render the index page.
    Also handles OAuth callback redirects if a code parameter is present.

    Returns:
        The rendered index page or a redirect to the OAuth callback.
    """
    # Check if this is an OAuth callback (has a code parameter)
    code = request.args.get('code')
    if code:
        logger.info(f"Detected OAuth callback code at root URL: {code[:10]}... (truncated)")
        # Redirect to the OAuth callback route with the code
        return redirect(url_for('auth.oauth_callback', code=code))

    # Normal index page rendering
    return render_template('index.html')

@main_bp.route('/privacy-policy')
def privacy_policy():
    """
    Render the privacy policy page.

    Returns:
        The rendered privacy policy page.
    """
    return render_template('legal/privacy_policy.html')

@main_bp.route('/terms-of-service')
def terms_of_service():
    """
    Render the terms of service page.

    Returns:
        The rendered terms of service page.
    """
    return render_template('legal/terms_of_service.html')

@main_bp.route('/cookie-policy')
def cookie_policy():
    """
    Render the cookie policy page.

    Returns:
        The rendered cookie policy page.
    """
    return render_template('legal/cookie_policy.html')

@main_bp.route('/gdpr-compliance')
def gdpr_compliance():
    """
    Render the GDPR compliance page.

    Returns:
        The rendered GDPR compliance page.
    """
    return render_template('legal/gdpr_compliance.html')

@main_bp.route('/accessibility-statement')
def accessibility_statement():
    """
    Render the accessibility statement page.

    Returns:
        The rendered accessibility statement page.
    """
    return render_template('legal/accessibility_statement.html')

@main_bp.route('/data-protection')
def data_protection():
    """
    Render the data protection page.

    Returns:
        The rendered data protection page.
    """
    return render_template('legal/data_protection.html')

@main_bp.route('/security-information')
def security_information():
    """
    Render the security information page.

    Returns:
        The rendered security information page.
    """
    return render_template('legal/security_information.html')
