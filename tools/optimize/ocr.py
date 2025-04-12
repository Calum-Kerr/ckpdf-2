"""
PDF OCR Module

This module provides functionality for performing OCR (Optical Character Recognition)
on PDF files. It extracts images from PDFs using PyMuPDF, runs Tesseract OCR on them,
and then overlays the recognized text back onto the PDF.
"""

import os
import subprocess
import tempfile
import logging
import platform
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
from app.errors import PDFProcessingError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_tesseract_path():
    """
    Get the path to the Tesseract executable.
    
    Returns:
        str: Path to the Tesseract executable.
    
    Raises:
        PDFProcessingError: If Tesseract is not found.
    """
    # Check if pytesseract has a custom path set
    if pytesseract.pytesseract.tesseract_cmd != 'tesseract':
        return pytesseract.pytesseract.tesseract_cmd
    
    # Try to find Tesseract in the system PATH
    try:
        if platform.system() == 'Windows':
            # On Windows, look for tesseract.exe
            try:
                tesseract_path = subprocess.check_output(['where', 'tesseract'], text=True).strip().split('\\n')[0]
                return tesseract_path
            except subprocess.CalledProcessError:
                # Check common installation locations
                common_paths = [
                    r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                    r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe'
                ]
                for path in common_paths:
                    if os.path.exists(path):
                        return path
        else:
            # On Unix-like systems, look for tesseract
            return subprocess.check_output(['which', 'tesseract'], text=True).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        # If Tesseract is not found in the system PATH, raise an error
        raise PDFProcessingError("Tesseract OCR not found. Please install Tesseract or check your PATH.")


def set_tesseract_path():
    """
    Set the path to the Tesseract executable for pytesseract.
    
    Raises:
        PDFProcessingError: If Tesseract is not found.
    """
    try:
        tesseract_path = get_tesseract_path()
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
    except PDFProcessingError:
        # If we can't find Tesseract, we'll let the error propagate when OCR is actually performed
        pass


def perform_ocr(input_path, output_path, language='eng'):
    """
    Perform OCR on a PDF file.
    
    Args:
        input_path (str): Path to the input PDF file.
        output_path (str): Path where the OCR'd PDF will be saved.
        language (str, optional): Language for OCR. Defaults to 'eng'.
    
    Returns:
        dict: A dictionary containing information about the OCR:
            - 'page_count': Number of pages processed.
            - 'text_found': Boolean indicating if text was found.
            - 'languages': List of languages used for OCR.
    
    Raises:
        PDFProcessingError: If the OCR fails.
    """
    try:
        # Validate input file
        if not os.path.exists(input_path):
            raise PDFProcessingError(f"Input file not found: {input_path}")
        
        # Set Tesseract path
        set_tesseract_path()
        
        # Validate language
        valid_languages = ['eng', 'fra', 'deu', 'spa', 'ita', 'por', 'rus', 'chi_sim', 'chi_tra', 'jpn', 'kor']
        if language not in valid_languages:
            logger.warning(f"Invalid language: {language}. Using 'eng' instead.")
            language = 'eng'
        
        # Create a temporary directory for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Open the input PDF
            input_doc = fitz.open(input_path)
            
            # Create a new PDF for output
            output_doc = fitz.open()
            
            # Process each page
            text_found = False
            for page_num in range(input_doc.page_count):
                # Get the page
                page = input_doc[page_num]
                
                # Check if the page already has text
                text = page.get_text("text")
                if text.strip():
                    # Page already has text, just copy it to the output
                    output_doc.insert_pdf(input_doc, from_page=page_num, to_page=page_num)
                    continue
                
                # Page doesn't have text, extract images and perform OCR
                text_found = True
                
                # Create a new page in the output document
                output_page = output_doc.new_page(width=page.rect.width, height=page.rect.height)
                
                # Copy the visual content from the input page to the output page
                output_page.show_pdf_page(output_page.rect, input_doc, page_num)
                
                # Extract images from the page
                image_list = page.get_images(full=True)
                
                for img_index, img_info in enumerate(image_list):
                    xref = img_info[0]  # Get the image reference
                    base_image = input_doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    
                    # Save the image to a temporary file
                    img_path = os.path.join(temp_dir, f"page_{page_num}_img_{img_index}.png")
                    with open(img_path, "wb") as img_file:
                        img_file.write(image_bytes)
                    
                    # Perform OCR on the image
                    try:
                        img = Image.open(img_path)
                        ocr_text = pytesseract.image_to_string(img, lang=language)
                        
                        if ocr_text.strip():
                            # Get the image position on the page
                            for img_rect in page.get_image_rects(xref):
                                # Add the OCR text as an invisible text layer
                                output_page.insert_text(
                                    img_rect.tl,  # Top-left point of the image
                                    ocr_text,
                                    fontsize=12,
                                    color=(0, 0, 0),
                                    opacity=0  # Make the text invisible (just for searching)
                                )
                    except Exception as e:
                        logger.warning(f"OCR failed for image {img_index} on page {page_num}: {str(e)}")
            
            # Save the output document
            output_doc.save(output_path)
            
            # Close the documents
            input_doc.close()
            output_doc.close()
            
            return {
                'page_count': input_doc.page_count,
                'text_found': text_found,
                'languages': [language]
            }
    
    except Exception as e:
        logger.error(f"Error performing OCR: {str(e)}")
        raise PDFProcessingError(f"Failed to perform OCR: {str(e)}")


def get_language_name(language_code):
    """
    Get the full name of a language from its code.
    
    Args:
        language_code (str): The language code.
    
    Returns:
        str: The full name of the language.
    """
    language_map = {
        'eng': 'English',
        'fra': 'French',
        'deu': 'German',
        'spa': 'Spanish',
        'ita': 'Italian',
        'por': 'Portuguese',
        'rus': 'Russian',
        'chi_sim': 'Chinese (Simplified)',
        'chi_tra': 'Chinese (Traditional)',
        'jpn': 'Japanese',
        'kor': 'Korean'
    }
    
    return language_map.get(language_code, language_code)
