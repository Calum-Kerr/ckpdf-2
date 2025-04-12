"""
PDF Redaction Module

This module provides functionality for redacting sensitive information from PDF files.
It uses PyMuPDF (fitz) to permanently remove text and replace it with redaction marks.
"""

import os
import logging
import fitz  # PyMuPDF
import re
from app.errors import PDFProcessingError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def redact_pdf(input_path, output_path, search_text, case_sensitive=False, whole_words=True):
    """
    Redact text from a PDF file.
    
    Args:
        input_path (str): Path to the input PDF file.
        output_path (str): Path where the redacted PDF will be saved.
        search_text (str): Text to search for and redact.
        case_sensitive (bool, optional): Whether the search should be case-sensitive. Defaults to False.
        whole_words (bool, optional): Whether to match whole words only. Defaults to True.
    
    Returns:
        dict: A dictionary containing information about the operation:
            - 'input_page_count': Number of pages in the input PDF.
            - 'redacted_count': Number of text instances redacted.
            - 'pages_affected': List of page numbers where redactions were applied.
    
    Raises:
        PDFProcessingError: If the operation fails.
    """
    try:
        # Validate input file
        if not os.path.exists(input_path):
            raise PDFProcessingError(f"Input file not found: {input_path}")
        
        # Validate search text
        if not search_text:
            raise PDFProcessingError("Search text cannot be empty")
        
        # Open the input PDF
        doc = fitz.open(input_path)
        
        # Get the input page count
        input_page_count = doc.page_count
        
        # Track redaction statistics
        redacted_count = 0
        pages_affected = set()
        
        # Process each page
        for page_num in range(input_page_count):
            page = doc[page_num]
            
            # Search for text
            flags = 0
            if not case_sensitive:
                flags |= fitz.TEXT_DEHYPHENATE  # Ignore case
            if whole_words:
                flags |= fitz.TEXT_PRESERVE_WHITESPACE  # Match whole words
            
            # Find all instances of the search text
            instances = page.search_for(search_text, flags=flags)
            
            if instances:
                # Add page to affected pages
                pages_affected.add(page_num + 1)  # 1-based page numbers
                
                # Count redactions
                redacted_count += len(instances)
                
                # Create redaction annotations
                for inst in instances:
                    # Add some padding to ensure complete coverage
                    redact_rect = inst.irect  # Integer rectangle
                    redact_rect.x0 -= 2
                    redact_rect.y0 -= 2
                    redact_rect.x1 += 2
                    redact_rect.y1 += 2
                    
                    # Create redaction annotation
                    annot = page.add_redact_annot(redact_rect)
                    
                    # Set appearance properties (black redaction marks)
                    annot.set_colors(stroke=(0, 0, 0), fill=(0, 0, 0))
                    annot.update()
                
                # Apply redactions
                page.apply_redactions()
        
        # Save the document
        doc.save(output_path)
        
        # Close the document
        doc.close()
        
        return {
            'input_page_count': input_page_count,
            'redacted_count': redacted_count,
            'pages_affected': sorted(pages_affected)
        }
    
    except PDFProcessingError:
        # Re-raise PDFProcessingError
        raise
    
    except Exception as e:
        logger.error(f"Error redacting PDF: {str(e)}")
        raise PDFProcessingError(f"Failed to redact PDF: {str(e)}")


def redact_pattern(input_path, output_path, pattern, case_sensitive=False):
    """
    Redact text matching a regular expression pattern from a PDF file.
    
    Args:
        input_path (str): Path to the input PDF file.
        output_path (str): Path where the redacted PDF will be saved.
        pattern (str): Regular expression pattern to match text for redaction.
        case_sensitive (bool, optional): Whether the pattern matching should be case-sensitive. Defaults to False.
    
    Returns:
        dict: A dictionary containing information about the operation:
            - 'input_page_count': Number of pages in the input PDF.
            - 'redacted_count': Number of text instances redacted.
            - 'pages_affected': List of page numbers where redactions were applied.
    
    Raises:
        PDFProcessingError: If the operation fails.
    """
    try:
        # Validate input file
        if not os.path.exists(input_path):
            raise PDFProcessingError(f"Input file not found: {input_path}")
        
        # Validate pattern
        if not pattern:
            raise PDFProcessingError("Pattern cannot be empty")
        
        # Compile the regular expression
        try:
            if case_sensitive:
                regex = re.compile(pattern)
            else:
                regex = re.compile(pattern, re.IGNORECASE)
        except re.error as e:
            raise PDFProcessingError(f"Invalid regular expression pattern: {str(e)}")
        
        # Open the input PDF
        doc = fitz.open(input_path)
        
        # Get the input page count
        input_page_count = doc.page_count
        
        # Track redaction statistics
        redacted_count = 0
        pages_affected = set()
        
        # Process each page
        for page_num in range(input_page_count):
            page = doc[page_num]
            
            # Extract text with its positions
            text_page = page.get_textpage()
            blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]
            
            # Find all matches in the text
            redactions_on_page = []
            
            for block in blocks:
                if block["type"] == 0:  # Text block
                    for line in block["lines"]:
                        for span in line["spans"]:
                            text = span["text"]
                            matches = list(regex.finditer(text))
                            
                            if matches:
                                # Get the span's rectangle
                                span_rect = fitz.Rect(span["bbox"])
                                
                                # Calculate character width (approximate)
                                char_width = span_rect.width / len(text) if len(text) > 0 else 0
                                
                                # Add redactions for each match
                                for match in matches:
                                    start, end = match.span()
                                    
                                    # Calculate the rectangle for this match
                                    match_rect = fitz.Rect(
                                        span_rect.x0 + start * char_width,
                                        span_rect.y0,
                                        span_rect.x0 + end * char_width,
                                        span_rect.y1
                                    )
                                    
                                    # Add some padding
                                    match_rect.x0 -= 2
                                    match_rect.y0 -= 2
                                    match_rect.x1 += 2
                                    match_rect.y1 += 2
                                    
                                    redactions_on_page.append(match_rect)
            
            # Apply redactions if any were found
            if redactions_on_page:
                # Add page to affected pages
                pages_affected.add(page_num + 1)  # 1-based page numbers
                
                # Count redactions
                redacted_count += len(redactions_on_page)
                
                # Create redaction annotations
                for rect in redactions_on_page:
                    annot = page.add_redact_annot(rect)
                    annot.set_colors(stroke=(0, 0, 0), fill=(0, 0, 0))
                    annot.update()
                
                # Apply redactions
                page.apply_redactions()
        
        # Save the document
        doc.save(output_path)
        
        # Close the document
        doc.close()
        
        return {
            'input_page_count': input_page_count,
            'redacted_count': redacted_count,
            'pages_affected': sorted(pages_affected)
        }
    
    except PDFProcessingError:
        # Re-raise PDFProcessingError
        raise
    
    except Exception as e:
        logger.error(f"Error redacting PDF with pattern: {str(e)}")
        raise PDFProcessingError(f"Failed to redact PDF with pattern: {str(e)}")


def get_common_patterns():
    """
    Get a dictionary of common patterns for redaction.
    
    Returns:
        dict: A dictionary mapping pattern names to regular expressions.
    """
    return {
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'phone': r'\b(\+\d{1,2}\s?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b',
        'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
        'credit_card': r'\b(?:\d{4}[- ]?){3}\d{4}\b',
        'date': r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
        'ip_address': r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
        'url': r'\bhttps?://[^\s<>"]+|www\.[^\s<>"]+\b'
    }
