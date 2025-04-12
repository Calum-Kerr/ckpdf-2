"""
Setup script to download and extract Ghostscript.

This script downloads the Ghostscript source code and extracts it to the
ghostscript directory. It's useful for setting up the project on a new machine.
"""

import os
import sys
import platform
import subprocess
import tempfile
import shutil
from urllib.request import urlretrieve
import tarfile
import zipfile

# Ghostscript version and download URLs
GS_VERSION = "10.02.0"
GS_TAR_URL = f"https://github.com/ArtifexSoftware/ghostpdl-downloads/releases/download/gs10020/ghostscript-{GS_VERSION}.tar.gz"
GS_ZIP_URL = f"https://github.com/ArtifexSoftware/ghostpdl-downloads/releases/download/gs10020/ghostscript-{GS_VERSION}.zip"

def download_file(url, output_path):
    """
    Download a file from a URL to a local path.
    
    Args:
        url (str): The URL to download from.
        output_path (str): The local path to save the file to.
    """
    print(f"Downloading {url} to {output_path}...")
    urlretrieve(url, output_path)
    print("Download complete.")

def extract_archive(archive_path, output_dir):
    """
    Extract an archive file to a directory.
    
    Args:
        archive_path (str): The path to the archive file.
        output_dir (str): The directory to extract to.
    """
    print(f"Extracting {archive_path} to {output_dir}...")
    
    if archive_path.endswith('.tar.gz') or archive_path.endswith('.tgz'):
        with tarfile.open(archive_path, 'r:gz') as tar:
            tar.extractall(path=output_dir)
    elif archive_path.endswith('.zip'):
        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            zip_ref.extractall(output_dir)
    else:
        raise ValueError(f"Unsupported archive format: {archive_path}")
    
    print("Extraction complete.")

def setup_ghostscript():
    """
    Download and extract Ghostscript.
    """
    # Create ghostscript directory if it doesn't exist
    gs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ghostscript')
    os.makedirs(gs_dir, exist_ok=True)
    
    # Check if Ghostscript is already extracted
    gs_version_dir = os.path.join(gs_dir, f"ghostscript-{GS_VERSION}")
    if os.path.exists(gs_version_dir):
        print(f"Ghostscript {GS_VERSION} is already extracted to {gs_version_dir}")
        return
    
    # Create a temporary directory for downloading
    with tempfile.TemporaryDirectory() as temp_dir:
        # Determine which archive to download based on the platform
        if platform.system() == 'Windows':
            archive_url = GS_ZIP_URL
            archive_path = os.path.join(temp_dir, f"ghostscript-{GS_VERSION}.zip")
        else:
            archive_url = GS_TAR_URL
            archive_path = os.path.join(temp_dir, f"ghostscript-{GS_VERSION}.tar.gz")
        
        # Download the archive
        download_file(archive_url, archive_path)
        
        # Extract the archive
        extract_archive(archive_path, gs_dir)
    
    print(f"Ghostscript {GS_VERSION} has been set up successfully.")

def main():
    """
    Main function.
    """
    try:
        setup_ghostscript()
        return 0
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
