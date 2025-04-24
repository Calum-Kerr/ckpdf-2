"""
Main routes for the application.
This module contains the main routes for the application.
"""

from flask import Blueprint, render_template, current_app, request, redirect, url_for, send_from_directory
import logging
import os

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

@main_bp.route('/sitemap.xml')
def sitemap():
    """
    Serve the sitemap.xml file.

    Returns:
        The sitemap.xml file.
    """
    return send_from_directory(current_app.root_path + '/../', 'sitemap.xml')

@main_bp.route('/robots.txt')
def robots():
    """
    Serve the robots.txt file.

    Returns:
        The robots.txt file.
    """
    return send_from_directory(current_app.root_path + '/../', 'robots.txt')

@main_bp.route('/google6520a768170937d3.html')
def google_verification():
    """
    Serve the Google Search Console verification file.

    Returns:
        The Google verification file.
    """
    return send_from_directory(current_app.static_folder, 'google6520a768170937d3.html')

@main_bp.route('/blog')
def blog():
    """
    Render the blog index page.

    Returns:
        The rendered blog index page.
    """
    return render_template('blog/index.html')

@main_bp.route('/blog/<slug>')
def blog_post(slug):
    """
    Render a specific blog post.

    Args:
        slug: The slug of the blog post.

    Returns:
        The rendered blog post page.
    """
    # Map slugs to template files
    blog_posts = {
        'best-pdf-tools-for-students': 'blog/best-pdf-tools-for-students.html',
        'how-to-compress-pdf-without-losing-quality': 'blog/how-to-compress-pdf-without-losing-quality.html',
        'ocr-technology-explained': 'blog/ocr-technology-explained.html',
        'secure-pdf-handling-best-practices': 'blog/secure-pdf-handling-best-practices.html',
        'convert-images-to-pdf-guide': 'blog/convert-images-to-pdf-guide.html',
        'pdf-accessibility-guide': 'blog/pdf-accessibility-guide.html'
    }

    if slug in blog_posts:
        return render_template(blog_posts[slug])
    else:
        return render_template('errors/404.html'), 404
