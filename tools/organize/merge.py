"""
PDF Merge Module

This module provides functionality for merging multiple PDF files into a single PDF.
It uses PyMuPDF (fitz) to combine PDFs while preserving their content and structure.
"""

import os
import logging
import fitz  # PyMuPDF
from app.errors import PDFProcessingError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def merge_pdfs(input_paths, output_path, toc=True):
    """
    Merge multiple PDF files into a single PDF.
    
    Args:
        input_paths (list): List of paths to the input PDF files.
        output_path (str): Path where the merged PDF will be saved.
        toc (bool, optional): Whether to create a table of contents. Defaults to True.
    
    Returns:
        dict: A dictionary containing information about the merge:
            - 'input_count': Number of input files.
            - 'total_pages': Total number of pages in the merged PDF.
            - 'file_sizes': Dictionary mapping input file paths to their sizes in bytes.
            - 'output_size': Size of the output file in bytes.
    
    Raises:
        PDFProcessingError: If the merge fails.
    """
    try:
        # Validate input files
        if not input_paths:
            raise PDFProcessingError("No input files provided")
        
        for path in input_paths:
            if not os.path.exists(path):
                raise PDFProcessingError(f"Input file not found: {path}")
            
            # Check if the file is a valid PDF
            try:
                doc = fitz.open(path)
                doc.close()
            except Exception as e:
                raise PDFProcessingError(f"Invalid PDF file: {path} - {str(e)}")
        
        # Create a new PDF document
        merged_doc = fitz.open()
        
        # Track file sizes and total pages
        file_sizes = {}
        total_pages = 0
        toc_entries = []
        
        # Process each input file
        for path in input_paths:
            # Get file size
            file_sizes[path] = os.path.getsize(path)
            
            # Open the PDF
            doc = fitz.open(path)
            
            # Get the filename without extension for TOC
            filename = os.path.basename(path)
            filename = os.path.splitext(filename)[0]
            
            # Add TOC entry for this file
            if toc and doc.page_count > 0:
                toc_entries.append([1, filename, total_pages + 1])
            
            # Add pages from this document to the merged document
            merged_doc.insert_pdf(doc, from_page=0, to_page=doc.page_count-1)
            
            # Update total pages
            total_pages += doc.page_count
            
            # Close the document
            doc.close()
        
        # Set the table of contents if requested
        if toc and toc_entries:
            merged_doc.set_toc(toc_entries)
        
        # Save the merged document
        merged_doc.save(output_path)
        
        # Get output file size
        output_size = os.path.getsize(output_path)
        
        # Close the merged document
        merged_doc.close()
        
        return {
            'input_count': len(input_paths),
            'total_pages': total_pages,
            'file_sizes': file_sizes,
            'output_size': output_size
        }
    
    except PDFProcessingError:
        # Re-raise PDFProcessingError
        raise
    
    except Exception as e:
        logger.error(f"Error merging PDFs: {str(e)}")
        raise PDFProcessingError(f"Failed to merge PDFs: {str(e)}")


def get_pdf_info(pdf_path):
    """
    Get information about a PDF file.
    
    Args:
        pdf_path (str): Path to the PDF file.
    
    Returns:
        dict: A dictionary containing information about the PDF:
            - 'page_count': Number of pages in the PDF.
            - 'file_size': Size of the file in bytes.
            - 'metadata': Dictionary containing PDF metadata.
    
    Raises:
        PDFProcessingError: If the PDF cannot be opened or is invalid.
    """
    try:
        # Check if the file exists
        if not os.path.exists(pdf_path):
            raise PDFProcessingError(f"File not found: {pdf_path}")
        
        # Get file size
        file_size = os.path.getsize(pdf_path)
        
        # Open the PDF
        doc = fitz.open(pdf_path)
        
        # Get page count
        page_count = doc.page_count
        
        # Get metadata
        metadata = {
            'title': doc.metadata.get('title', ''),
            'author': doc.metadata.get('author', ''),
            'subject': doc.metadata.get('subject', ''),
            'keywords': doc.metadata.get('keywords', ''),
            'creator': doc.metadata.get('creator', ''),
            'producer': doc.metadata.get('producer', ''),
            'creation_date': doc.metadata.get('creationDate', ''),
            'modification_date': doc.metadata.get('modDate', '')
        }
        
        # Close the document
        doc.close()
        
        return {
            'page_count': page_count,
            'file_size': file_size,
            'metadata': metadata
        }
    
    except Exception as e:
        logger.error(f"Error getting PDF info: {str(e)}")
        raise PDFProcessingError(f"Failed to get PDF info: {str(e)}")
