"""
PDF Content Editing Module

This module provides functionality for editing content in PDF files.
It uses PyMuPDF (fitz) to add, edit, and remove text and images.
"""

import os
import logging
import fitz  # PyMuPDF
from PIL import Image
import io
import base64
import re
from app.errors import PDFProcessingError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def add_text_to_pdf(input_path, output_path, text, page_number, x, y,
                   font_name="helv", font_size=12, color=(0, 0, 0),
                   align="left", rotate=0):
    """
    Add text to a PDF file.

    Args:
        input_path (str): Path to the input PDF file.
        output_path (str): Path where the edited PDF will be saved.
        text (str): Text to add to the PDF.
        page_number (int): Page number where the text will be added (1-based).
        x (float): X-coordinate for the text position.
        y (float): Y-coordinate for the text position.
        font_name (str, optional): Font name. Defaults to "helv".
        font_size (int, optional): Font size. Defaults to 12.
        color (tuple, optional): RGB color tuple (0-1 range). Defaults to (0, 0, 0).
        align (str, optional): Text alignment ("left", "center", "right"). Defaults to "left".
        rotate (int, optional): Rotation angle in degrees. Defaults to 0.

    Returns:
        dict: A dictionary containing information about the operation:
            - 'input_page_count': Number of pages in the input PDF.
            - 'page_number': Page number where the text was added.
            - 'text': Text that was added.
            - 'position': (x, y) coordinates where the text was added.

    Raises:
        PDFProcessingError: If the operation fails.
    """
    try:
        # Validate input file
        if not os.path.exists(input_path):
            raise PDFProcessingError(f"Input file not found: {input_path}")

        # Validate page number
        if not isinstance(page_number, int) or page_number < 1:
            raise PDFProcessingError(f"Invalid page number: {page_number}. Must be a positive integer.")

        # Open the input PDF
        doc = fitz.open(input_path)

        # Get the input page count
        input_page_count = doc.page_count

        # Validate page number against page count
        if page_number > input_page_count:
            doc.close()
            raise PDFProcessingError(f"Page number {page_number} exceeds document length ({input_page_count} pages).")

        # Get the page (0-based index)
        page = doc[page_number - 1]

        # Validate alignment
        valid_alignments = ["left", "center", "right"]
        if align not in valid_alignments:
            align = "left"

        # Add text to the page
        text_writer = fitz.TextWriter(page.rect)

        # Create a point for text insertion
        point = fitz.Point(x, y)

        # Get the font
        font = fitz.Font(font_name)

        # Add text to the TextWriter
        text_writer.append(point, text, font=font, fontsize=font_size, color=color)

        # Apply the text to the page
        text_writer.write_text(page, morph=(page.rect.width/2, page.rect.height/2, rotate))

        # Save the document
        doc.save(output_path)

        # Close the document
        doc.close()

        return {
            'input_page_count': input_page_count,
            'page_number': page_number,
            'text': text,
            'position': (x, y)
        }

    except PDFProcessingError:
        # Re-raise PDFProcessingError
        raise

    except Exception as e:
        logger.error(f"Error adding text to PDF: {str(e)}")
        raise PDFProcessingError(f"Failed to add text to PDF: {str(e)}")


def add_image_to_pdf(input_path, output_path, image_path, page_number, x, y,
                    width=None, height=None, rotate=0):
    """
    Add an image to a PDF file.

    Args:
        input_path (str): Path to the input PDF file.
        output_path (str): Path where the edited PDF will be saved.
        image_path (str): Path to the image file to add.
        page_number (int): Page number where the image will be added (1-based).
        x (float): X-coordinate for the image position.
        y (float): Y-coordinate for the image position.
        width (float, optional): Width of the image. If None, uses the image's natural width.
        height (float, optional): Height of the image. If None, uses the image's natural height.
        rotate (int, optional): Rotation angle in degrees. Defaults to 0.

    Returns:
        dict: A dictionary containing information about the operation:
            - 'input_page_count': Number of pages in the input PDF.
            - 'page_number': Page number where the image was added.
            - 'image_size': (width, height) of the added image.
            - 'position': (x, y) coordinates where the image was added.

    Raises:
        PDFProcessingError: If the operation fails.
    """
    try:
        # Validate input file
        if not os.path.exists(input_path):
            raise PDFProcessingError(f"Input file not found: {input_path}")

        # Validate image file
        if not os.path.exists(image_path):
            raise PDFProcessingError(f"Image file not found: {image_path}")

        # Validate page number
        if not isinstance(page_number, int) or page_number < 1:
            raise PDFProcessingError(f"Invalid page number: {page_number}. Must be a positive integer.")

        # Open the input PDF
        doc = fitz.open(input_path)

        # Get the input page count
        input_page_count = doc.page_count

        # Validate page number against page count
        if page_number > input_page_count:
            doc.close()
            raise PDFProcessingError(f"Page number {page_number} exceeds document length ({input_page_count} pages).")

        # Get the page (0-based index)
        page = doc[page_number - 1]

        # Open and process the image
        img = Image.open(image_path)

        # Get image dimensions
        img_width, img_height = img.size

        # Calculate dimensions if not provided
        if width is None and height is None:
            # Use natural dimensions
            width = img_width
            height = img_height
        elif width is None:
            # Calculate width based on height to maintain aspect ratio
            width = img_width * (height / img_height)
        elif height is None:
            # Calculate height based on width to maintain aspect ratio
            height = img_height * (width / img_width)

        # Convert PIL Image to bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format=img.format)
        img_bytes.seek(0)

        # Insert the image
        rect = fitz.Rect(x, y, x + width, y + height)
        page.insert_image(rect, stream=img_bytes.read(), rotate=rotate)

        # Save the document
        doc.save(output_path)

        # Close the document
        doc.close()

        return {
            'input_page_count': input_page_count,
            'page_number': page_number,
            'image_size': (width, height),
            'position': (x, y)
        }

    except PDFProcessingError:
        # Re-raise PDFProcessingError
        raise

    except Exception as e:
        logger.error(f"Error adding image to PDF: {str(e)}")
        raise PDFProcessingError(f"Failed to add image to PDF: {str(e)}")


def remove_content_from_pdf(input_path, output_path, page_number, x1, y1, x2, y2):
    """
    Remove content from a rectangular area in a PDF file.

    Args:
        input_path (str): Path to the input PDF file.
        output_path (str): Path where the edited PDF will be saved.
        page_number (int): Page number where content will be removed (1-based).
        x1 (float): X-coordinate of the top-left corner of the rectangle.
        y1 (float): Y-coordinate of the top-left corner of the rectangle.
        x2 (float): X-coordinate of the bottom-right corner of the rectangle.
        y2 (float): Y-coordinate of the bottom-right corner of the rectangle.

    Returns:
        dict: A dictionary containing information about the operation:
            - 'input_page_count': Number of pages in the input PDF.
            - 'page_number': Page number where content was removed.
            - 'area': (x1, y1, x2, y2) coordinates of the removed area.

    Raises:
        PDFProcessingError: If the operation fails.
    """
    try:
        # Validate input file
        if not os.path.exists(input_path):
            raise PDFProcessingError(f"Input file not found: {input_path}")

        # Validate page number
        if not isinstance(page_number, int) or page_number < 1:
            raise PDFProcessingError(f"Invalid page number: {page_number}. Must be a positive integer.")

        # Open the input PDF
        doc = fitz.open(input_path)

        # Get the input page count
        input_page_count = doc.page_count

        # Validate page number against page count
        if page_number > input_page_count:
            doc.close()
            raise PDFProcessingError(f"Page number {page_number} exceeds document length ({input_page_count} pages).")

        # Get the page (0-based index)
        page = doc[page_number - 1]

        # Create a rectangle for the area to remove
        rect = fitz.Rect(x1, y1, x2, y2)

        # Add a white rectangle to cover the area with full opacity
        # Draw multiple times to ensure complete coverage
        for _ in range(3):  # Draw three times for better coverage
            page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1), opacity=1.0)

        # Save the document
        doc.save(output_path)

        # Close the document
        doc.close()

        return {
            'input_page_count': input_page_count,
            'page_number': page_number,
            'area': (x1, y1, x2, y2)
        }

    except PDFProcessingError:
        # Re-raise PDFProcessingError
        raise

    except Exception as e:
        logger.error(f"Error removing content from PDF: {str(e)}")
        raise PDFProcessingError(f"Failed to remove content from PDF: {str(e)}")


def get_pdf_dimensions(pdf_path, page_number=1):
    """
    Get the dimensions of a PDF page.

    Args:
        pdf_path (str): Path to the PDF file.
        page_number (int, optional): Page number to get dimensions for (1-based). Defaults to 1.

    Returns:
        tuple: (width, height) of the PDF page in points.

    Raises:
        PDFProcessingError: If the operation fails.
    """
    try:
        # Validate input file
        if not os.path.exists(pdf_path):
            raise PDFProcessingError(f"PDF file not found: {pdf_path}")

        # Validate page number
        if not isinstance(page_number, int) or page_number < 1:
            raise PDFProcessingError(f"Invalid page number: {page_number}. Must be a positive integer.")

        # Open the PDF
        doc = fitz.open(pdf_path)

        # Validate page number against page count
        if page_number > doc.page_count:
            doc.close()
            raise PDFProcessingError(f"Page number {page_number} exceeds document length ({doc.page_count} pages).")

        # Get the page (0-based index)
        page = doc[page_number - 1]

        # Get the page dimensions
        width = page.rect.width
        height = page.rect.height

        # Close the document
        doc.close()

        return (width, height)

    except PDFProcessingError:
        # Re-raise PDFProcessingError
        raise

    except Exception as e:
        logger.error(f"Error getting PDF dimensions: {str(e)}")
        raise PDFProcessingError(f"Failed to get PDF dimensions: {str(e)}")


def get_pdf_preview(pdf_path, page_number=1, dpi=150):
    """
    Generate a base64-encoded preview image of a PDF page.

    Args:
        pdf_path (str): Path to the PDF file.
        page_number (int, optional): Page number to preview (1-based). Defaults to 1.
        dpi (int, optional): Resolution of the preview image. Defaults to 150.

    Returns:
        str: Base64-encoded PNG image of the PDF page.

    Raises:
        PDFProcessingError: If the operation fails.
    """
    try:
        # Validate input file
        if not os.path.exists(pdf_path):
            raise PDFProcessingError(f"PDF file not found: {pdf_path}")

        # Validate page number
        if not isinstance(page_number, int) or page_number < 1:
            raise PDFProcessingError(f"Invalid page number: {page_number}. Must be a positive integer.")

        # Open the PDF
        doc = fitz.open(pdf_path)

        # Validate page number against page count
        if page_number > doc.page_count:
            doc.close()
            raise PDFProcessingError(f"Page number {page_number} exceeds document length ({doc.page_count} pages).")

        # Get the page (0-based index)
        page = doc[page_number - 1]

        # Calculate zoom factor based on DPI
        zoom = dpi / 72  # 72 DPI is the base resolution in PyMuPDF

        # Create a matrix for rendering at the specified DPI
        mat = fitz.Matrix(zoom, zoom)

        # Render the page as a pixmap
        pix = page.get_pixmap(matrix=mat, alpha=False)

        # Convert to PIL Image
        img_data = pix.tobytes("png")

        # Encode as base64
        base64_img = base64.b64encode(img_data).decode('utf-8')

        # Close the document
        doc.close()

        return base64_img

    except PDFProcessingError:
        # Re-raise PDFProcessingError
        raise

    except Exception as e:
        logger.error(f"Error generating PDF preview: {str(e)}")
        raise PDFProcessingError(f"Failed to generate PDF preview: {str(e)}")


def extract_text_from_area(pdf_path, page_number, x1, y1, x2, y2):
    """
    Extract text from a rectangular area in a PDF file.

    Args:
        pdf_path (str): Path to the PDF file.
        page_number (int): Page number to extract text from (1-based).
        x1 (float): X-coordinate of the top-left corner of the rectangle.
        y1 (float): Y-coordinate of the top-left corner of the rectangle.
        x2 (float): X-coordinate of the bottom-right corner of the rectangle.
        y2 (float): Y-coordinate of the bottom-right corner of the rectangle.

    Returns:
        str: Extracted text from the specified area.

    Raises:
        PDFProcessingError: If the operation fails.
    """
    try:
        # Validate input file
        if not os.path.exists(pdf_path):
            raise PDFProcessingError(f"PDF file not found: {pdf_path}")

        # Validate page number
        if not isinstance(page_number, int) or page_number < 1:
            raise PDFProcessingError(f"Invalid page number: {page_number}. Must be a positive integer.")

        # Open the PDF
        doc = fitz.open(pdf_path)

        # Validate page number against page count
        if page_number > doc.page_count:
            doc.close()
            raise PDFProcessingError(f"Page number {page_number} exceeds document length ({doc.page_count} pages).")

        # Get the page (0-based index)
        page = doc[page_number - 1]

        # Create a rectangle for the area to extract text from
        rect = fitz.Rect(x1, y1, x2, y2)

        # Extract text from the specified area
        text = page.get_text("text", clip=rect)

        # Close the document
        doc.close()

        return text

    except PDFProcessingError:
        # Re-raise PDFProcessingError
        raise

    except Exception as e:
        logger.error(f"Error extracting text from area: {str(e)}")
        raise PDFProcessingError(f"Failed to extract text from area: {str(e)}")


def extract_text_with_attributes(pdf_path, page_number, x1, y1, x2, y2):
    """
    Extract text and its attributes from a rectangular area in a PDF file.

    Args:
        pdf_path (str): Path to the PDF file.
        page_number (int): Page number to extract text from (1-based).
        x1 (float): X-coordinate of the top-left corner of the rectangle.
        y1 (float): Y-coordinate of the top-left corner of the rectangle.
        x2 (float): X-coordinate of the bottom-right corner of the rectangle.
        y2 (float): Y-coordinate of the bottom-right corner of the rectangle.

    Returns:
        dict: A dictionary containing the extracted text and its attributes:
            - 'text': The extracted text.
            - 'blocks': List of text blocks with their attributes.
            - 'rect': The rectangle coordinates used for extraction.

    Raises:
        PDFProcessingError: If the operation fails.
    """
    try:
        # Validate input file
        if not os.path.exists(pdf_path):
            raise PDFProcessingError(f"PDF file not found: {pdf_path}")

        # Validate page number
        if not isinstance(page_number, int) or page_number < 1:
            raise PDFProcessingError(f"Invalid page number: {page_number}. Must be a positive integer.")

        # Open the PDF
        doc = fitz.open(pdf_path)

        # Validate page number against page count
        if page_number > doc.page_count:
            doc.close()
            raise PDFProcessingError(f"Page number {page_number} exceeds document length ({doc.page_count} pages).")

        # Get the page (0-based index)
        page = doc[page_number - 1]

        # Get all text on the page with positions
        all_text_dict = page.get_text("dict")

        # Calculate the center point of the selection rectangle
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2

        # Find the closest text block to the click point
        closest_blocks = []
        closest_distance = float('inf')
        full_text = ""

        # Process all blocks to find the closest one
        for block in all_text_dict.get("blocks", []):
            if block.get("type") == 0:  # Text block
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        span_text = span.get("text", "").strip()
                        if not span_text:  # Skip empty spans
                            continue

                        # Get the bounding box of the span
                        bbox = span.get("bbox", [0, 0, 0, 0])

                        # Calculate the center of the span
                        span_center_x = (bbox[0] + bbox[2]) / 2
                        span_center_y = (bbox[1] + bbox[3]) / 2

                        # Calculate distance to the click point
                        distance = ((span_center_x - center_x) ** 2 + (span_center_y - center_y) ** 2) ** 0.5

                        # Check if this span is within or very close to the selection rectangle
                        is_close = (x1 <= span_center_x <= x2 and y1 <= span_center_y <= y2) or distance < 50

                        if is_close:
                            # If this is the closest span so far, clear the list and add this one
                            if distance < closest_distance:
                                closest_blocks = []
                                closest_distance = distance
                                full_text = span_text

                                # Extract span attributes
                                closest_blocks.append({
                                    "text": span_text,
                                    "font": span.get("font", ""),
                                    "size": span.get("size", 12),
                                    "color": span.get("color", (0, 0, 0)),
                                    "bbox": bbox,
                                    "origin": span.get("origin", [bbox[0], bbox[1]])
                                })

        # If no close blocks were found, try to get any text in the selection rectangle
        if not closest_blocks:
            rect = fitz.Rect(x1, y1, x2, y2)
            text_in_rect = page.get_text("text", clip=rect).strip()

            if text_in_rect:
                full_text = text_in_rect
                closest_blocks.append({
                    "text": text_in_rect,
                    "font": "helv",  # Default font
                    "size": 12,      # Default size
                    "color": (0, 0, 0),  # Default color (black)
                    "bbox": [x1, y1, x2, y2],
                    "origin": [x1, y1]
                })

        # Close the document
        doc.close()

        return {
            'text': full_text,
            'blocks': closest_blocks,
            'rect': [x1, y1, x2, y2]
        }

    except PDFProcessingError:
        # Re-raise PDFProcessingError
        raise

    except Exception as e:
        logger.error(f"Error extracting text with attributes: {str(e)}")
        raise PDFProcessingError(f"Failed to extract text with attributes: {str(e)}")


def get_all_text_with_positions(pdf_path, page_number):
    """
    Get all text on a page with their positions.

    Args:
        pdf_path (str): Path to the PDF file.
        page_number (int): Page number to extract text from (1-based).

    Returns:
        dict: A dictionary containing all text blocks with their positions.

    Raises:
        PDFProcessingError: If the operation fails.
    """
    try:
        # Validate input file
        if not os.path.exists(pdf_path):
            raise PDFProcessingError(f"PDF file not found: {pdf_path}")

        # Validate page number
        if not isinstance(page_number, int) or page_number < 1:
            raise PDFProcessingError(f"Invalid page number: {page_number}. Must be a positive integer.")

        # Open the PDF
        doc = fitz.open(pdf_path)

        # Validate page number against page count
        if page_number > doc.page_count:
            doc.close()
            raise PDFProcessingError(f"Page number {page_number} exceeds document length ({doc.page_count} pages).")

        # Get the page (0-based index)
        page = doc[page_number - 1]

        # Get all text on the page with positions
        text_dict = page.get_text("dict")

        # Process the text blocks
        text_blocks = []

        for block in text_dict.get("blocks", []):
            if block.get("type") == 0:  # Text block
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        span_text = span.get("text", "").strip()
                        if not span_text:  # Skip empty spans
                            continue

                        # Extract span attributes
                        text_blocks.append({
                            "text": span_text,
                            "font": span.get("font", ""),
                            "size": span.get("size", 12),
                            "color": span.get("color", (0, 0, 0)),
                            "bbox": span.get("bbox", [0, 0, 0, 0]),
                            "origin": span.get("origin", [0, 0])
                        })

        # Close the document
        doc.close()

        return {
            'blocks': text_blocks
        }

    except PDFProcessingError:
        # Re-raise PDFProcessingError
        raise

    except Exception as e:
        logger.error(f"Error getting text with positions: {str(e)}")
        raise PDFProcessingError(f"Failed to get text with positions: {str(e)}")


def replace_text_preserving_attributes(input_path, output_path, page_number, original_rect, new_text, text_attributes=None):
    """
    Replace text in a PDF while preserving its attributes.

    Args:
        input_path (str): Path to the input PDF file.
        output_path (str): Path where the edited PDF will be saved.
        page_number (int): Page number where the text will be replaced (1-based).
        original_rect (list): Rectangle coordinates [x1, y1, x2, y2] of the original text.
        new_text (str): New text to replace the original text.
        text_attributes (dict, optional): Attributes of the original text. If None, will use default attributes.
            Should contain 'font', 'size', 'color', and 'origin' keys.

    Returns:
        dict: A dictionary containing information about the operation:
            - 'page_number': Page number where the text was replaced.
            - 'original_rect': Rectangle coordinates of the original text.
            - 'new_text': The new text that replaced the original.

    Raises:
        PDFProcessingError: If the operation fails.
    """
    try:
        # Validate input file
        if not os.path.exists(input_path):
            raise PDFProcessingError(f"Input file not found: {input_path}")

        # Validate page number
        if not isinstance(page_number, int) or page_number < 1:
            raise PDFProcessingError(f"Invalid page number: {page_number}. Must be a positive integer.")

        # Open the input PDF
        doc = fitz.open(input_path)

        # Validate page number against page count
        if page_number > doc.page_count:
            doc.close()
            raise PDFProcessingError(f"Page number {page_number} exceeds document length ({doc.page_count} pages).")

        # Get the page (0-based index)
        page = doc[page_number - 1]

        # Parse the rectangle coordinates
        x1, y1, x2, y2 = original_rect
        rect = fitz.Rect(x1, y1, x2, y2)

        # First, remove the original text by covering it with a white rectangle
        # Add padding to ensure complete coverage
        padding = 2
        expanded_rect = fitz.Rect(
            rect.x0 - padding,
            rect.y0 - padding,
            rect.x1 + padding,
            rect.y1 + padding
        )
        # Use opacity=1.0 to ensure complete coverage
        page.draw_rect(expanded_rect, color=(1, 1, 1), fill=(1, 1, 1), opacity=1.0)

        # If text_attributes is provided, use them; otherwise, use defaults
        if text_attributes:
            font_name = text_attributes.get('font', 'helv')
            font_size = text_attributes.get('size', 12)
            color = text_attributes.get('color', (0, 0, 0))
            origin = text_attributes.get('origin', [x1, y1])
        else:
            font_name = 'helv'
            font_size = 12
            color = (0, 0, 0)
            origin = [x1, y1]

        # Create a text writer
        text_writer = fitz.TextWriter(page.rect)

        # Create a point for text insertion
        point = fitz.Point(origin[0], origin[1])

        # Get the font
        font = fitz.Font(font_name)

        # Add text to the TextWriter
        text_writer.append(point, new_text, font=font, fontsize=font_size, color=color)

        # Apply the text to the page
        text_writer.write_text(page)

        # Save the document
        doc.save(output_path)

        # Close the document
        doc.close()

        return {
            'page_number': page_number,
            'original_rect': original_rect,
            'new_text': new_text
        }

    except PDFProcessingError:
        # Re-raise PDFProcessingError
        raise

    except Exception as e:
        logger.error(f"Error replacing text: {str(e)}")
        raise PDFProcessingError(f"Failed to replace text: {str(e)}")


def get_available_fonts():
    """
    Get a list of available fonts for PDF editing.

    Returns:
        list: List of available font names.
    """
    # Standard PDF fonts
    standard_fonts = [
        "Helvetica", "Helvetica-Bold", "Helvetica-Oblique", "Helvetica-BoldOblique",
        "Times-Roman", "Times-Bold", "Times-Italic", "Times-BoldItalic",
        "Courier", "Courier-Bold", "Courier-Oblique", "Courier-BoldOblique",
        "Symbol", "ZapfDingbats"
    ]

    # PyMuPDF built-in fonts
    pymupdf_fonts = [
        "helv", "heit", "tiro", "tiit", "tibo", "tibi",
        "cour", "coit", "cobo", "cobi", "symb", "zadb"
    ]

    # Combine and return
    return standard_fonts + pymupdf_fonts
