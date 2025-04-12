"""
PDF Signature Module

This module provides functionality for adding signatures to PDF files.
It uses PyMuPDF (fitz) to add signature images to PDF documents.
"""

import os
import logging
import fitz  # PyMuPDF
from PIL import Image
import io
import base64
import re
from app.errors import PDFProcessingError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def add_signature_to_pdf(input_path, output_path, signature_path, page_number, x, y, 
                        width=None, height=None, rotate=0):
    """
    Add a signature image to a PDF file.
    
    Args:
        input_path (str): Path to the input PDF file.
        output_path (str): Path where the signed PDF will be saved.
        signature_path (str): Path to the signature image file.
        page_number (int): Page number where the signature will be added (1-based).
        x (float): X-coordinate for the signature position.
        y (float): Y-coordinate for the signature position.
        width (float, optional): Width of the signature. If None, uses the image's natural width.
        height (float, optional): Height of the signature. If None, uses the image's natural height.
        rotate (int, optional): Rotation angle in degrees. Defaults to 0.
    
    Returns:
        dict: A dictionary containing information about the operation:
            - 'input_page_count': Number of pages in the input PDF.
            - 'page_number': Page number where the signature was added.
            - 'signature_size': (width, height) of the added signature.
            - 'position': (x, y) coordinates where the signature was added.
    
    Raises:
        PDFProcessingError: If the operation fails.
    """
    try:
        # Validate input file
        if not os.path.exists(input_path):
            raise PDFProcessingError(f"Input file not found: {input_path}")
        
        # Validate signature file
        if not os.path.exists(signature_path):
            raise PDFProcessingError(f"Signature file not found: {signature_path}")
        
        # Validate page number
        if not isinstance(page_number, int) or page_number < 1:
            raise PDFProcessingError(f"Invalid page number: {page_number}. Must be a positive integer.")
        
        # Open the input PDF
        doc = fitz.open(input_path)
        
        # Get the input page count
        input_page_count = doc.page_count
        
        # Validate page number against page count
        if page_number > input_page_count:
            doc.close()
            raise PDFProcessingError(f"Page number {page_number} exceeds document length ({input_page_count} pages).")
        
        # Get the page (0-based index)
        page = doc[page_number - 1]
        
        # Open and process the signature image
        img = Image.open(signature_path)
        
        # Get image dimensions
        img_width, img_height = img.size
        
        # Calculate dimensions if not provided
        if width is None and height is None:
            # Use natural dimensions
            width = img_width
            height = img_height
        elif width is None:
            # Calculate width based on height to maintain aspect ratio
            width = img_width * (height / img_height)
        elif height is None:
            # Calculate height based on width to maintain aspect ratio
            height = img_height * (width / img_width)
        
        # Convert PIL Image to bytes
        img_bytes = io.BytesIO()
        
        # If the image has transparency (PNG), preserve it
        if 'A' in img.getbands():
            img.save(img_bytes, format='PNG')
        else:
            img.save(img_bytes, format=img.format if img.format else 'JPEG')
        
        img_bytes.seek(0)
        
        # Insert the signature image
        rect = fitz.Rect(x, y, x + width, y + height)
        page.insert_image(rect, stream=img_bytes.read(), rotate=rotate)
        
        # Save the document
        doc.save(output_path)
        
        # Close the document
        doc.close()
        
        return {
            'input_page_count': input_page_count,
            'page_number': page_number,
            'signature_size': (width, height),
            'position': (x, y)
        }
    
    except PDFProcessingError:
        # Re-raise PDFProcessingError
        raise
    
    except Exception as e:
        logger.error(f"Error adding signature to PDF: {str(e)}")
        raise PDFProcessingError(f"Failed to add signature to PDF: {str(e)}")


def add_signature_from_data_url(input_path, output_path, data_url, page_number, x, y, 
                               width=None, height=None, rotate=0):
    """
    Add a signature from a data URL to a PDF file.
    
    Args:
        input_path (str): Path to the input PDF file.
        output_path (str): Path where the signed PDF will be saved.
        data_url (str): Data URL of the signature image.
        page_number (int): Page number where the signature will be added (1-based).
        x (float): X-coordinate for the signature position.
        y (float): Y-coordinate for the signature position.
        width (float, optional): Width of the signature. If None, uses the image's natural width.
        height (float, optional): Height of the signature. If None, uses the image's natural height.
        rotate (int, optional): Rotation angle in degrees. Defaults to 0.
    
    Returns:
        dict: A dictionary containing information about the operation:
            - 'input_page_count': Number of pages in the input PDF.
            - 'page_number': Page number where the signature was added.
            - 'signature_size': (width, height) of the added signature.
            - 'position': (x, y) coordinates where the signature was added.
    
    Raises:
        PDFProcessingError: If the operation fails.
    """
    try:
        # Validate input file
        if not os.path.exists(input_path):
            raise PDFProcessingError(f"Input file not found: {input_path}")
        
        # Validate data URL
        if not data_url or not data_url.startswith('data:image/'):
            raise PDFProcessingError("Invalid signature data URL")
        
        # Extract the base64 data from the data URL
        match = re.match(r'data:image/(\w+);base64,(.+)', data_url)
        if not match:
            raise PDFProcessingError("Invalid signature data URL format")
        
        image_format, base64_data = match.groups()
        
        # Decode the base64 data
        try:
            image_data = base64.b64decode(base64_data)
        except Exception as e:
            raise PDFProcessingError(f"Failed to decode signature data: {str(e)}")
        
        # Create a temporary file for the signature image
        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{image_format}') as temp_file:
            temp_file.write(image_data)
            temp_file_path = temp_file.name
        
        try:
            # Add the signature to the PDF
            result = add_signature_to_pdf(input_path, output_path, temp_file_path, page_number, 
                                         x, y, width, height, rotate)
            
            # Return the result
            return result
        
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
    
    except PDFProcessingError:
        # Re-raise PDFProcessingError
        raise
    
    except Exception as e:
        logger.error(f"Error adding signature from data URL: {str(e)}")
        raise PDFProcessingError(f"Failed to add signature from data URL: {str(e)}")


def get_pdf_preview(pdf_path, page_number=1, dpi=150):
    """
    Generate a base64-encoded preview image of a PDF page.
    
    Args:
        pdf_path (str): Path to the PDF file.
        page_number (int, optional): Page number to preview (1-based). Defaults to 1.
        dpi (int, optional): Resolution of the preview image. Defaults to 150.
    
    Returns:
        str: Base64-encoded PNG image of the PDF page.
    
    Raises:
        PDFProcessingError: If the operation fails.
    """
    try:
        # Validate input file
        if not os.path.exists(pdf_path):
            raise PDFProcessingError(f"PDF file not found: {pdf_path}")
        
        # Validate page number
        if not isinstance(page_number, int) or page_number < 1:
            raise PDFProcessingError(f"Invalid page number: {page_number}. Must be a positive integer.")
        
        # Open the PDF
        doc = fitz.open(pdf_path)
        
        # Validate page number against page count
        if page_number > doc.page_count:
            doc.close()
            raise PDFProcessingError(f"Page number {page_number} exceeds document length ({doc.page_count} pages).")
        
        # Get the page (0-based index)
        page = doc[page_number - 1]
        
        # Calculate zoom factor based on DPI
        zoom = dpi / 72  # 72 DPI is the base resolution in PyMuPDF
        
        # Create a matrix for rendering at the specified DPI
        mat = fitz.Matrix(zoom, zoom)
        
        # Render the page as a pixmap
        pix = page.get_pixmap(matrix=mat, alpha=False)
        
        # Convert to PNG bytes
        img_bytes = pix.tobytes("png")
        
        # Encode as base64
        base64_img = base64.b64encode(img_bytes).decode('utf-8')
        
        # Close the document
        doc.close()
        
        return base64_img
    
    except PDFProcessingError:
        # Re-raise PDFProcessingError
        raise
    
    except Exception as e:
        logger.error(f"Error generating PDF preview: {str(e)}")
        raise PDFProcessingError(f"Failed to generate PDF preview: {str(e)}")


def get_pdf_dimensions(pdf_path, page_number=1):
    """
    Get the dimensions of a PDF page.
    
    Args:
        pdf_path (str): Path to the PDF file.
        page_number (int, optional): Page number to get dimensions for (1-based). Defaults to 1.
    
    Returns:
        tuple: (width, height) of the PDF page in points.
    
    Raises:
        PDFProcessingError: If the operation fails.
    """
    try:
        # Validate input file
        if not os.path.exists(pdf_path):
            raise PDFProcessingError(f"PDF file not found: {pdf_path}")
        
        # Validate page number
        if not isinstance(page_number, int) or page_number < 1:
            raise PDFProcessingError(f"Invalid page number: {page_number}. Must be a positive integer.")
        
        # Open the PDF
        doc = fitz.open(pdf_path)
        
        # Validate page number against page count
        if page_number > doc.page_count:
            doc.close()
            raise PDFProcessingError(f"Page number {page_number} exceeds document length ({doc.page_count} pages).")
        
        # Get the page (0-based index)
        page = doc[page_number - 1]
        
        # Get the page dimensions
        width = page.rect.width
        height = page.rect.height
        
        # Close the document
        doc.close()
        
        return (width, height)
    
    except PDFProcessingError:
        # Re-raise PDFProcessingError
        raise
    
    except Exception as e:
        logger.error(f"Error getting PDF dimensions: {str(e)}")
        raise PDFProcessingError(f"Failed to get PDF dimensions: {str(e)}")


# Add missing import
import tempfile
