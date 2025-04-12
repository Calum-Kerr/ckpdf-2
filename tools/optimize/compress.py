"""
PDF Compression Module

This module provides functionality for compressing PDF files using Ghostscript.
It reduces the file size while maintaining acceptable quality.
"""

import os
import subprocess
import tempfile
import logging
import platform
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
        str: Path to the Ghostscript executable.

    Raises:
        PDFProcessingError: If Ghostscript is not found.
    """
    # First, try to use the local Ghostscript installation
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    gs_dir = os.path.join(base_dir, 'ghostscript')

    # Check if we have a local Ghostscript installation
    if os.path.exists(gs_dir):
        # Find the Ghostscript directory (it might have a version suffix)
        gs_dirs = [d for d in os.listdir(gs_dir) if d.startswith('ghostscript-')]

        if gs_dirs:
            # Use the first directory found (should be only one)
            gs_version_dir = os.path.join(gs_dir, gs_dirs[0])

            # Determine the executable name based on the platform
            if platform.system() == 'Windows':
                # On Windows, look for gswin64c.exe or gswin32c.exe in the bin directory
                for exe_name in ['gswin64c.exe', 'gswin32c.exe']:
                    exe_path = os.path.join(gs_version_dir, 'bin', exe_name)
                    if os.path.exists(exe_path):
                        return exe_path

                # If not found in bin, check the root directory
                for exe_name in ['gswin64c.exe', 'gswin32c.exe']:
                    exe_path = os.path.join(gs_version_dir, exe_name)
                    if os.path.exists(exe_path):
                        return exe_path
            else:
                # On Unix-like systems, look for gs in the bin directory
                exe_path = os.path.join(gs_version_dir, 'bin', 'gs')
                if os.path.exists(exe_path):
                    return exe_path

    # If local installation not found or executable not found, try system Ghostscript
    try:
        # Try to find Ghostscript in the system PATH
        if platform.system() == 'Windows':
            # On Windows, look for gswin64c.exe or gswin32c.exe
            for gs_name in ['gswin64c', 'gswin32c', 'gs']:
                try:
                    gs_path = subprocess.check_output(['where', gs_name], text=True).strip().split('\n')[0]
                    return gs_path
                except subprocess.CalledProcessError:
                    continue
        else:
            # On Unix-like systems, look for gs
            return subprocess.check_output(['which', 'gs'], text=True).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        # If Ghostscript is not found in the system PATH, raise an error
        raise PDFProcessingError("Ghostscript not found. Please install Ghostscript or check your PATH.")


def compress_pdf(input_path, output_path, compression_level='ebook'):
    """
    Compress a PDF file using Ghostscript.

    Args:
        input_path (str): Path to the input PDF file.
        output_path (str): Path where the compressed PDF will be saved.
        compression_level (str, optional): Compression level to use.
            Options: 'screen', 'ebook', 'printer', 'prepress', 'default'.
            Defaults to 'ebook'.

    Returns:
        dict: A dictionary containing information about the compression:
            - 'input_size': Size of the input file in bytes.
            - 'output_size': Size of the output file in bytes.
            - 'reduction_percent': Percentage of size reduction.

    Raises:
        PDFProcessingError: If the compression fails.
    """
    try:
        # Validate input file
        if not os.path.exists(input_path):
            raise PDFProcessingError(f"Input file not found: {input_path}")

        # Validate compression level
        valid_levels = ['screen', 'ebook', 'printer', 'prepress', 'default']
        if compression_level not in valid_levels:
            logger.warning(f"Invalid compression level: {compression_level}. Using 'ebook' instead.")
            compression_level = 'ebook'

        # Get input file size
        input_size = os.path.getsize(input_path)

        # Create a temporary directory for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Get the Ghostscript executable path
            try:
                gs_path = get_ghostscript_path()
            except PDFProcessingError as e:
                logger.error(f"Failed to find Ghostscript: {str(e)}")
                raise

            # Set up Ghostscript command
            gs_command = [
                gs_path,
                '-sDEVICE=pdfwrite',
                f'-dPDFSETTINGS=/{compression_level}',
                '-dCompatibilityLevel=1.4',
                '-dNOPAUSE',
                '-dQUIET',
                '-dBATCH',
                f'-sOutputFile={output_path}',
                input_path
            ]

            # Run Ghostscript
            logger.info(f"Running Ghostscript with compression level: {compression_level}")
            result = subprocess.run(gs_command, capture_output=True, text=True)

            # Check if the command was successful
            if result.returncode != 0:
                error_message = result.stderr.strip() if result.stderr else "Unknown error"
                logger.error(f"Ghostscript error: {error_message}")
                raise PDFProcessingError(f"Failed to compress PDF: {error_message}")

            # Check if the output file was created
            if not os.path.exists(output_path):
                logger.error("Output file was not created")
                raise PDFProcessingError("Failed to create output file")

            # Get output file size
            output_size = os.path.getsize(output_path)

            # Calculate size reduction
            size_reduction = input_size - output_size
            reduction_percent = (size_reduction / input_size) * 100 if input_size > 0 else 0

            logger.info(f"Compression complete. Input size: {input_size} bytes, Output size: {output_size} bytes, Reduction: {reduction_percent:.2f}%")

            # If the output file is larger than the input, use the input file instead
            if output_size > input_size:
                logger.warning("Compressed file is larger than the original. Using the original file instead.")
                os.remove(output_path)
                with open(input_path, 'rb') as input_file:
                    with open(output_path, 'wb') as output_file:
                        output_file.write(input_file.read())
                output_size = input_size
                reduction_percent = 0

            return {
                'input_size': input_size,
                'output_size': output_size,
                'reduction_percent': reduction_percent
            }

    except subprocess.SubprocessError as e:
        logger.error(f"Subprocess error: {str(e)}")
        raise PDFProcessingError(f"Failed to run Ghostscript: {str(e)}")

    except Exception as e:
        logger.error(f"Error compressing PDF: {str(e)}")
        raise PDFProcessingError(f"Failed to compress PDF: {str(e)}")


def get_compression_settings(compression_level):
    """
    Get the description and typical reduction for a compression level.

    Args:
        compression_level (str): The compression level.

    Returns:
        dict: A dictionary containing information about the compression level:
            - 'description': Description of the compression level.
            - 'typical_reduction': Typical reduction percentage.
    """
    settings = {
        'screen': {
            'description': 'Low quality, smallest file size. Suitable for screen viewing.',
            'typical_reduction': '70-90%'
        },
        'ebook': {
            'description': 'Medium quality, good file size. Suitable for ebooks.',
            'typical_reduction': '50-70%'
        },
        'printer': {
            'description': 'High quality, larger file size. Suitable for printing.',
            'typical_reduction': '30-50%'
        },
        'prepress': {
            'description': 'High quality with color preservation. Suitable for prepress.',
            'typical_reduction': '20-40%'
        },
        'default': {
            'description': 'Default quality settings from Ghostscript.',
            'typical_reduction': '40-60%'
        }
    }

    return settings.get(compression_level, settings['ebook'])
