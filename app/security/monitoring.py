"""
Security monitoring module.
This module provides functions for monitoring security events.
"""

import os
import time
import json
import logging
import threading
from datetime import datetime
from flask import request, current_app, g

# Configure logging
logger = logging.getLogger(__name__)

# Default log directory
DEFAULT_LOG_DIR = 'logs/security'

class SecurityMonitor:
    """Class for monitoring security events."""
    
    def __init__(self, app=None, log_dir=None):
        """
        Initialize the security monitor.
        
        Args:
            app: The Flask application.
            log_dir: Directory for security logs.
        """
        self.app = app
        self.log_dir = log_dir or DEFAULT_LOG_DIR
        self.suspicious_ips = set()
        self.ip_request_counts = {}
        self.ip_last_reset = {}
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """
        Initialize the security monitor with a Flask application.
        
        Args:
            app: The Flask application.
        """
        # Create log directory
        self.log_dir = app.config.get('SECURITY_LOG_DIR', self.log_dir)
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Register before_request handler
        app.before_request(self.monitor_request)
        
        # Register after_request handler
        app.after_request(self.log_response)
        
        # Start cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_thread, daemon=True)
        self.cleanup_thread.start()
        
        logger.info("Security monitor initialized")
    
    def monitor_request(self):
        """Monitor incoming requests for suspicious activity."""
        # Get client IP
        client_ip = request.remote_addr
        
        # Check if IP is already marked as suspicious
        if client_ip in self.suspicious_ips:
            logger.warning(f"Request from suspicious IP: {client_ip}")
            self._log_security_event('suspicious_ip', {
                'ip': client_ip,
                'path': request.path,
                'method': request.method
            })
        
        # Track request count for rate limiting
        if client_ip not in self.ip_request_counts:
            self.ip_request_counts[client_ip] = 0
            self.ip_last_reset[client_ip] = time.time()
        
        # Reset count if it's been more than an hour
        if time.time() - self.ip_last_reset[client_ip] > 3600:
            self.ip_request_counts[client_ip] = 0
            self.ip_last_reset[client_ip] = time.time()
        
        # Increment request count
        self.ip_request_counts[client_ip] += 1
        
        # Check for high request rate
        if self.ip_request_counts[client_ip] > 100:  # More than 100 requests per hour
            if client_ip not in self.suspicious_ips:
                logger.warning(f"High request rate from IP: {client_ip}")
                self.suspicious_ips.add(client_ip)
                self._log_security_event('high_request_rate', {
                    'ip': client_ip,
                    'count': self.ip_request_counts[client_ip],
                    'period': 'hour'
                })
        
        # Check for suspicious request patterns
        self._check_suspicious_patterns()
    
    def log_response(self, response):
        """
        Log the response for security monitoring.
        
        Args:
            response: The Flask response.
            
        Returns:
            The response.
        """
        # Log 4xx and 5xx responses
        if 400 <= response.status_code < 600:
            self._log_security_event('error_response', {
                'ip': request.remote_addr,
                'path': request.path,
                'method': request.method,
                'status_code': response.status_code
            })
        
        return response
    
    def _check_suspicious_patterns(self):
        """Check for suspicious patterns in the request."""
        # Check for SQL injection attempts
        sql_patterns = [
            'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'UNION',
            'OR 1=1', 'OR TRUE', 'OR \'1\'=\'1\'', '--', '/*'
        ]
        
        # Check URL parameters
        for param, value in request.args.items():
            for pattern in sql_patterns:
                if pattern.lower() in value.lower():
                    logger.warning(f"Possible SQL injection attempt in URL parameter: {param}={value}")
                    self._log_security_event('sql_injection_attempt', {
                        'ip': request.remote_addr,
                        'parameter': param,
                        'value': value
                    })
                    self.suspicious_ips.add(request.remote_addr)
                    return
        
        # Check form data
        for param, value in request.form.items():
            for pattern in sql_patterns:
                if pattern.lower() in value.lower():
                    logger.warning(f"Possible SQL injection attempt in form data: {param}={value}")
                    self._log_security_event('sql_injection_attempt', {
                        'ip': request.remote_addr,
                        'parameter': param,
                        'value': value
                    })
                    self.suspicious_ips.add(request.remote_addr)
                    return
        
        # Check for XSS attempts
        xss_patterns = [
            '<script', 'javascript:', 'onerror=', 'onload=', 'eval(',
            'document.cookie', 'alert(', 'String.fromCharCode('
        ]
        
        # Check URL parameters
        for param, value in request.args.items():
            for pattern in xss_patterns:
                if pattern.lower() in value.lower():
                    logger.warning(f"Possible XSS attempt in URL parameter: {param}={value}")
                    self._log_security_event('xss_attempt', {
                        'ip': request.remote_addr,
                        'parameter': param,
                        'value': value
                    })
                    self.suspicious_ips.add(request.remote_addr)
                    return
        
        # Check form data
        for param, value in request.form.items():
            for pattern in xss_patterns:
                if pattern.lower() in value.lower():
                    logger.warning(f"Possible XSS attempt in form data: {param}={value}")
                    self._log_security_event('xss_attempt', {
                        'ip': request.remote_addr,
                        'parameter': param,
                        'value': value
                    })
                    self.suspicious_ips.add(request.remote_addr)
                    return
    
    def _log_security_event(self, event_type, data):
        """
        Log a security event.
        
        Args:
            event_type: The type of security event.
            data: Additional data about the event.
        """
        # Create event data
        event = {
            'timestamp': datetime.now().isoformat(),
            'type': event_type,
            'request_id': getattr(g, 'request_id', 'unknown'),
            'data': data
        }
        
        # Log to file
        log_file = os.path.join(self.log_dir, f"{datetime.now().strftime('%Y-%m-%d')}.log")
        
        try:
            with open(log_file, 'a') as f:
                f.write(json.dumps(event) + '\n')
        except Exception as e:
            logger.error(f"Error writing to security log: {str(e)}")
        
        # Log to application logger
        logger.warning(f"Security event: {event_type} - {json.dumps(data)}")
    
    def _cleanup_thread(self):
        """Background thread to clean up old data."""
        while True:
            try:
                # Clean up IP request counts older than a day
                current_time = time.time()
                for ip in list(self.ip_last_reset.keys()):
                    if current_time - self.ip_last_reset[ip] > 86400:  # 24 hours
                        del self.ip_request_counts[ip]
                        del self.ip_last_reset[ip]
                
                # Clean up suspicious IPs after a week
                for ip in list(self.suspicious_ips):
                    # This is a simplified approach - in a real application,
                    # you would store the time when the IP was marked as suspicious
                    # and check against that time
                    pass
            except Exception as e:
                logger.error(f"Error in cleanup thread: {str(e)}")
            
            # Sleep for a while before the next cleanup
            time.sleep(3600)  # 1 hour
