"""
PDF to Panoramic Module

This module provides functionality for creating panoramic images from PDF pages.
It uses PyMuPDF (fitz) to render PDF pages and PIL to stitch them together.
"""

import os
import logging
import fitz  # PyMuPDF
from PIL import Image
import io
from app.errors import PDFProcessingError
from tools.organize.split import parse_page_ranges

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_panoramic_image(input_path, output_path, image_format='jpg', dpi=300, 
                          direction='horizontal', pages='all', spacing=0):
    """
    Create a panoramic image from PDF pages.
    
    Args:
        input_path (str): Path to the input PDF file.
        output_path (str): Path where the panoramic image will be saved.
        image_format (str, optional): Format of the output image ('jpg', 'png', or 'tiff').
            Defaults to 'jpg'.
        dpi (int, optional): Resolution of the output image in DPI.
            Defaults to 300.
        direction (str, optional): Direction to stitch pages ('horizontal' or 'vertical').
            Defaults to 'horizontal'.
        pages (str, optional): String specifying which pages to include, e.g., '1,3,5-7' or 'all'.
            Defaults to 'all'.
        spacing (int, optional): Spacing between pages in pixels.
            Defaults to 0.
    
    Returns:
        dict: A dictionary containing information about the operation:
            - 'input_page_count': Number of pages in the input PDF.
            - 'pages_used': List of page numbers that were used.
            - 'image_width': Width of the output image in pixels.
            - 'image_height': Height of the output image in pixels.
            - 'image_format': Format of the output image.
            - 'dpi': Resolution of the output image in DPI.
    
    Raises:
        PDFProcessingError: If the operation fails.
    """
    try:
        # Validate input file
        if not os.path.exists(input_path):
            raise PDFProcessingError(f"Input file not found: {input_path}")
        
        # Validate image format
        valid_formats = ['jpg', 'jpeg', 'png', 'tiff']
        if image_format.lower() not in valid_formats:
            raise PDFProcessingError(f"Invalid image format: {image_format}. Valid formats: {', '.join(valid_formats)}")
        
        # Normalize image format
        if image_format.lower() == 'jpeg':
            image_format = 'jpg'
        
        # Validate DPI
        try:
            dpi = int(dpi)
            if dpi < 72 or dpi > 600:
                raise PDFProcessingError(f"Invalid DPI: {dpi}. Valid range: 72-600")
        except ValueError:
            raise PDFProcessingError(f"Invalid DPI: {dpi}. Must be an integer.")
        
        # Validate direction
        valid_directions = ['horizontal', 'vertical']
        if direction.lower() not in valid_directions:
            raise PDFProcessingError(f"Invalid direction: {direction}. Valid directions: {', '.join(valid_directions)}")
        
        # Validate spacing
        try:
            spacing = int(spacing)
            if spacing < 0 or spacing > 100:
                raise PDFProcessingError(f"Invalid spacing: {spacing}. Valid range: 0-100")
        except ValueError:
            raise PDFProcessingError(f"Invalid spacing: {spacing}. Must be an integer.")
        
        # Open the input PDF
        doc = fitz.open(input_path)
        
        # Get the input page count
        input_page_count = doc.page_count
        
        # Determine which pages to include
        pages_to_include = []
        if pages.lower() == 'all':
            # Include all pages
            pages_to_include = list(range(1, input_page_count + 1))
        else:
            # Parse the page ranges
            page_ranges = parse_page_ranges(pages, input_page_count)
            
            # Create a list of all pages to include
            for start, end in page_ranges:
                pages_to_include.extend(range(start, end + 1))
            
            # Remove duplicates and sort
            pages_to_include = sorted(set(pages_to_include))
        
        # Calculate the zoom factor based on DPI
        # 72 DPI is the base resolution in PyMuPDF
        zoom = dpi / 72
        
        # Render each page as an image
        page_images = []
        for page_num in pages_to_include:
            # Page numbers are 1-based in the input, but 0-based in PyMuPDF
            page = doc[page_num - 1]
            
            # Get the page dimensions
            rect = page.rect
            
            # Create a matrix for rendering at the specified DPI
            mat = fitz.Matrix(zoom, zoom)
            
            # Render the page as a pixmap
            pix = page.get_pixmap(matrix=mat, alpha=False)
            
            # Convert to PIL Image
            img_data = pix.tobytes("ppm")  # Convert to PPM format
            img = Image.open(io.BytesIO(img_data))
            
            # Add to the list of page images
            page_images.append(img)
        
        # Close the document
        doc.close()
        
        # Create the panoramic image
        if not page_images:
            raise PDFProcessingError("No pages to include in the panoramic image")
        
        # Calculate the dimensions of the panoramic image
        if direction.lower() == 'horizontal':
            # Horizontal panorama
            width = sum(img.width for img in page_images) + spacing * (len(page_images) - 1)
            height = max(img.height for img in page_images)
            
            # Create a new image with the calculated dimensions
            panorama = Image.new('RGB', (width, height), (255, 255, 255))
            
            # Paste each page image into the panorama
            x_offset = 0
            for img in page_images:
                # Center vertically if the image is shorter than the panorama
                y_offset = (height - img.height) // 2
                
                # Paste the image
                panorama.paste(img, (x_offset, y_offset))
                
                # Update the offset for the next image
                x_offset += img.width + spacing
        
        else:
            # Vertical panorama
            width = max(img.width for img in page_images)
            height = sum(img.height for img in page_images) + spacing * (len(page_images) - 1)
            
            # Create a new image with the calculated dimensions
            panorama = Image.new('RGB', (width, height), (255, 255, 255))
            
            # Paste each page image into the panorama
            y_offset = 0
            for img in page_images:
                # Center horizontally if the image is narrower than the panorama
                x_offset = (width - img.width) // 2
                
                # Paste the image
                panorama.paste(img, (x_offset, y_offset))
                
                # Update the offset for the next image
                y_offset += img.height + spacing
        
        # Save the panoramic image
        if image_format.lower() == 'jpg':
            panorama.save(output_path, format='JPEG', quality=95)
        elif image_format.lower() == 'png':
            panorama.save(output_path, format='PNG')
        elif image_format.lower() == 'tiff':
            panorama.save(output_path, format='TIFF', compression='tiff_lzw')
        
        return {
            'input_page_count': input_page_count,
            'pages_used': pages_to_include,
            'image_width': panorama.width,
            'image_height': panorama.height,
            'image_format': image_format.upper(),
            'dpi': dpi
        }
    
    except PDFProcessingError:
        # Re-raise PDFProcessingError
        raise
    
    except Exception as e:
        logger.error(f"Error creating panoramic image: {str(e)}")
        raise PDFProcessingError(f"Failed to create panoramic image: {str(e)}")
