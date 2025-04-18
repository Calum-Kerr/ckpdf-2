"""
File validation and sanitization module.
This module provides functions to validate and sanitize uploaded files.
"""

import os
import magic
import hashlib
import logging
from werkzeug.utils import secure_filename
from flask import current_app
import fitz  # PyMuPDF

# Configure logging
logger = logging.getLogger(__name__)

# Maximum file size (50MB)
MAX_FILE_SIZE = 50 * 1024 * 1024

# Allowed file types and their corresponding MIME types
ALLOWED_MIME_TYPES = {
    'application/pdf': '.pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation': '.pptx',
    'image/jpeg': '.jpg',
    'image/png': '.png',
    'image/tiff': '.tiff',
    'text/plain': '.txt',
    'text/html': '.html',
}

def is_valid_file_size(file_stream):
    """
    Check if the file size is within the allowed limit.
    
    Args:
        file_stream: The file stream to check.
        
    Returns:
        bool: True if the file size is valid, False otherwise.
    """
    file_stream.seek(0, os.SEEK_END)
    file_size = file_stream.tell()
    file_stream.seek(0)  # Reset file pointer
    
    if file_size > MAX_FILE_SIZE:
        logger.warning(f"File size {file_size} exceeds maximum allowed size {MAX_FILE_SIZE}")
        return False
    
    return True

def get_file_mime_type(file_stream):
    """
    Determine the MIME type of a file using magic numbers.
    
    Args:
        file_stream: The file stream to check.
        
    Returns:
        str: The MIME type of the file.
    """
    file_stream.seek(0)
    mime = magic.Magic(mime=True)
    mime_type = mime.from_buffer(file_stream.read(2048))
    file_stream.seek(0)  # Reset file pointer
    return mime_type

def is_valid_file_type(file_stream, filename):
    """
    Check if the file type is allowed based on both extension and content.
    
    Args:
        file_stream: The file stream to check.
        filename: The original filename.
        
    Returns:
        bool: True if the file type is valid, False otherwise.
    """
    # Check MIME type
    mime_type = get_file_mime_type(file_stream)
    
    if mime_type not in ALLOWED_MIME_TYPES:
        logger.warning(f"Invalid MIME type: {mime_type}")
        return False
    
    # Check file extension
    _, file_extension = os.path.splitext(filename.lower())
    expected_extension = ALLOWED_MIME_TYPES.get(mime_type)
    
    if file_extension != expected_extension:
        logger.warning(f"File extension mismatch: {file_extension} vs {expected_extension}")
        return False
    
    return True

def sanitize_pdf(input_path, output_path):
    """
    Sanitize a PDF file by removing potentially harmful elements.
    
    Args:
        input_path: Path to the input PDF file.
        output_path: Path where the sanitized PDF will be saved.
        
    Returns:
        bool: True if sanitization was successful, False otherwise.
    """
    try:
        # Open the PDF
        doc = fitz.open(input_path)
        
        # Create a new PDF for the sanitized output
        sanitized_doc = fitz.open()
        
        # Process each page
        for page_num in range(doc.page_count):
            # Get the page
            page = doc[page_num]
            
            # Create a new page in the sanitized document
            new_page = sanitized_doc.new_page(width=page.rect.width, height=page.rect.height)
            
            # Copy the visual content from the original page
            new_page.show_pdf_page(new_page.rect, doc, page_num)
            
            # We don't copy any JavaScript, form fields, annotations, or links
        
        # Save the sanitized PDF
        sanitized_doc.save(output_path)
        
        # Close the documents
        doc.close()
        sanitized_doc.close()
        
        return True
    except Exception as e:
        logger.error(f"Error sanitizing PDF: {str(e)}")
        return False

def generate_secure_filename(filename):
    """
    Generate a secure filename that doesn't reveal the original name.
    
    Args:
        filename: The original filename.
        
    Returns:
        str: A secure filename.
    """
    # Get the file extension
    _, file_extension = os.path.splitext(filename.lower())
    
    # Generate a random hash based on filename and current time
    hash_base = f"{filename}{os.urandom(16).hex()}{os.getpid()}"
    file_hash = hashlib.sha256(hash_base.encode()).hexdigest()[:16]
    
    # Create a secure filename
    secure_name = f"{file_hash}{file_extension}"
    
    return secure_name

def validate_and_secure_file(file_stream, original_filename):
    """
    Validate and secure a file upload.
    
    Args:
        file_stream: The uploaded file stream.
        original_filename: The original filename.
        
    Returns:
        tuple: (is_valid, secure_filename, error_message)
    """
    # Check file size
    if not is_valid_file_size(file_stream):
        return False, None, "File size exceeds the maximum allowed limit."
    
    # Check file type
    if not is_valid_file_type(file_stream, original_filename):
        return False, None, "Invalid file type. Only PDF, Office documents, and images are allowed."
    
    # Generate a secure filename
    secure_name = generate_secure_filename(original_filename)
    
    return True, secure_name, None
