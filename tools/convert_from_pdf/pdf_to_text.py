"""
PDF to Text Module

This module provides functionality for extracting text from PDF files.
It uses PyMuPDF (fitz) to extract text content from PDF pages.
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

def extract_text_from_pdf(input_path, output_path, pages='all', include_page_numbers=True):
    """
    Extract text from a PDF file.
    
    Args:
        input_path (str): Path to the input PDF file.
        output_path (str): Path where the extracted text will be saved.
        pages (str, optional): String specifying which pages to extract text from, e.g., '1,3,5-7' or 'all'.
            Defaults to 'all'.
        include_page_numbers (bool, optional): Whether to include page numbers in the output.
            Defaults to True.
    
    Returns:
        dict: A dictionary containing information about the extraction:
            - 'input_page_count': Number of pages in the input PDF.
            - 'extracted_pages': List of page numbers that were extracted.
            - 'text_length': Length of the extracted text in characters.
            - 'word_count': Approximate number of words in the extracted text.
    
    Raises:
        PDFProcessingError: If the extraction fails.
    """
    try:
        # Validate input file
        if not os.path.exists(input_path):
            raise PDFProcessingError(f"Input file not found: {input_path}")
        
        # Open the input PDF
        doc = fitz.open(input_path)
        
        # Get the input page count
        input_page_count = doc.page_count
        
        # Determine which pages to extract text from
        pages_to_extract = []
        if pages.lower() == 'all':
            # Extract text from all pages
            pages_to_extract = list(range(1, input_page_count + 1))
        else:
            # Parse the page ranges
            page_ranges = parse_page_ranges(pages, input_page_count)
            
            # Create a list of all pages to extract text from
            for start, end in page_ranges:
                pages_to_extract.extend(range(start, end + 1))
            
            # Remove duplicates and sort
            pages_to_extract = sorted(set(pages_to_extract))
        
        # Extract text from the specified pages
        extracted_text = ""
        word_count = 0
        
        for page_num in pages_to_extract:
            # Page numbers are 1-based in the input, but 0-based in PyMuPDF
            page = doc[page_num - 1]
            
            # Extract text from the page
            page_text = page.get_text()
            
            # Add page number if requested
            if include_page_numbers:
                extracted_text += f"--- Page {page_num} ---\n\n"
            
            # Add the page text
            extracted_text += page_text
            
            # Add a separator between pages
            if page_num != pages_to_extract[-1]:
                extracted_text += "\n\n"
            
            # Count words (approximate)
            word_count += len(page_text.split())
        
        # Save the extracted text to a file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(extracted_text)
        
        # Close the document
        doc.close()
        
        return {
            'input_page_count': input_page_count,
            'extracted_pages': pages_to_extract,
            'text_length': len(extracted_text),
            'word_count': word_count
        }
    
    except PDFProcessingError:
        # Re-raise PDFProcessingError
        raise
    
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        raise PDFProcessingError(f"Failed to extract text from PDF: {str(e)}")
