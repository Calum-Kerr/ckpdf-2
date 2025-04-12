"""
Ghostscript Utilities Module

This module provides utility functions for working with Ghostscript.
"""

import os
import platform
import subprocess
import logging
import glob
from app.errors import PDFProcessingError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_ghostscript_path():
    """
    Get the path to the Ghostscript executable.
    
    Returns:
        str: Path to the Ghostscript executable, or None if not found.
    """
    # Check if Ghostscript is in the project directory
    project_gs_path = get_project_ghostscript_path()
    if project_gs_path:
        return project_gs_path
    
    # Check if Ghostscript is installed on the system
    system_gs_path = get_system_ghostscript_path()
    if system_gs_path:
        return system_gs_path
    
    return None


def get_project_ghostscript_path():
    """
    Get the path to the Ghostscript executable in the project directory.
    
    Returns:
        str: Path to the Ghostscript executable, or None if not found.
    """
    # Base directory for Ghostscript
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'ghostscript'))
    
    if not os.path.exists(base_dir):
        return None
    
    # Platform-specific executable name
    if platform.system() == 'Windows':
        # Look for gswin64c.exe or gswin32c.exe in bin directory
        for bit in ['64', '32']:
            gs_path = os.path.join(base_dir, 'bin', f'gswin{bit}c.exe')
            if os.path.exists(gs_path):
                return gs_path
        
        # If not found in bin, search in all subdirectories
        for gs_path in glob.glob(os.path.join(base_dir, '**', 'gswin*.exe'), recursive=True):
            if 'gswin64c.exe' in gs_path or 'gswin32c.exe' in gs_path:
                return gs_path
    
    elif platform.system() == 'Linux' or platform.system() == 'Darwin':
        # Look for gs in bin directory
        gs_path = os.path.join(base_dir, 'bin', 'gs')
        if os.path.exists(gs_path):
            return gs_path
        
        # If not found in bin, search in all subdirectories
        for gs_path in glob.glob(os.path.join(base_dir, '**', 'gs'), recursive=True):
            return gs_path
    
    return None


def get_system_ghostscript_path():
    """
    Get the path to the Ghostscript executable installed on the system.
    
    Returns:
        str: Path to the Ghostscript executable, or None if not found.
    """
    try:
        # Try to find Ghostscript in the system path
        if platform.system() == 'Windows':
            # Check for gswin64c.exe or gswin32c.exe
            for gs_name in ['gswin64c', 'gswin32c']:
                try:
                    result = subprocess.run(['where', gs_name], 
                                           stdout=subprocess.PIPE, 
                                           stderr=subprocess.PIPE, 
                                           text=True, 
                                           check=False)
                    if result.returncode == 0 and result.stdout.strip():
                        return result.stdout.strip().split('\n')[0]
                except:
                    pass
            
            # Check common installation paths
            program_files = os.environ.get('ProgramFiles', 'C:\\Program Files')
            program_files_x86 = os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)')
            
            for root_dir in [program_files, program_files_x86]:
                for gs_dir in glob.glob(os.path.join(root_dir, 'gs', '*')):
                    for bit in ['64', '32']:
                        gs_path = os.path.join(gs_dir, 'bin', f'gswin{bit}c.exe')
                        if os.path.exists(gs_path):
                            return gs_path
        
        elif platform.system() == 'Linux' or platform.system() == 'Darwin':
            # Check for gs in the system path
            result = subprocess.run(['which', 'gs'], 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE, 
                                   text=True, 
                                   check=False)
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
    
    except Exception as e:
        logger.warning(f"Error finding system Ghostscript: {str(e)}")
    
    return None


def check_ghostscript_version(gs_path):
    """
    Check the version of Ghostscript.
    
    Args:
        gs_path (str): Path to the Ghostscript executable.
    
    Returns:
        str: Ghostscript version string, or None if not found.
    """
    try:
        result = subprocess.run([gs_path, '--version'], 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE, 
                               text=True, 
                               check=False)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    
    except Exception as e:
        logger.warning(f"Error checking Ghostscript version: {str(e)}")
    
    return None
