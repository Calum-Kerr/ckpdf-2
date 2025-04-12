"""
PDF Repair Module

This module provides functionality for repairing damaged or corrupted PDF files.
It uses PyMuPDF (fitz) for structure checks and rebuilds, with Ghostscript as a fallback.
"""

import os
import subprocess
import tempfile
import logging
import platform
import fitz  # PyMuPDF
from app.errors import PDFProcessingError
from tools.optimize.compress import get_ghostscript_path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def repair_pdf(input_path, output_path):
    """
    Repair a damaged or corrupted PDF file.
    
    This function attempts to repair a PDF file using PyMuPDF first,
    and falls back to Ghostscript if PyMuPDF fails.
    
    Args:
        input_path (str): Path to the input PDF file.
        output_path (str): Path where the repaired PDF will be saved.
    
    Returns:
        dict: A dictionary containing information about the repair:
            - 'method': The method used for repair ('pymupdf' or 'ghostscript').
            - 'errors_fixed': List of errors that were fixed (if available).
    
    Raises:
        PDFProcessingError: If the repair fails.
    """
    try:
        # Validate input file
        if not os.path.exists(input_path):
            raise PDFProcessingError(f"Input file not found: {input_path}")
        
        # Try to repair using PyMuPDF first
        try:
            errors_fixed = repair_with_pymupdf(input_path, output_path)
            return {
                'method': 'pymupdf',
                'errors_fixed': errors_fixed
            }
        except Exception as e:
            logger.warning(f"PyMuPDF repair failed: {str(e)}. Falling back to Ghostscript.")
            
            # Fall back to Ghostscript
            repair_with_ghostscript(input_path, output_path)
            return {
                'method': 'ghostscript',
                'errors_fixed': ['Unknown - Ghostscript does not provide detailed error information']
            }
    
    except Exception as e:
        logger.error(f"Error repairing PDF: {str(e)}")
        raise PDFProcessingError(f"Failed to repair PDF: {str(e)}")


def repair_with_pymupdf(input_path, output_path):
    """
    Repair a PDF file using PyMuPDF.
    
    Args:
        input_path (str): Path to the input PDF file.
        output_path (str): Path where the repaired PDF will be saved.
    
    Returns:
        list: A list of errors that were fixed.
    
    Raises:
        Exception: If the repair fails.
    """
    errors_fixed = []
    
    try:
        # Open the PDF with error recovery enabled
        doc = fitz.open(input_path)
        
        # Check for common issues
        if doc.is_encrypted:
            errors_fixed.append("Encrypted document")
            # Try to decrypt with empty password
            if doc.authenticate(""):
                errors_fixed.append("Successfully decrypted with empty password")
            else:
                raise PDFProcessingError("Cannot repair encrypted document without password")
        
        # Check for missing pages
        if doc.page_count == 0:
            errors_fixed.append("Document has no pages")
            raise PDFProcessingError("Cannot repair document with no pages")
        
        # Check each page for errors
        for page_num in range(doc.page_count):
            try:
                page = doc[page_num]
                # Force page access to check for errors
                _ = page.get_text("text")
            except Exception as e:
                errors_fixed.append(f"Page {page_num + 1} has errors: {str(e)}")
        
        # Save the repaired document
        doc.save(output_path, garbage=4, clean=True, deflate=True)
        doc.close()
        
        if not errors_fixed:
            errors_fixed.append("No specific errors found, but document was cleaned and optimized")
        
        return errors_fixed
    
    except Exception as e:
        logger.error(f"PyMuPDF repair error: {str(e)}")
        raise


def repair_with_ghostscript(input_path, output_path):
    """
    Repair a PDF file using Ghostscript.
    
    Args:
        input_path (str): Path to the input PDF file.
        output_path (str): Path where the repaired PDF will be saved.
    
    Raises:
        PDFProcessingError: If the repair fails.
    """
    try:
        # Get the Ghostscript executable path
        gs_path = get_ghostscript_path()
        
        # Set up Ghostscript command for repair
        # We use the pdfwrite device which will reinterpret and rebuild the PDF
        gs_command = [
            gs_path,
            '-sDEVICE=pdfwrite',
            '-dPDFSETTINGS=/prepress',  # Use prepress quality to preserve as much as possible
            '-dDetectDuplicateImages=true',
            '-dDownsampleMonoImages=false',
            '-dDownsampleGrayImages=false',
            '-dDownsampleColorImages=false',
            '-dAutoFilterColorImages=false',
            '-dAutoFilterGrayImages=false',
            '-dCompressFonts=false',
            '-dEmbedAllFonts=true',
            '-dSubsetFonts=false',
            '-dNOPAUSE',
            '-dQUIET',
            '-dBATCH',
            f'-sOutputFile={output_path}',
            input_path
        ]
        
        # Run Ghostscript
        logger.info("Running Ghostscript for PDF repair")
        result = subprocess.run(gs_command, capture_output=True, text=True)
        
        # Check if the command was successful
        if result.returncode != 0:
            error_message = result.stderr.strip() if result.stderr else "Unknown error"
            logger.error(f"Ghostscript error: {error_message}")
            raise PDFProcessingError(f"Failed to repair PDF with Ghostscript: {error_message}")
        
        # Check if the output file was created
        if not os.path.exists(output_path):
            logger.error("Output file was not created")
            raise PDFProcessingError("Failed to create output file")
        
    except subprocess.SubprocessError as e:
        logger.error(f"Subprocess error: {str(e)}")
        raise PDFProcessingError(f"Failed to run Ghostscript: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error repairing PDF with Ghostscript: {str(e)}")
        raise PDFProcessingError(f"Failed to repair PDF with Ghostscript: {str(e)}")


def check_pdf_structure(input_path):
    """
    Check the structure of a PDF file and identify potential issues.
    
    Args:
        input_path (str): Path to the input PDF file.
    
    Returns:
        dict: A dictionary containing information about the PDF structure:
            - 'is_valid': Boolean indicating if the PDF is valid.
            - 'issues': List of issues found in the PDF.
            - 'page_count': Number of pages in the PDF.
            - 'is_encrypted': Boolean indicating if the PDF is encrypted.
            - 'metadata': Dictionary containing PDF metadata.
    """
    issues = []
    metadata = {}
    is_valid = True
    
    try:
        # Open the PDF
        doc = fitz.open(input_path)
        
        # Check if the PDF is encrypted
        is_encrypted = doc.is_encrypted
        if is_encrypted:
            issues.append("PDF is encrypted")
            # Try to decrypt with empty password
            if doc.authenticate(""):
                issues.append("PDF can be decrypted with empty password")
            else:
                issues.append("PDF requires a password to decrypt")
                is_valid = False
        
        # Get page count
        page_count = doc.page_count
        if page_count == 0:
            issues.append("PDF has no pages")
            is_valid = False
        
        # Get metadata
        metadata = {
            'title': doc.metadata.get('title', ''),
            'author': doc.metadata.get('author', ''),
            'subject': doc.metadata.get('subject', ''),
            'keywords': doc.metadata.get('keywords', ''),
            'creator': doc.metadata.get('creator', ''),
            'producer': doc.metadata.get('producer', ''),
            'creation_date': doc.metadata.get('creationDate', ''),
            'modification_date': doc.metadata.get('modDate', '')
        }
        
        # Check each page for errors
        for page_num in range(page_count):
            try:
                page = doc[page_num]
                # Force page access to check for errors
                _ = page.get_text("text")
            except Exception as e:
                issues.append(f"Page {page_num + 1} has errors: {str(e)}")
                is_valid = False
        
        # Check for other common issues
        if doc.needs_pass:
            issues.append("PDF requires a password")
            is_valid = False
        
        doc.close()
        
        return {
            'is_valid': is_valid,
            'issues': issues,
            'page_count': page_count,
            'is_encrypted': is_encrypted,
            'metadata': metadata
        }
    
    except Exception as e:
        logger.error(f"Error checking PDF structure: {str(e)}")
        return {
            'is_valid': False,
            'issues': [f"Failed to open PDF: {str(e)}"],
            'page_count': 0,
            'is_encrypted': False,
            'metadata': {}
        }
