"""
PDF Unlock Module

This module provides functionality for removing password protection from PDF files.
It uses PyMuPDF (fitz) to decrypt PDFs with the correct password.
"""

import os
import logging
import fitz  # PyMuPDF
from app.errors import PDFProcessingError
from tools.security.protect import check_pdf_encryption

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def unlock_pdf(input_path, output_path, password):
    """
    Remove password protection from a PDF file.
    
    Args:
        input_path (str): Path to the input PDF file.
        output_path (str): Path where the unlocked PDF will be saved.
        password (str): Password to unlock the PDF.
    
    Returns:
        dict: A dictionary containing information about the operation:
            - 'input_page_count': Number of pages in the input PDF.
            - 'was_encrypted': Whether the input PDF was encrypted.
            - 'encryption_method': The encryption method that was used.
            - 'permissions': Dictionary of permissions that were set.
    
    Raises:
        PDFProcessingError: If the operation fails.
    """
    try:
        # Validate input file
        if not os.path.exists(input_path):
            raise PDFProcessingError(f"Input file not found: {input_path}")
        
        # Check if the PDF is encrypted
        encryption_info = check_pdf_encryption(input_path)
        
        if not encryption_info['is_encrypted']:
            raise PDFProcessingError("The PDF is not encrypted and does not need to be unlocked")
        
        # Open the input PDF
        doc = fitz.open(input_path)
        
        # Get the input page count
        input_page_count = doc.page_count
        
        # Try to authenticate with the provided password
        if not doc.authenticate(password):
            doc.close()
            raise PDFProcessingError("Incorrect password. The PDF could not be unlocked.")
        
        # Save the document without encryption
        doc.save(output_path, encryption=0)  # 0 means no encryption
        
        # Close the document
        doc.close()
        
        return {
            'input_page_count': input_page_count,
            'was_encrypted': True,
            'encryption_method': encryption_info['encryption_method'],
            'permissions': encryption_info['permissions']
        }
    
    except PDFProcessingError:
        # Re-raise PDFProcessingError
        raise
    
    except Exception as e:
        logger.error(f"Error unlocking PDF: {str(e)}")
        raise PDFProcessingError(f"Failed to unlock PDF: {str(e)}")


def is_pdf_encrypted(pdf_path):
    """
    Check if a PDF file is encrypted.
    
    Args:
        pdf_path (str): Path to the PDF file.
    
    Returns:
        bool: True if the PDF is encrypted, False otherwise.
    
    Raises:
        PDFProcessingError: If the operation fails.
    """
    try:
        # Validate input file
        if not os.path.exists(pdf_path):
            raise PDFProcessingError(f"File not found: {pdf_path}")
        
        # Open the PDF
        doc = fitz.open(pdf_path)
        
        # Check if the PDF is encrypted
        is_encrypted = doc.is_encrypted
        
        # Close the document
        doc.close()
        
        return is_encrypted
    
    except PDFProcessingError:
        # Re-raise PDFProcessingError
        raise
    
    except Exception as e:
        logger.error(f"Error checking if PDF is encrypted: {str(e)}")
        raise PDFProcessingError(f"Failed to check if PDF is encrypted: {str(e)}")
