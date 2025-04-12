"""
PDF Extract Module

This module provides functionality for extracting specific pages from a PDF file.
It uses PyMuPDF (fitz) to extract pages and create a new PDF.
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

def extract_pages(input_path, output_path, pages):
    """
    Extract specific pages from a PDF file.
    
    Args:
        input_path (str): Path to the input PDF file.
        output_path (str): Path where the extracted PDF will be saved.
        pages (str): String specifying which pages to extract, e.g., '1,3,5-7'.
    
    Returns:
        dict: A dictionary containing information about the extraction:
            - 'input_page_count': Number of pages in the input PDF.
            - 'extracted_pages': List of page numbers that were extracted.
            - 'output_page_count': Number of pages in the output PDF.
    
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
        
        # Parse the page ranges
        page_ranges = parse_page_ranges(pages, input_page_count)
        
        # Create a list of all pages to extract
        pages_to_extract = []
        for start, end in page_ranges:
            pages_to_extract.extend(range(start, end + 1))
        
        # Remove duplicates and sort
        pages_to_extract = sorted(set(pages_to_extract))
        
        # Create a new PDF document
        new_doc = fitz.open()
        
        # Extract the specified pages
        for page_num in pages_to_extract:
            # Page numbers are 1-based in the input, but 0-based in PyMuPDF
            new_doc.insert_pdf(doc, from_page=page_num - 1, to_page=page_num - 1)
        
        # Save the new document
        new_doc.save(output_path)
        
        # Get the output page count
        output_page_count = new_doc.page_count
        
        # Close the documents
        doc.close()
        new_doc.close()
        
        return {
            'input_page_count': input_page_count,
            'extracted_pages': pages_to_extract,
            'output_page_count': output_page_count
        }
    
    except PDFProcessingError:
        # Re-raise PDFProcessingError
        raise
    
    except Exception as e:
        logger.error(f"Error extracting pages: {str(e)}")
        raise PDFProcessingError(f"Failed to extract pages: {str(e)}")


def format_page_list(pages):
    """
    Format a list of page numbers into a readable string.
    
    Args:
        pages (list): List of page numbers.
    
    Returns:
        str: Formatted string of page numbers.
    """
    if not pages:
        return ""
    
    # Sort the pages
    pages = sorted(pages)
    
    # Group consecutive pages
    groups = []
    current_group = [pages[0]]
    
    for i in range(1, len(pages)):
        if pages[i] == pages[i-1] + 1:
            current_group.append(pages[i])
        else:
            groups.append(current_group)
            current_group = [pages[i]]
    
    groups.append(current_group)
    
    # Format the groups
    formatted_groups = []
    for group in groups:
        if len(group) == 1:
            formatted_groups.append(str(group[0]))
        else:
            formatted_groups.append(f"{group[0]}-{group[-1]}")
    
    return ", ".join(formatted_groups)
