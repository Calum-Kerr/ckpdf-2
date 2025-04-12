"""
PDF Rotation Module

This module provides functionality for rotating pages in a PDF file.
It uses PyMuPDF (fitz) to rotate pages and create a new PDF.
"""

import os
import logging
import fitz  # PyMuPDF
from app.errors import PDFProcessingError
from tools.organize.split import parse_page_ranges

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def rotate_pages(input_path, output_path, rotation, pages='all'):
    """
    Rotate pages in a PDF file.
    
    Args:
        input_path (str): Path to the input PDF file.
        output_path (str): Path where the rotated PDF will be saved.
        rotation (int): Rotation angle in degrees (90, 180, or 270).
        pages (str, optional): String specifying which pages to rotate, e.g., '1,3,5-7' or 'all'.
            Defaults to 'all'.
    
    Returns:
        dict: A dictionary containing information about the rotation:
            - 'input_page_count': Number of pages in the input PDF.
            - 'rotated_pages': List of page numbers that were rotated.
            - 'rotation_angle': Rotation angle in degrees.
    
    Raises:
        PDFProcessingError: If the rotation fails.
    """
    try:
        # Validate input file
        if not os.path.exists(input_path):
            raise PDFProcessingError(f"Input file not found: {input_path}")
        
        # Validate rotation angle
        try:
            rotation = int(rotation)
            if rotation not in [90, 180, 270]:
                raise PDFProcessingError(f"Invalid rotation angle: {rotation}. Valid angles: 90, 180, 270")
        except ValueError:
            raise PDFProcessingError(f"Invalid rotation angle: {rotation}. Must be an integer.")
        
        # Open the input PDF
        doc = fitz.open(input_path)
        
        # Get the input page count
        input_page_count = doc.page_count
        
        # Determine which pages to rotate
        pages_to_rotate = []
        if pages.lower() == 'all':
            # Rotate all pages
            pages_to_rotate = list(range(1, input_page_count + 1))
        else:
            # Parse the page ranges
            page_ranges = parse_page_ranges(pages, input_page_count)
            
            # Create a list of all pages to rotate
            for start, end in page_ranges:
                pages_to_rotate.extend(range(start, end + 1))
            
            # Remove duplicates and sort
            pages_to_rotate = sorted(set(pages_to_rotate))
        
        # Rotate the specified pages
        for page_num in pages_to_rotate:
            # Page numbers are 1-based in the input, but 0-based in PyMuPDF
            page = doc[page_num - 1]
            
            # Get the current rotation
            current_rotation = page.rotation
            
            # Calculate the new rotation
            new_rotation = (current_rotation + rotation) % 360
            
            # Set the new rotation
            page.set_rotation(new_rotation)
        
        # Save the document
        doc.save(output_path)
        
        # Close the document
        doc.close()
        
        return {
            'input_page_count': input_page_count,
            'rotated_pages': pages_to_rotate,
            'rotation_angle': rotation
        }
    
    except PDFProcessingError:
        # Re-raise PDFProcessingError
        raise
    
    except Exception as e:
        logger.error(f"Error rotating pages: {str(e)}")
        raise PDFProcessingError(f"Failed to rotate pages: {str(e)}")


def get_rotation_description(angle):
    """
    Get a human-readable description of a rotation angle.
    
    Args:
        angle (int): Rotation angle in degrees.
    
    Returns:
        str: Human-readable description of the rotation.
    """
    descriptions = {
        90: "90° Clockwise",
        180: "180°",
        270: "90° Counterclockwise (270°)"
    }
    
    return descriptions.get(angle, f"{angle}°")
