"""
PDF to Image Module

This module provides functionality for converting PDF pages to images.
It uses PyMuPDF (fitz) to render PDF pages as images.
"""

import os
import logging
import fitz  # PyMuPDF
from PIL import Image
import io
import zipfile
from app.errors import PDFProcessingError
from tools.organize.split import parse_page_ranges

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def convert_pdf_to_images(input_path, output_dir, image_format='png', dpi=300, pages='all'):
    """
    Convert PDF pages to images.
    
    Args:
        input_path (str): Path to the input PDF file.
        output_dir (str): Directory where the images will be saved.
        image_format (str, optional): Format of the output images ('png', 'jpg', or 'tiff').
            Defaults to 'png'.
        dpi (int, optional): Resolution of the output images in DPI.
            Defaults to 300.
        pages (str, optional): String specifying which pages to convert, e.g., '1,3,5-7' or 'all'.
            Defaults to 'all'.
    
    Returns:
        dict: A dictionary containing information about the conversion:
            - 'input_page_count': Number of pages in the input PDF.
            - 'converted_pages': List of page numbers that were converted.
            - 'output_files': List of paths to the output image files.
            - 'image_format': Format of the output images.
            - 'dpi': Resolution of the output images in DPI.
    
    Raises:
        PDFProcessingError: If the conversion fails.
    """
    try:
        # Validate input file
        if not os.path.exists(input_path):
            raise PDFProcessingError(f"Input file not found: {input_path}")
        
        # Validate image format
        valid_formats = ['png', 'jpg', 'jpeg', 'tiff']
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
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Open the input PDF
        doc = fitz.open(input_path)
        
        # Get the input page count
        input_page_count = doc.page_count
        
        # Determine which pages to convert
        pages_to_convert = []
        if pages.lower() == 'all':
            # Convert all pages
            pages_to_convert = list(range(1, input_page_count + 1))
        else:
            # Parse the page ranges
            page_ranges = parse_page_ranges(pages, input_page_count)
            
            # Create a list of all pages to convert
            for start, end in page_ranges:
                pages_to_convert.extend(range(start, end + 1))
            
            # Remove duplicates and sort
            pages_to_convert = sorted(set(pages_to_convert))
        
        # Get the base filename without extension
        base_filename = os.path.basename(input_path)
        base_filename = os.path.splitext(base_filename)[0]
        
        # Convert the specified pages
        output_files = []
        for page_num in pages_to_convert:
            # Page numbers are 1-based in the input, but 0-based in PyMuPDF
            page = doc[page_num - 1]
            
            # Calculate the zoom factor based on DPI
            # 72 DPI is the base resolution in PyMuPDF
            zoom = dpi / 72
            
            # Get the page dimensions
            rect = page.rect
            
            # Create a matrix for rendering at the specified DPI
            mat = fitz.Matrix(zoom, zoom)
            
            # Render the page as a pixmap
            pix = page.get_pixmap(matrix=mat, alpha=False)
            
            # Generate output filename
            output_filename = f"{base_filename}_page_{page_num}.{image_format}"
            output_path = os.path.join(output_dir, output_filename)
            
            # Save the pixmap as an image
            if image_format.lower() == 'png':
                pix.save(output_path)
            else:
                # For other formats, convert using PIL
                img_data = pix.tobytes("ppm")  # Convert to PPM format
                img = Image.open(io.BytesIO(img_data))
                img.save(output_path, format=image_format.upper())
            
            # Add to output files list
            output_files.append(output_path)
        
        # Close the document
        doc.close()
        
        return {
            'input_page_count': input_page_count,
            'converted_pages': pages_to_convert,
            'output_files': output_files,
            'image_format': image_format,
            'dpi': dpi
        }
    
    except PDFProcessingError:
        # Re-raise PDFProcessingError
        raise
    
    except Exception as e:
        logger.error(f"Error converting PDF to images: {str(e)}")
        raise PDFProcessingError(f"Failed to convert PDF to images: {str(e)}")


def create_images_zip(image_paths, output_path):
    """
    Create a ZIP archive containing the specified images.
    
    Args:
        image_paths (list): List of paths to the image files.
        output_path (str): Path where the ZIP archive will be saved.
    
    Returns:
        str: Path to the ZIP archive.
    
    Raises:
        PDFProcessingError: If the ZIP creation fails.
    """
    try:
        # Create a ZIP file
        with zipfile.ZipFile(output_path, 'w') as zipf:
            # Add each image to the ZIP file
            for image_path in image_paths:
                # Get the filename without the path
                filename = os.path.basename(image_path)
                
                # Add the file to the ZIP
                zipf.write(image_path, filename)
        
        return output_path
    
    except Exception as e:
        logger.error(f"Error creating ZIP archive: {str(e)}")
        raise PDFProcessingError(f"Failed to create ZIP archive: {str(e)}")
