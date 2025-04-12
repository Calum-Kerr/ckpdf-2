"""
Ghostscript integration for RevisePDF.

This package provides integration with Ghostscript for PDF processing tasks.
"""

import os
import sys
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Path to the Ghostscript executable
GHOSTSCRIPT_PATH = None

def find_ghostscript():
    """
    Find the Ghostscript executable in the package directory.
    
    Returns:
        str: Path to the Ghostscript executable, or None if not found.
    """
    global GHOSTSCRIPT_PATH
    
    if GHOSTSCRIPT_PATH is not None:
        return GHOSTSCRIPT_PATH
    
    # Get the directory of this package
    package_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Look for the Ghostscript executable
    if sys.platform == 'win32':
        # Windows
        gs_exe = os.path.join(package_dir, 'ghostscript-10.02.0', 'bin', 'gswin64c.exe')
        if os.path.exists(gs_exe):
            GHOSTSCRIPT_PATH = gs_exe
            return GHOSTSCRIPT_PATH
    else:
        # Unix-like systems
        gs_exe = os.path.join(package_dir, 'ghostscript-10.02.0', 'bin', 'gs')
        if os.path.exists(gs_exe):
            GHOSTSCRIPT_PATH = gs_exe
            return GHOSTSCRIPT_PATH
    
    # If we get here, we couldn't find the executable
    logger.warning("Ghostscript executable not found in package directory")
    return None
