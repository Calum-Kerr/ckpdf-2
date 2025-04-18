"""
Security API routes.
This module provides API routes for security-related functionality.
"""

import logging
from flask import Blueprint, request, jsonify, current_app
from app.security.auth import api_token_required

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
security_api_bp = Blueprint('security_api', __name__, url_prefix='/api/security')

@security_api_bp.route('/csp-report', methods=['POST'])
def csp_report():
    """
    Handle CSP violation reports.
    
    Returns:
        JSON response.
    """
    try:
        # Get the report data
        report = request.get_json()
        
        # Log the violation
        logger.warning(f"CSP Violation: {report}")
        
        return jsonify({'status': 'success'}), 204
    except Exception as e:
        logger.error(f"Error processing CSP report: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Error processing report'}), 400

@security_api_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint.
    
    Returns:
        JSON response with health status.
    """
    return jsonify({
        'status': 'ok',
        'version': current_app.config.get('VERSION', '1.0.0')
    })

@security_api_bp.route('/token', methods=['POST'])
def get_token():
    """
    Get a new API token.
    
    Returns:
        JSON response with token.
    """
    from app.security.auth import generate_api_token
    
    # Generate a new token
    token, expiration = generate_api_token()
    
    # Store the token in the session
    from flask import session
    session['api_token'] = token
    session['token_expiration'] = expiration
    
    return jsonify({
        'token': token,
        'expires': expiration
    })

@security_api_bp.route('/protected', methods=['GET'])
@api_token_required
def protected_endpoint():
    """
    Protected endpoint that requires a valid API token.
    
    Returns:
        JSON response.
    """
    return jsonify({
        'status': 'success',
        'message': 'You have access to this protected endpoint'
    })
