"""
Watermark Module

This module provides functionality for adding text watermarks to PDF files.
It uses PyMuPDF (fitz) to add watermarks in various styles and positions.
"""

import os
import logging
import fitz  # PyMuPDF
import math
from app.errors import PDFProcessingError
from tools.organize.split import parse_page_ranges

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def add_watermark(input_path, output_path, text, position='center', 
                  font_name='helv', font_size=36, opacity=0.3, 
                  rotation=45, color=(128, 128, 128), pages='all'):
    """
    Add a text watermark to a PDF file.
    
    Args:
        input_path (str): Path to the input PDF file.
        output_path (str): Path where the watermarked PDF will be saved.
        text (str): Text to use as watermark.
        position (str, optional): Position of the watermark. Options:
            'center', 'top', 'bottom', 'left', 'right',
            'top-left', 'top-right', 'bottom-left', 'bottom-right'.
            Defaults to 'center'.
        font_name (str, optional): Font to use. Defaults to 'helv'.
        font_size (int, optional): Font size in points. Defaults to 36.
        opacity (float, optional): Opacity of the watermark (0.0-1.0). Defaults to 0.3.
        rotation (int, optional): Rotation angle in degrees. Defaults to 45.
        color (tuple, optional): RGB color tuple (0-255, 0-255, 0-255). Defaults to (128, 128, 128).
        pages (str, optional): String specifying which pages to watermark, e.g., '1,3,5-7' or 'all'.
            Defaults to 'all'.
    
    Returns:
        dict: A dictionary containing information about the operation:
            - 'input_page_count': Number of pages in the input PDF.
            - 'watermarked_pages': List of page numbers that were watermarked.
            - 'watermark_text': Text used as watermark.
            - 'position': Position of the watermark.
            - 'opacity': Opacity of the watermark.
            - 'rotation': Rotation angle of the watermark.
    
    Raises:
        PDFProcessingError: If the operation fails.
    """
    try:
        # Validate input file
        if not os.path.exists(input_path):
            raise PDFProcessingError(f"Input file not found: {input_path}")
        
        # Validate text
        if not text:
            raise PDFProcessingError("Watermark text cannot be empty")
        
        # Validate position
        valid_positions = ['center', 'top', 'bottom', 'left', 'right',
                          'top-left', 'top-right', 'bottom-left', 'bottom-right']
        if position not in valid_positions:
            raise PDFProcessingError(f"Invalid position: {position}. Valid positions: {', '.join(valid_positions)}")
        
        # Validate font
        valid_fonts = ['helv', 'tiro', 'cour', 'times']
        if font_name not in valid_fonts:
            raise PDFProcessingError(f"Invalid font: {font_name}. Valid fonts: {', '.join(valid_fonts)}")
        
        # Validate font size
        try:
            font_size = int(font_size)
            if font_size < 6 or font_size > 144:
                raise PDFProcessingError(f"Invalid font size: {font_size}. Valid range: 6-144")
        except ValueError:
            raise PDFProcessingError(f"Invalid font size: {font_size}. Must be an integer.")
        
        # Validate opacity
        try:
            opacity = float(opacity)
            if opacity < 0.0 or opacity > 1.0:
                raise PDFProcessingError(f"Invalid opacity: {opacity}. Valid range: 0.0-1.0")
        except ValueError:
            raise PDFProcessingError(f"Invalid opacity: {opacity}. Must be a float.")
        
        # Validate rotation
        try:
            rotation = int(rotation)
            if rotation < 0 or rotation > 360:
                raise PDFProcessingError(f"Invalid rotation: {rotation}. Valid range: 0-360")
        except ValueError:
            raise PDFProcessingError(f"Invalid rotation: {rotation}. Must be an integer.")
        
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
        
        # Determine which pages to watermark
        pages_to_watermark = []
        if pages.lower() == 'all':
            # Watermark all pages
            pages_to_watermark = list(range(1, input_page_count + 1))
        else:
            # Parse the page ranges
            page_ranges = parse_page_ranges(pages, input_page_count)
            
            # Create a list of all pages to watermark
            for start, end in page_ranges:
                pages_to_watermark.extend(range(start, end + 1))
            
            # Remove duplicates and sort
            pages_to_watermark = sorted(set(pages_to_watermark))
        
        # Add watermark to the specified pages
        for page_num in pages_to_watermark:
            # Page numbers are 1-based in the input, but 0-based in PyMuPDF
            page = doc[page_num - 1]
            
            # Get page dimensions
            rect = page.rect
            width = rect.width
            height = rect.height
            
            # Create a new transparent page to overlay
            overlay = fitz.Page(doc, page_num - 1)
            
            # Determine the position of the watermark
            x, y = get_position_coordinates(position, rect)
            
            # Calculate font size based on page dimensions if needed
            if font_size == 0:  # Auto size
                # Use a size proportional to the page width
                font_size = int(min(width, height) / 10)
            
            # Create a text writer
            tw = fitz.TextWriter(overlay.rect)
            
            # Add the text
            tw.append(
                point=(x, y),
                text=text,
                fontname=font_name,
                fontsize=font_size,
                color=color,
                rotate=rotation
            )
            
            # Apply the text to the page with opacity
            overlay = tw.write_text(overlay, opacity=opacity)
            
            # Merge the overlay with the page
            page.show_pdf_page(
                rect=page.rect,
                src=doc,
                pno=page_num - 1,
                keep_proportion=True,
                overlay=overlay
            )
        
        # Save the document
        doc.save(output_path)
        
        # Close the document
        doc.close()
        
        return {
            'input_page_count': input_page_count,
            'watermarked_pages': pages_to_watermark,
            'watermark_text': text,
            'position': position,
            'opacity': opacity,
            'rotation': rotation
        }
    
    except PDFProcessingError:
        # Re-raise PDFProcessingError
        raise
    
    except Exception as e:
        logger.error(f"Error adding watermark: {str(e)}")
        raise PDFProcessingError(f"Failed to add watermark: {str(e)}")


def get_position_coordinates(position, rect):
    """
    Get the coordinates for a given position on the page.
    
    Args:
        position (str): Position name ('center', 'top-left', etc.).
        rect (fitz.Rect): Page rectangle.
    
    Returns:
        tuple: (x, y) coordinates for the position.
    """
    width = rect.width
    height = rect.height
    
    if position == 'center':
        return width / 2, height / 2
    elif position == 'top':
        return width / 2, height / 10
    elif position == 'bottom':
        return width / 2, height * 9 / 10
    elif position == 'left':
        return width / 10, height / 2
    elif position == 'right':
        return width * 9 / 10, height / 2
    elif position == 'top-left':
        return width / 10, height / 10
    elif position == 'top-right':
        return width * 9 / 10, height / 10
    elif position == 'bottom-left':
        return width / 10, height * 9 / 10
    elif position == 'bottom-right':
        return width * 9 / 10, height * 9 / 10
    else:
        # Default to center
        return width / 2, height / 2


def get_position_name(position_code):
    """
    Get the human-readable position name for a position code.
    
    Args:
        position_code (str): Position code ('center', 'top-left', etc.).
    
    Returns:
        str: Human-readable position name.
    """
    position_names = {
        'center': 'Center',
        'top': 'Top',
        'bottom': 'Bottom',
        'left': 'Left',
        'right': 'Right',
        'top-left': 'Top Left',
        'top-right': 'Top Right',
        'bottom-left': 'Bottom Left',
        'bottom-right': 'Bottom Right'
    }
    
    return position_names.get(position_code, position_code)
