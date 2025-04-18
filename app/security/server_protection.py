"""
Server protection module.
This module provides functions to protect the server from various attacks.
"""

import os
import time
import logging
import threading
import signal
import resource
from functools import wraps
from flask import request, abort, current_app

# Configure logging
logger = logging.getLogger(__name__)

# Default timeout for processing operations (30 seconds)
DEFAULT_TIMEOUT = 30

# Default resource limits
DEFAULT_RESOURCE_LIMITS = {
    'CPU_TIME': 30,  # 30 seconds of CPU time
    'MEMORY': 1024 * 1024 * 500,  # 500MB of memory
    'FILES': 100,  # Maximum number of open files
}

class TimeoutError(Exception):
    """Exception raised when a function times out."""
    pass

def timeout_handler(signum, frame):
    """Signal handler for timeouts."""
    raise TimeoutError("Operation timed out")

def with_timeout(seconds=DEFAULT_TIMEOUT):
    """
    Decorator to apply a timeout to a function.
    
    Args:
        seconds: The timeout in seconds.
        
    Returns:
        The decorated function.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Set the timeout handler
            original_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(seconds)
            
            try:
                result = func(*args, **kwargs)
                return result
            except TimeoutError:
                logger.error(f"Function {func.__name__} timed out after {seconds} seconds")
                raise
            finally:
                # Reset the alarm and restore the original handler
                signal.alarm(0)
                signal.signal(signal.SIGALRM, original_handler)
        
        return wrapper
    
    return decorator

def set_resource_limits(limits=None):
    """
    Set resource limits for the current process.
    
    Args:
        limits: Dictionary of resource limits to set.
        
    Returns:
        None
    """
    if limits is None:
        limits = DEFAULT_RESOURCE_LIMITS
    
    # Set CPU time limit
    if 'CPU_TIME' in limits:
        resource.setrlimit(resource.RLIMIT_CPU, (limits['CPU_TIME'], limits['CPU_TIME']))
    
    # Set memory limit
    if 'MEMORY' in limits:
        resource.setrlimit(resource.RLIMIT_AS, (limits['MEMORY'], limits['MEMORY']))
    
    # Set open files limit
    if 'FILES' in limits:
        resource.setrlimit(resource.RLIMIT_NOFILE, (limits['FILES'], limits['FILES']))

def run_in_sandbox(func, *args, **kwargs):
    """
    Run a function in a sandboxed environment with resource limits.
    
    Args:
        func: The function to run.
        *args: Arguments to pass to the function.
        **kwargs: Keyword arguments to pass to the function.
        
    Returns:
        The result of the function.
    """
    # Create a new process to run the function
    result = [None]
    error = [None]
    
    def target():
        try:
            # Set resource limits
            set_resource_limits()
            
            # Run the function
            result[0] = func(*args, **kwargs)
        except Exception as e:
            error[0] = e
    
    # Start the process
    thread = threading.Thread(target=target)
    thread.daemon = True
    thread.start()
    
    # Wait for the process to finish
    start_time = time.time()
    while thread.is_alive():
        if time.time() - start_time > DEFAULT_TIMEOUT:
            logger.error(f"Function {func.__name__} timed out after {DEFAULT_TIMEOUT} seconds")
            return None
        time.sleep(0.1)
    
    # Check for errors
    if error[0] is not None:
        logger.error(f"Error in sandboxed function: {str(error[0])}")
        raise error[0]
    
    return result[0]

def rate_limit(max_requests, time_window):
    """
    Decorator to apply rate limiting to a route.
    
    Args:
        max_requests: Maximum number of requests allowed in the time window.
        time_window: Time window in seconds.
        
    Returns:
        The decorated function.
    """
    # Store request timestamps for each IP
    request_history = {}
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get the client IP
            client_ip = request.remote_addr
            
            # Initialize request history for this IP if needed
            if client_ip not in request_history:
                request_history[client_ip] = []
            
            # Get current time
            current_time = time.time()
            
            # Remove old requests from history
            request_history[client_ip] = [t for t in request_history[client_ip] 
                                         if current_time - t < time_window]
            
            # Check if rate limit is exceeded
            if len(request_history[client_ip]) >= max_requests:
                logger.warning(f"Rate limit exceeded for IP {client_ip}")
                abort(429)  # Too Many Requests
            
            # Add current request to history
            request_history[client_ip].append(current_time)
            
            # Call the original function
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator
