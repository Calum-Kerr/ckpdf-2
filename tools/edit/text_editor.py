import os
import logging
import fitz  # PyMuPDF
import base64
from app.errors import PDFProcessingError

# Configure logging
logger = logging.getLogger(__name__)

def get_pdf_preview(pdf_path, page_number):
    """
    Generate a preview image of a PDF page.

    Args:
        pdf_path (str): Path to the PDF file.
        page_number (int): Page number to preview (1-based).

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

        # Render the page to a PNG image
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better quality

        # Convert the pixmap to a PNG image
        img_data = pix.tobytes("png")

        # Encode the image as base64
        img_base64 = base64.b64encode(img_data).decode('utf-8')

        # Close the document
        doc.close()

        return img_base64

    except PDFProcessingError:
        # Re-raise PDFProcessingError
        raise

    except Exception as e:
        logger.error(f"Error generating PDF preview: {str(e)}")
        raise PDFProcessingError(f"Failed to generate PDF preview: {str(e)}")

def get_pdf_dimensions(pdf_path, page_number):
    """
    Get the dimensions of a PDF page.

    Args:
        pdf_path (str): Path to the PDF file.
        page_number (int): Page number (1-based).

    Returns:
        tuple: A tuple containing the width and height of the page in points.

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
        width, height = page.rect.width, page.rect.height

        # Close the document
        doc.close()

        return width, height

    except PDFProcessingError:
        # Re-raise PDFProcessingError
        raise

    except Exception as e:
        logger.error(f"Error getting PDF dimensions: {str(e)}")
        raise PDFProcessingError(f"Failed to get PDF dimensions: {str(e)}")

def extract_text_blocks(pdf_path, page_number):
    """
    Extract text blocks from a PDF page with their positions and attributes.

    Args:
        pdf_path (str): Path to the PDF file.
        page_number (int): Page number to extract text from (1-based).

    Returns:
        list: A list of dictionaries, each containing information about a text block:
            - 'text': The text content.
            - 'bbox': The bounding box coordinates [x0, y0, x1, y1].
            - 'font': The font name.
            - 'size': The font size.
            - 'color': The text color as RGB tuple.
            - 'block_type': The type of block ('paragraph', 'heading', etc.).

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

        # Extract text blocks with detailed information
        text_dict = page.get_text("dict")

        # Process the text blocks
        text_blocks = []

        # First, try to extract blocks directly
        for block in text_dict.get("blocks", []):
            if block.get("type") == 0:  # Text block
                # Collect all text in this block
                block_text = ""
                block_bbox = block.get("bbox", [0, 0, 0, 0])

                # Default attributes (will be overridden if we find better values)
                font_name = "helv"
                font_size = 12
                color = (0, 0, 0)

                # Process lines and spans to get the most common attributes
                spans_count = 0
                total_size = 0

                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        span_text = span.get("text", "")
                        block_text += span_text + " "

                        # Collect font information
                        if span.get("font"):
                            font_name = span.get("font")

                        if span.get("size"):
                            total_size += span.get("size")
                            spans_count += 1

                        if span.get("color"):
                            color = span.get("color")

                # Calculate average font size
                if spans_count > 0:
                    font_size = total_size / spans_count

                # Determine block type based on font size and position
                # This is a simple heuristic and can be improved
                block_type = "paragraph"
                if font_size > 14:
                    block_type = "heading"

                # Add the block to our list
                if block_text.strip():
                    text_blocks.append({
                        "text": block_text.strip(),
                        "bbox": block_bbox,
                        "font": font_name,
                        "size": font_size,
                        "color": color,
                        "block_type": block_type
                    })

        # If we didn't get any blocks, try a different approach
        if not text_blocks:
            # Try to extract text as HTML and parse it
            html = page.get_text("html")

            # For now, just extract text as a single block if we couldn't get proper blocks
            text = page.get_text("text")
            if text.strip():
                # Get page dimensions
                width, height = page.rect.width, page.rect.height

                # Create a single block with the entire page text
                text_blocks.append({
                    "text": text.strip(),
                    "bbox": [50, 50, width - 50, height - 50],  # Add some margin
                    "font": "helv",
                    "size": 12,
                    "color": (0, 0, 0),
                    "block_type": "paragraph"
                })

        # Close the document
        doc.close()

        # Log the number of blocks found
        logger.info(f"Extracted {len(text_blocks)} text blocks from page {page_number}")

        return text_blocks

    except PDFProcessingError:
        # Re-raise PDFProcessingError
        raise

    except Exception as e:
        logger.error(f"Error extracting text blocks: {str(e)}")
        raise PDFProcessingError(f"Failed to extract text blocks: {str(e)}")

def replace_text_in_pdf(input_path, output_path, text_blocks):
    """
    Replace text in a PDF based on the provided text blocks.

    Args:
        input_path (str): Path to the input PDF file.
        output_path (str): Path where the edited PDF will be saved.
        text_blocks (list): A list of dictionaries, each containing:
            - 'text': The new text content.
            - 'bbox': The bounding box coordinates [x0, y0, x1, y1].
            - 'font': The font name.
            - 'size': The font size.
            - 'color': The text color as RGB tuple.
            - 'page_number': The page number (1-based).

    Returns:
        dict: A dictionary containing information about the operation:
            - 'success': Boolean indicating if the operation was successful.
            - 'blocks_replaced': Number of text blocks replaced.

    Raises:
        PDFProcessingError: If the operation fails.
    """
    try:
        # Validate input file
        if not os.path.exists(input_path):
            raise PDFProcessingError(f"Input file not found: {input_path}")

        # Log input parameters for debugging
        logger.info(f"Replacing text in PDF: {input_path} -> {output_path}")
        logger.info(f"Number of text blocks to replace: {len(text_blocks)}")

        # Make a copy of the input file to the output path first
        import shutil
        shutil.copy2(input_path, output_path)

        # Open the output PDF for editing
        doc = fitz.open(output_path)

        # Track the number of blocks replaced
        blocks_replaced = 0

        # Group text blocks by page
        blocks_by_page = {}
        for block in text_blocks:
            page_number = block.get("page_number", 1)
            if page_number not in blocks_by_page:
                blocks_by_page[page_number] = []
            blocks_by_page[page_number].append(block)

        # Process each page
        for page_number, page_blocks in blocks_by_page.items():
            # Validate page number
            if not isinstance(page_number, int) or page_number < 1 or page_number > doc.page_count:
                logger.warning(f"Invalid page number: {page_number}. Skipping.")
                continue

            # Get the page (0-based index)
            page = doc[page_number - 1]

            # Process each block on this page
            for block in page_blocks:
                try:
                    # Get block information
                    bbox = block.get("bbox")
                    if not bbox or len(bbox) != 4:
                        logger.warning(f"Invalid bbox: {bbox}. Skipping block.")
                        continue

                    new_text = block.get("text", "")
                    font_name = block.get("font", "helv")
                    font_size = float(block.get("size", 12))

                    # Handle color - ensure it's a tuple of 3 floats
                    color_raw = block.get("color", (0, 0, 0))
                    if isinstance(color_raw, list):
                        color = tuple(color_raw)
                    else:
                        color = (0, 0, 0)  # Default to black

                    # Create a rectangle for the area to replace
                    rect = fitz.Rect(bbox)

                    # Log the block we're replacing
                    logger.info(f"Replacing block on page {page_number}: {new_text[:30]}... at {bbox}")

                    # First, remove the original text by covering it with a white rectangle
                    # Add padding to ensure complete coverage
                    padding = 5  # Increased padding for better coverage
                    expanded_rect = fitz.Rect(
                        rect.x0 - padding,
                        rect.y0 - padding,
                        rect.x1 + padding,
                        rect.y1 + padding
                    )
                    # Use opacity=1.0 to ensure complete coverage
                    # Draw multiple times to ensure complete coverage
                    for _ in range(3):  # Draw three times for better coverage
                        page.draw_rect(expanded_rect, color=(1, 1, 1), fill=(1, 1, 1), opacity=1.0)

                    # Then add the new text
                    text_writer = fitz.TextWriter(page.rect)

                    # Create a point for text insertion (top-left of the bbox)
                    point = fitz.Point(bbox[0], bbox[1] + font_size)  # Adjust y for baseline

                    # Get the font
                    try:
                        font = fitz.Font(font_name)
                    except Exception as font_error:
                        logger.warning(f"Error loading font {font_name}: {str(font_error)}. Using default font.")
                        font = fitz.Font("helv")

                    # Add text to the TextWriter
                    text_writer.append(point, new_text, font=font, fontsize=font_size, color=color)

                    # Apply the text to the page
                    text_writer.write_text(page)

                    blocks_replaced += 1

                except Exception as e:
                    logger.warning(f"Error replacing text block: {str(e)}")
                    continue

        # Save the document
        doc.save(output_path)

        # Close the document
        doc.close()

        logger.info(f"Successfully replaced {blocks_replaced} text blocks")

        return {
            'success': True,
            'blocks_replaced': blocks_replaced
        }

    except PDFProcessingError:
        # Re-raise PDFProcessingError
        raise

    except Exception as e:
        logger.error(f"Error replacing text in PDF: {str(e)}")
        raise PDFProcessingError(f"Failed to replace text in PDF: {str(e)}")
