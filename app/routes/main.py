"""
Main routes for the application.
This module contains the main routes for the application.
"""

from flask import Blueprint, render_template, current_app

# Create blueprint
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """
    Render the index page.
    
    Returns:
        The rendered index page.
    """
    return render_template('index.html')

@main_bp.route('/privacy-policy')
def privacy_policy():
    """
    Render the privacy policy page.
    
    Returns:
        The rendered privacy policy page.
    """
    return render_template('compliance/privacy_policy.html')

@main_bp.route('/terms-of-service')
def terms_of_service():
    """
    Render the terms of service page.
    
    Returns:
        The rendered terms of service page.
    """
    return render_template('compliance/terms_of_service.html')

@main_bp.route('/cookie-policy')
def cookie_policy():
    """
    Render the cookie policy page.
    
    Returns:
        The rendered cookie policy page.
    """
    return render_template('compliance/cookie_policy.html')

@main_bp.route('/gdpr-compliance')
def gdpr_compliance():
    """
    Render the GDPR compliance page.
    
    Returns:
        The rendered GDPR compliance page.
    """
    return render_template('compliance/gdpr_compliance.html')

@main_bp.route('/accessibility-statement')
def accessibility_statement():
    """
    Render the accessibility statement page.
    
    Returns:
        The rendered accessibility statement page.
    """
    return render_template('compliance/accessibility_statement.html')

@main_bp.route('/data-protection')
def data_protection():
    """
    Render the data protection page.
    
    Returns:
        The rendered data protection page.
    """
    return render_template('compliance/data_protection.html')

@main_bp.route('/security-information')
def security_information():
    """
    Render the security information page.
    
    Returns:
        The rendered security information page.
    """
    return render_template('compliance/security_information.html')
