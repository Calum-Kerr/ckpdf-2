"""
Page Numbers Module

This module provides functionality for adding page numbers to PDF files.
It uses PyMuPDF (fitz) to add page numbers in various styles and positions.
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

def add_page_numbers(input_path, output_path, start_number=1, position='bottom-center', 
                     font_name='helv', font_size=10, color=(0, 0, 0), 
                     margin=36, prefix='', suffix='', pages='all'):
    """
    Add page numbers to a PDF file.
    
    Args:
        input_path (str): Path to the input PDF file.
        output_path (str): Path where the numbered PDF will be saved.
        start_number (int, optional): Number to start with. Defaults to 1.
        position (str, optional): Position of the page numbers. Options:
            'top-left', 'top-center', 'top-right',
            'bottom-left', 'bottom-center', 'bottom-right'.
            Defaults to 'bottom-center'.
        font_name (str, optional): Font to use. Defaults to 'helv'.
        font_size (int, optional): Font size in points. Defaults to 10.
        color (tuple, optional): RGB color tuple (0-255, 0-255, 0-255). Defaults to (0, 0, 0).
        margin (int, optional): Margin in points from the edge. Defaults to 36.
        prefix (str, optional): Text to add before the page number. Defaults to ''.
        suffix (str, optional): Text to add after the page number. Defaults to ''.
        pages (str, optional): String specifying which pages to number, e.g., '1,3,5-7' or 'all'.
            Defaults to 'all'.
    
    Returns:
        dict: A dictionary containing information about the operation:
            - 'input_page_count': Number of pages in the input PDF.
            - 'numbered_pages': List of page numbers that were numbered.
            - 'start_number': Number started with.
            - 'position': Position of the page numbers.
            - 'font': Font used.
            - 'font_size': Font size used.
    
    Raises:
        PDFProcessingError: If the operation fails.
    """
    try:
        # Validate input file
        if not os.path.exists(input_path):
            raise PDFProcessingError(f"Input file not found: {input_path}")
        
        # Validate position
        valid_positions = ['top-left', 'top-center', 'top-right', 
                          'bottom-left', 'bottom-center', 'bottom-right']
        if position not in valid_positions:
            raise PDFProcessingError(f"Invalid position: {position}. Valid positions: {', '.join(valid_positions)}")
        
        # Validate font
        valid_fonts = ['helv', 'tiro', 'cour', 'times']
        if font_name not in valid_fonts:
            raise PDFProcessingError(f"Invalid font: {font_name}. Valid fonts: {', '.join(valid_fonts)}")
        
        # Validate font size
        try:
            font_size = int(font_size)
            if font_size < 6 or font_size > 72:
                raise PDFProcessingError(f"Invalid font size: {font_size}. Valid range: 6-72")
        except ValueError:
            raise PDFProcessingError(f"Invalid font size: {font_size}. Must be an integer.")
        
        # Validate start number
        try:
            start_number = int(start_number)
            if start_number < 1:
                raise PDFProcessingError(f"Invalid start number: {start_number}. Must be at least 1.")
        except ValueError:
            raise PDFProcessingError(f"Invalid start number: {start_number}. Must be an integer.")
        
        # Validate color
        try:
            if not isinstance(color, tuple) or len(color) != 3:
                raise ValueError()
            for c in color:
                if not isinstance(c, int) or c < 0 or c > 255:
                    raise ValueError()
        except ValueError:
            raise PDFProcessingError(f"Invalid color: {color}. Must be a tuple of 3 integers (0-255).")
        
        # Normalize color to 0-1 range for PyMuPDF
        color = (color[0]/255, color[1]/255, color[2]/255)
        
        # Open the input PDF
        doc = fitz.open(input_path)
        
        # Get the input page count
        input_page_count = doc.page_count
        
        # Determine which pages to number
        pages_to_number = []
        if pages.lower() == 'all':
            # Number all pages
            pages_to_number = list(range(1, input_page_count + 1))
        else:
            # Parse the page ranges
            page_ranges = parse_page_ranges(pages, input_page_count)
            
            # Create a list of all pages to number
            for start, end in page_ranges:
                pages_to_number.extend(range(start, end + 1))
            
            # Remove duplicates and sort
            pages_to_number = sorted(set(pages_to_number))
        
        # Add page numbers to the specified pages
        current_number = start_number
        for page_num in pages_to_number:
            # Page numbers are 1-based in the input, but 0-based in PyMuPDF
            page = doc[page_num - 1]
            
            # Get page dimensions
            rect = page.rect
            
            # Determine the position of the page number
            x, y = get_position_coordinates(position, rect, margin)
            
            # Create the page number text
            text = f"{prefix}{current_number}{suffix}"
            
            # Add the page number directly using insert_text
            page.insert_text(
                point=(x, y),
                text=text,
                fontname=font_name,
                fontsize=font_size,
                color=color
            )
            
            # Increment the page number
            current_number += 1
        
        # Save the document
        doc.save(output_path, garbage=4, deflate=True)
        
        # Close the document
        doc.close()
        
        return {
            'input_page_count': input_page_count,
            'numbered_pages': pages_to_number,
            'start_number': start_number,
            'position': position,
            'font': font_name,
            'font_size': font_size
        }
    
    except PDFProcessingError:
        # Re-raise PDFProcessingError
        raise
    
    except Exception as e:
        logger.error(f"Error adding page numbers: {str(e)}")
        raise PDFProcessingError(f"Failed to add page numbers: {str(e)}")


def get_position_coordinates(position, rect, margin):
    """
    Get the coordinates for a given position on the page.
    
    Args:
        position (str): Position name ('top-left', 'bottom-center', etc.).
        rect (fitz.Rect): Page rectangle.
        margin (int): Margin in points from the edge.
    
    Returns:
        tuple: (x, y) coordinates for the position.
    """
    width = rect.width
    height = rect.height
    
    if position == 'top-left':
        return margin, margin
    elif position == 'top-center':
        return width / 2, margin
    elif position == 'top-right':
        return width - margin, margin
    elif position == 'bottom-left':
        return margin, height - margin
    elif position == 'bottom-center':
        return width / 2, height - margin
    elif position == 'bottom-right':
        return width - margin, height - margin
    else:
        # Default to bottom-center
        return width / 2, height - margin


def get_alignment(position):
    """
    Get the text alignment for a given position.
    
    Args:
        position (str): Position name ('top-left', 'bottom-center', etc.).
    
    Returns:
        int: Alignment value (0 = left, 1 = center, 2 = right).
    """
    if 'left' in position:
        return 0  # Left-aligned
    elif 'center' in position:
        return 1  # Center-aligned
    elif 'right' in position:
        return 2  # Right-aligned
    else:
        # Default to center
        return 1


def get_font_name(font_code):
    """
    Get the human-readable font name for a font code.
    
    Args:
        font_code (str): Font code ('helv', 'tiro', etc.).
    
    Returns:
        str: Human-readable font name.
    """
    font_names = {
        'helv': 'Helvetica',
        'tiro': 'Times Roman',
        'cour': 'Courier',
        'times': 'Times New Roman'
    }
    
    return font_names.get(font_code, font_code)


def get_position_name(position_code):
    """
    Get the human-readable position name for a position code.
    
    Args:
        position_code (str): Position code ('top-left', 'bottom-center', etc.).
    
    Returns:
        str: Human-readable position name.
    """
    position_names = {
        'top-left': 'Top Left',
        'top-center': 'Top Center',
        'top-right': 'Top Right',
        'bottom-left': 'Bottom Left',
        'bottom-center': 'Bottom Center',
        'bottom-right': 'Bottom Right'
    }
    
    return position_names.get(position_code, position_code)
