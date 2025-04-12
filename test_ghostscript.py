"""
Test script to check if Ghostscript is properly set up.
"""

import os
import sys
import subprocess
from tools.optimize.compress import get_ghostscript_path

def main():
    """
    Test if Ghostscript is properly set up.
    """
    try:
        # Get the Ghostscript path
        gs_path = get_ghostscript_path()
        print(f"Ghostscript found at: {gs_path}")
        
        # Test Ghostscript by running a simple command
        result = subprocess.run([gs_path, "--version"], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"Ghostscript version: {result.stdout.strip()}")
            print("Ghostscript is working correctly!")
        else:
            print(f"Error running Ghostscript: {result.stderr}")
            return 1
        
        return 0
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
