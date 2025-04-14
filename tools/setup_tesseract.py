"""
Tesseract OCR Setup Script

This script checks if Tesseract OCR is installed and available in the PATH.
If not, it attempts to use a bundled version of Tesseract included with the application.
"""

import os
import sys
import platform
import subprocess
import logging
import shutil
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def is_tesseract_in_path():
    """Check if Tesseract is available in the system PATH."""
    try:
        if platform.system() == 'Windows':
            subprocess.check_output(['where', 'tesseract'], stderr=subprocess.STDOUT, text=True)
        else:
            subprocess.check_output(['which', 'tesseract'], stderr=subprocess.STDOUT, text=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def check_bundled_tesseract():
    """Check if the bundled Tesseract is available."""
    base_dir = Path(__file__).resolve().parent.parent
    tesseract_dir = base_dir / 'tesseract'

    if platform.system() == 'Windows':
        tesseract_exe = tesseract_dir / 'bin' / 'tesseract.exe'
    else:
        tesseract_exe = tesseract_dir / 'bin' / 'tesseract'

    return tesseract_exe.exists()

def get_tesseract_path():
    """
    Get the path to the Tesseract executable.

    Returns:
        str: Path to the Tesseract executable or None if not found.
    """
    # First, check if Tesseract is in the system PATH
    if is_tesseract_in_path():
        try:
            if platform.system() == 'Windows':
                return subprocess.check_output(['where', 'tesseract'], stderr=subprocess.STDOUT, text=True).strip().split('\n')[0]
            else:
                return subprocess.check_output(['which', 'tesseract'], stderr=subprocess.STDOUT, text=True).strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

    # If not in PATH, check for bundled Tesseract
    base_dir = Path(__file__).resolve().parent.parent
    tesseract_dir = base_dir / 'tesseract'

    if platform.system() == 'Windows':
        tesseract_exe = tesseract_dir / 'bin' / 'tesseract.exe'
    else:
        tesseract_exe = tesseract_dir / 'bin' / 'tesseract'

    if tesseract_exe.exists():
        return str(tesseract_exe)

    # Check common installation locations on Windows
    if platform.system() == 'Windows':
        common_paths = [
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            # Add more potential paths here
            r'D:\Program Files\Tesseract-OCR\tesseract.exe',
            r'D:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            r'E:\Program Files\Tesseract-OCR\tesseract.exe',
            r'E:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            # Check for user-specific installations
            os.path.expanduser(r'~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'),
            os.path.expanduser(r'~\Tesseract-OCR\tesseract.exe')
        ]
        for path in common_paths:
            if os.path.exists(path):
                logger.info(f"Found Tesseract at: {path}")
                return path

    return None

def setup_tesseract_environment():
    """
    Set up the Tesseract environment.

    Returns:
        bool: True if Tesseract is available, False otherwise.
    """
    tesseract_path = get_tesseract_path()

    if tesseract_path:
        logger.info(f"Tesseract found at: {tesseract_path}")

        # Set environment variable for pytesseract
        os.environ['TESSERACT_CMD'] = tesseract_path

        # Set TESSDATA_PREFIX to our tessdata directory regardless of where Tesseract is found
        # This ensures we use our language data files
        base_dir = Path(__file__).resolve().parent.parent
        tesseract_dir = base_dir / 'tesseract'
        tessdata_dir = tesseract_dir / 'tessdata'

        if tessdata_dir.exists():
            os.environ['TESSDATA_PREFIX'] = str(tessdata_dir)
            logger.info(f"TESSDATA_PREFIX set to: {tessdata_dir}")
        else:
            # Try to find the tessdata directory relative to the Tesseract executable
            tesseract_exe_dir = Path(tesseract_path).parent
            possible_tessdata_dirs = [
                tesseract_exe_dir / 'tessdata',
                tesseract_exe_dir.parent / 'tessdata',
                tesseract_exe_dir.parent / 'share' / 'tessdata'
            ]

            for tessdata_dir in possible_tessdata_dirs:
                if tessdata_dir.exists():
                    os.environ['TESSDATA_PREFIX'] = str(tessdata_dir)
                    logger.info(f"TESSDATA_PREFIX set to: {tessdata_dir}")
                    break

        return True
    else:
        logger.warning("Tesseract OCR not found. OCR functionality will be limited.")
        return False

def download_language_data(lang_code):
    """
    Download language data for Tesseract.

    Args:
        lang_code (str): Language code (e.g., 'eng', 'fra', etc.)

    Returns:
        bool: True if successful, False otherwise.
    """
    base_dir = Path(__file__).resolve().parent.parent
    tessdata_dir = base_dir / 'tesseract' / 'tessdata'
    tessdata_dir.mkdir(parents=True, exist_ok=True)

    lang_file = tessdata_dir / f"{lang_code}.traineddata"

    if lang_file.exists():
        logger.info(f"Language data for {lang_code} already exists.")
        return True

    # URL for language data
    url = f"https://github.com/tesseract-ocr/tessdata/raw/main/{lang_code}.traineddata"

    try:
        import requests
        logger.info(f"Downloading language data for {lang_code}...")
        response = requests.get(url, stream=True)
        response.raise_for_status()

        with open(lang_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        logger.info(f"Language data for {lang_code} downloaded successfully.")
        return True
    except Exception as e:
        logger.error(f"Failed to download language data for {lang_code}: {str(e)}")
        return False

if __name__ == "__main__":
    # Check if Tesseract is available
    if setup_tesseract_environment():
        print("Tesseract OCR is available.")

        # Download English language data if using bundled Tesseract
        if check_bundled_tesseract():
            download_language_data('eng')
    else:
        print("Tesseract OCR is not available. OCR functionality will be limited.")
