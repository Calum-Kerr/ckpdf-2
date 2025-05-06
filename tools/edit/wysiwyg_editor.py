"""
WYSIWYG PDF Editor Module

This module provides functionality for editing PDF text in a WYSIWYG manner.
It uses PyMuPDF (fitz) to modify text directly in the PDF.
"""

import os
import logging
import fitz  # PyMuPDF
import base64
from app.errors import PDFProcessingError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def modify_pdf_text(input_path, output_path, modifications):
    """
    Modify text in a PDF based on the provided modifications.

    Args:
        input_path (str): Path to the input PDF file.
        output_path (str): Path where the edited PDF will be saved.
        modifications (list): A list of dictionaries, each containing:
            - 'page': The page number (1-based).
            - 'index': The index of the text item.
            - 'originalText': The original text content.
            - 'newText': The new text content.
            - 'transform': The transform matrix for the text.
            - 'fontName': The font name.
            - 'fontSize': The original font size.
            - 'newFontSize': The new font size.

    Returns:
        dict: A dictionary containing information about the operation:
            - 'success': Boolean indicating if the operation was successful.
            - 'modifications_applied': Number of text modifications applied.
    """
    try:
        # Log input parameters for debugging
        logger.info(f"Modifying text in PDF: {input_path} -> {output_path}")
        logger.info(f"Number of modifications to apply: {len(modifications)}")

        # Make a copy of the input file to the output path first
        import shutil
        shutil.copy2(input_path, output_path)

        # Open the output PDF for editing
        doc = fitz.open(output_path)

        # Track the number of modifications applied
        modifications_applied = 0

        # Group modifications by page
        mods_by_page = {}
        for mod in modifications:
            page_number = mod.get("page", 1)
            if page_number not in mods_by_page:
                mods_by_page[page_number] = []
            mods_by_page[page_number].append(mod)

        # Process each page
        for page_number, page_mods in mods_by_page.items():
            try:
                # Get the page (0-based index)
                page = doc[page_number - 1]

                # Get all text on the page with positions
                text_dict = page.get_text("dict")

                # Process each modification
                for mod in page_mods:
                    try:
                        # Extract modification details
                        index = mod.get("index")
                        original_text = mod.get("originalText", "")
                        new_text = mod.get("newText", "")
                        transform = mod.get("transform", [1, 0, 0, 1, 0, 0])
                        font_name = mod.get("fontName", "helv")
                        font_size = mod.get("fontSize", 12)
                        new_font_size = mod.get("newFontSize", font_size)

                        # Calculate scale factor for font size change
                        scale_factor = new_font_size / font_size if font_size > 0 else 1

                        # Find the text span in the page
                        found = False
                        for block in text_dict.get("blocks", []):
                            if block.get("type") == 0:  # Text block
                                for line in block.get("lines", []):
                                    for span_idx, span in enumerate(line.get("spans", [])):
                                        span_text = span.get("text", "")
                                        if span_text == original_text:
                                            # Found the text to replace
                                            found = True

                                            # Get the bounding box
                                            bbox = span.get("bbox")

                                            # Create a rectangle for the area to replace
                                            rect = fitz.Rect(bbox)

                                            # Log the modification we're applying
                                            logger.info(f"Replacing text on page {page_number}: '{original_text}' -> '{new_text}'")

                                            # First, remove the original text by covering it with a white rectangle
                                            # Add a small padding to ensure we cover the entire text
                                            padding = 2
                                            expanded_rect = fitz.Rect(
                                                rect.x0 - padding,
                                                rect.y0 - padding,
                                                rect.x1 + padding,
                                                rect.y1 + padding
                                            )
                                            page.draw_rect(expanded_rect, color=(1, 1, 1), fill=(1, 1, 1))

                                            # Then add the new text
                                            text_writer = fitz.TextWriter(page.rect)

                                            # Get text color from the original span if available
                                            text_color = (0, 0, 0)  # Default to black
                                            if 'color' in span:
                                                try:
                                                    color_components = span.get('color', [0, 0, 0])
                                                    # Normalize color values to 0-1 range if needed
                                                    if any(c > 1 for c in color_components):
                                                        color_components = [c/255 for c in color_components]
                                                    text_color = tuple(color_components)
                                                except Exception as color_error:
                                                    logger.warning(f"Error parsing text color: {str(color_error)}. Using default color.")

                                            # Create a point for text insertion (top-left of the bbox)
                                            # Adjust y position based on font size change
                                            y_adjustment = new_font_size - font_size if font_size > 0 else 0
                                            point = fitz.Point(bbox[0], bbox[1] + new_font_size - y_adjustment * 0.5)

                                            # Get the font
                                            try:
                                                font = fitz.Font(font_name)
                                            except Exception as font_error:
                                                logger.warning(f"Error loading font {font_name}: {str(font_error)}. Using default font.")
                                                try:
                                                    # Try to find a similar font
                                                    available_fonts = fitz.Font.available_fonts()
                                                    if "helv" in available_fonts:
                                                        font = fitz.Font("helv")
                                                    elif "tiro" in available_fonts:
                                                        font = fitz.Font("tiro")
                                                    elif len(available_fonts) > 0:
                                                        font = fitz.Font(available_fonts[0])
                                                    else:
                                                        # Last resort - use a built-in font
                                                        font = fitz.Font("helv")
                                                except Exception as e:
                                                    logger.warning(f"Error loading fallback font: {str(e)}. Using default font.")
                                                    font = fitz.Font("helv")

                                            # Add text to the TextWriter with the original color
                                            text_writer.append(point, new_text, font=font, fontsize=new_font_size, color=text_color)

                                            # Apply the text to the page
                                            text_writer.write_text(page)

                                            # Log successful modification
                                            logger.info(f"Successfully replaced text: '{original_text}' -> '{new_text}' with font size {font_size} -> {new_font_size}")

                                            modifications_applied += 1
                                            break
                                    if found:
                                        break
                            if found:
                                break

                        if not found:
                            logger.warning(f"Text not found on page {page_number}: '{original_text}'")

                    except Exception as e:
                        logger.warning(f"Error applying modification: {str(e)}")
                        continue

            except Exception as e:
                logger.warning(f"Error processing page {page_number}: {str(e)}")
                continue

        # Save the document
        doc.save(output_path)

        # Close the document
        doc.close()

        logger.info(f"Successfully applied {modifications_applied} text modifications")

        return {
            'success': True,
            'modifications_applied': modifications_applied
        }

    except PDFProcessingError:
        # Re-raise PDFProcessingError
        raise

    except Exception as e:
        logger.error(f"Error modifying text in PDF: {str(e)}")
        raise PDFProcessingError(f"Failed to modify text in PDF: {str(e)}")

def get_pdf_preview(pdf_path, page_number=1, dpi=150):
    """
    Generate a preview image of a PDF page.

    Args:
        pdf_path (str): Path to the PDF file.
        page_number (int, optional): Page number to preview (1-based). Defaults to 1.
        dpi (int, optional): DPI for the preview image. Defaults to 150.

    Returns:
        str: Base64-encoded PNG image of the PDF page.
    """
    try:
        # Open the PDF
        doc = fitz.open(pdf_path)

        # Get the page (0-based index)
        page = doc[page_number - 1]

        # Set the zoom factor based on DPI
        zoom = dpi / 72  # 72 DPI is the default PDF resolution

        # Get the page as a pixmap
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))

        # Convert the pixmap to a PNG image
        png_data = pix.tobytes("png")

        # Encode the PNG data as base64
        base64_data = base64.b64encode(png_data).decode('utf-8')

        # Close the document
        doc.close()

        return base64_data

    except Exception as e:
        logger.error(f"Error generating PDF preview: {str(e)}")
        raise PDFProcessingError(f"Failed to generate PDF preview: {str(e)}")

def get_pdf_dimensions(pdf_path, page_number=1):
    """
    Get the dimensions of a PDF page.

    Args:
        pdf_path (str): Path to the PDF file.
        page_number (int, optional): Page number (1-based). Defaults to 1.

    Returns:
        tuple: A tuple containing the width and height of the page in points.
    """
    try:
        # Open the PDF
        doc = fitz.open(pdf_path)

        # Get the page (0-based index)
        page = doc[page_number - 1]

        # Get the page dimensions
        width, height = page.rect.width, page.rect.height

        # Close the document
        doc.close()

        return (width, height)

    except Exception as e:
        logger.error(f"Error getting PDF dimensions: {str(e)}")
        raise PDFProcessingError(f"Failed to get PDF dimensions: {str(e)}")
