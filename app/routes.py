"""
RevisePDF Routes Module

This module defines the routes for the RevisePDF application.
It includes blueprints for different sections of the application.
"""

from flask import Blueprint, render_template, current_app, request, redirect, url_for, flash, send_from_directory, jsonify, send_file
import os
import uuid
import datetime
import logging
import zipfile
import io
import json
from werkzeug.utils import secure_filename
from app.forms import CompressForm, RepairForm, OCRForm, ImageToPDFForm, MergeForm, SplitForm, ExtractForm, RotateForm, PDFToImageForm, PDFToTextForm, PDFToPDFAForm, PDFToPanoramicForm, PageNumbersForm, WatermarkForm, ProtectForm, UnlockForm, FlattenForm, RedactForm, ContentEditForm, SignatureForm
from tools.optimize.compress import compress_pdf
from tools.optimize.repair import repair_pdf, check_pdf_structure
from tools.optimize.ocr import perform_ocr, get_language_name
from tools.convert_to_pdf.image_to_pdf import convert_image_to_pdf
from tools.organize.merge import merge_pdfs
from tools.organize.split import split_pdf
from tools.organize.extract import extract_pages, format_page_list
from tools.organize.rotate import rotate_pages, get_rotation_description
from tools.convert_from_pdf.pdf_to_image import convert_pdf_to_images, create_images_zip
from tools.convert_from_pdf.pdf_to_text import extract_text_from_pdf
from tools.convert_from_pdf.pdf_to_pdfa import convert_to_pdfa, get_conformance_description
from tools.convert_from_pdf.pdf_to_panoramic import create_panoramic_image
from tools.edit.page_numbers import add_page_numbers, get_position_name, get_font_name
from tools.edit.watermark import add_watermark, get_position_name as get_watermark_position_name
from tools.edit.content import add_text_to_pdf, add_image_to_pdf, remove_content_from_pdf, get_pdf_dimensions, get_pdf_preview, get_available_fonts, extract_text_with_attributes, replace_text_preserving_attributes, get_all_text_with_positions
from tools.edit.text_editor import extract_text_blocks, replace_text_in_pdf, get_pdf_dimensions as get_text_editor_pdf_dimensions, get_pdf_preview as get_text_editor_pdf_preview
from tools.edit.signature import add_signature_to_pdf, add_signature_from_data_url, get_pdf_dimensions as get_signature_pdf_dimensions, get_pdf_preview as get_signature_pdf_preview
from tools.security.protect import protect_pdf, check_pdf_encryption
from tools.security.unlock import unlock_pdf, is_pdf_encrypted
from tools.security.flatten import flatten_pdf, has_form_fields_or_annotations
from tools.security.redact import redact_pdf, redact_pattern, get_common_patterns
from app.errors import PDFProcessingError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create blueprints for different sections of the application
main_bp = Blueprint('main', __name__)
optimize_bp = Blueprint('optimize', __name__, url_prefix='/optimise')
convert_to_pdf_bp = Blueprint('convert_to_pdf', __name__, url_prefix='/convert-to-pdf')
edit_bp = Blueprint('edit', __name__, url_prefix='/edit')
organize_bp = Blueprint('organize', __name__, url_prefix='/organise')
convert_from_pdf_bp = Blueprint('convert_from_pdf', __name__, url_prefix='/convert-from-pdf')
security_bp = Blueprint('security', __name__, url_prefix='/security')

# Helper functions
def allowed_file(filename, allowed_extensions=None):
    """
    Check if a file has an allowed extension.

    Args:
        filename (str): The filename to check.
        allowed_extensions (set, optional): Set of allowed extensions.
                                           Defaults to the app's ALLOWED_EXTENSIONS.

    Returns:
        bool: True if the file has an allowed extension, False otherwise.
    """
    if allowed_extensions is None:
        allowed_extensions = current_app.config['ALLOWED_EXTENSIONS']

    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def get_unique_filename(filename):
    """
    Generate a unique filename to prevent overwriting existing files.

    Args:
        filename (str): The original filename.

    Returns:
        str: A unique filename with a UUID and timestamp.
    """
    # Get the file extension
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

    # Generate a unique filename with UUID and timestamp
    unique_name = f"{uuid.uuid4().hex}_{int(datetime.datetime.now().timestamp())}"

    # Return the unique filename with the original extension
    return f"{unique_name}.{ext}" if ext else unique_name

def save_uploaded_file(file):
    """
    Save an uploaded file to the upload folder.

    Args:
        file (FileStorage): The uploaded file.

    Returns:
        str: The path to the saved file.
    """
    # Secure the filename to prevent directory traversal attacks
    filename = secure_filename(file.filename)

    # Generate a unique filename
    unique_filename = get_unique_filename(filename)

    # Create the full path to save the file
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)

    # Save the file
    file.save(file_path)

    return file_path

# Main routes
@main_bp.route('/')
def index():
    """Render the home page."""
    return render_template('index.html')

@main_bp.route('/privacy-policy')
def privacy_policy():
    """Render the privacy policy page."""
    return render_template('legal/privacy_policy.html')

@main_bp.route('/terms-of-service')
def terms_of_service():
    """Render the terms of service page."""
    return render_template('legal/terms_of_service.html')

@main_bp.route('/cookie-policy')
def cookie_policy():
    """Render the cookie policy page."""
    return render_template('legal/cookie_policy.html')

@main_bp.route('/gdpr-compliance')
def gdpr_compliance():
    """Render the GDPR compliance page."""
    return render_template('legal/gdpr_compliance.html')

@main_bp.route('/accessibility-statement')
def accessibility_statement():
    """Render the accessibility statement page."""
    return render_template('legal/accessibility_statement.html')

@main_bp.route('/data-protection')
def data_protection():
    """Render the data protection page."""
    return render_template('legal/data_protection.html')

@main_bp.route('/security-information')
def security_information():
    """Render the security information page."""
    return render_template('legal/security_information.html')

# Optimize routes
@optimize_bp.route('/')
def index():
    """Render the optimize index page."""
    return render_template('optimise/index.html')

@optimize_bp.route('/compress', methods=['GET', 'POST'])
def compress():
    """Render the compress page and handle form submission."""
    form = CompressForm()
    result = None
    output_filename = None

    if form.validate_on_submit():
        try:
            # Save the uploaded file
            input_file = form.file.data
            input_path = save_uploaded_file(input_file)

            # Generate output filename
            output_filename = get_unique_filename('compressed_' + secure_filename(input_file.filename))
            output_path = os.path.join(current_app.config['UPLOAD_FOLDER'], output_filename)

            # Compress the PDF
            compression_level = form.compression_level.data
            result = compress_pdf(input_path, output_path, compression_level)

            flash('PDF compressed successfully!', 'success')

        except PDFProcessingError as e:
            flash(f'Error compressing PDF: {str(e)}', 'danger')
            logger.error(f'Error compressing PDF: {str(e)}')
        except Exception as e:
            flash('An unexpected error occurred. Please try again.', 'danger')
            logger.error(f'Unexpected error in compress route: {str(e)}')

    return render_template('optimise/compress.html', form=form, result=result, output_filename=output_filename)

@optimize_bp.route('/download/<filename>')
def download_compressed(filename):
    """Download a compressed PDF file."""
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@optimize_bp.route('/repair', methods=['GET', 'POST'])
def repair():
    """Render the repair page and handle form submission."""
    form = RepairForm()
    result = None
    structure = None
    output_filename = None

    if form.validate_on_submit():
        try:
            # Save the uploaded file
            input_file = form.file.data
            input_path = save_uploaded_file(input_file)

            # Check the PDF structure
            structure = check_pdf_structure(input_path)

            # Generate output filename
            output_filename = get_unique_filename('repaired_' + secure_filename(input_file.filename))
            output_path = os.path.join(current_app.config['UPLOAD_FOLDER'], output_filename)

            # Repair the PDF
            result = repair_pdf(input_path, output_path)

            flash('PDF repaired successfully!', 'success')

        except PDFProcessingError as e:
            flash(f'Error repairing PDF: {str(e)}', 'danger')
            logger.error(f'Error repairing PDF: {str(e)}')
        except Exception as e:
            flash('An unexpected error occurred. Please try again.', 'danger')
            logger.error(f'Unexpected error in repair route: {str(e)}')

    return render_template('optimise/repair.html', form=form, result=result, structure=structure, output_filename=output_filename)

@optimize_bp.route('/download_repaired/<filename>')
def download_repaired(filename):
    """Download a repaired PDF file."""
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@optimize_bp.route('/ocr', methods=['GET', 'POST'])
def ocr():
    """Render the OCR page and handle form submission."""
    form = OCRForm()
    result = None
    output_filename = None

    if form.validate_on_submit():
        try:
            # Save the uploaded file
            input_file = form.file.data
            input_path = save_uploaded_file(input_file)

            # Generate output filename
            output_filename = get_unique_filename('ocr_' + secure_filename(input_file.filename))
            output_path = os.path.join(current_app.config['UPLOAD_FOLDER'], output_filename)

            # Perform OCR on the PDF
            language = form.language.data
            result = perform_ocr(input_path, output_path, language)

            flash('OCR completed successfully!', 'success')

        except PDFProcessingError as e:
            flash(f'Error performing OCR: {str(e)}', 'danger')
            logger.error(f'Error performing OCR: {str(e)}')
        except Exception as e:
            flash('An unexpected error occurred. Please try again.', 'danger')
            logger.error(f'Unexpected error in OCR route: {str(e)}')

    return render_template('optimise/ocr.html', form=form, result=result, output_filename=output_filename, get_language_name=get_language_name)

@optimize_bp.route('/download_ocr/<filename>')
def download_ocr(filename):
    """Download an OCR'd PDF file."""
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

# Convert to PDF routes
@convert_to_pdf_bp.route('/')
def index():
    """Render the convert to PDF index page."""
    return render_template('convert_to_pdf/index.html')

@convert_to_pdf_bp.route('/image-to-pdf', methods=['GET', 'POST'])
def image_to_pdf():
    """Render the image to PDF page and handle form submission."""
    form = ImageToPDFForm()
    result = None
    output_filename = None

    if form.validate_on_submit():
        try:
            # Save the uploaded file
            input_file = form.file.data
            input_path = save_uploaded_file(input_file)

            # Generate output filename
            output_filename = get_unique_filename(secure_filename(input_file.filename).rsplit('.', 1)[0] + '.pdf')
            output_path = os.path.join(current_app.config['UPLOAD_FOLDER'], output_filename)

            # Convert the image to PDF
            page_size = form.page_size.data
            orientation = form.orientation.data
            result = convert_image_to_pdf(input_path, output_path, page_size, orientation)

            flash('Image converted to PDF successfully!', 'success')

        except PDFProcessingError as e:
            flash(f'Error converting image to PDF: {str(e)}', 'danger')
            logger.error(f'Error converting image to PDF: {str(e)}')
        except Exception as e:
            flash('An unexpected error occurred. Please try again.', 'danger')
            logger.error(f'Unexpected error in image_to_pdf route: {str(e)}')

    return render_template('convert_to_pdf/image_to_pdf.html', form=form, result=result, output_filename=output_filename)

@convert_to_pdf_bp.route('/download_pdf/<filename>')
def download_pdf(filename):
    """Download a converted PDF file."""
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@convert_to_pdf_bp.route('/office-to-pdf')
def office_to_pdf():
    """Render the office to PDF page."""
    return render_template('convert_to_pdf/office_to_pdf.html')

@convert_to_pdf_bp.route('/html-to-pdf')
def html_to_pdf():
    """Render the HTML to PDF page."""
    return render_template('convert_to_pdf/html_to_pdf.html')

@convert_to_pdf_bp.route('/zip-to-pdf')
def zip_to_pdf():
    """Render the zip to PDF page."""
    return render_template('convert_to_pdf/zip_to_pdf.html')

# Edit routes
@edit_bp.route('/')
def index():
    """Render the edit index page."""
    return render_template('edit/index.html')

@edit_bp.route('/page-numbers', methods=['GET', 'POST'])
def page_numbers():
    """Render the page numbers page and handle form submission."""
    form = PageNumbersForm()
    result = None
    output_filename = None
    position_name = ""
    font_name = ""

    if form.validate_on_submit():
        try:
            # Save the uploaded file
            input_file = form.file.data
            input_path = save_uploaded_file(input_file)

            # Generate output filename
            output_filename = get_unique_filename('numbered_' + secure_filename(input_file.filename))
            output_path = os.path.join(current_app.config['UPLOAD_FOLDER'], output_filename)

            # Get form data
            position = form.position.data
            start_number = form.start_number.data
            font = form.font.data
            font_size = form.font_size.data
            prefix = form.prefix.data
            suffix = form.suffix.data
            margin = form.margin.data
            pages = form.pages.data

            # Add page numbers to the PDF
            result = add_page_numbers(
                input_path, output_path, start_number, position, font, font_size,
                (0, 0, 0), margin, prefix, suffix, pages
            )

            # Get human-readable names for display
            position_name = get_position_name(position)
            font_name = get_font_name(font)

            flash('Page numbers added successfully!', 'success')

        except PDFProcessingError as e:
            flash(f'Error adding page numbers: {str(e)}', 'danger')
            logger.error(f'Error adding page numbers: {str(e)}')
        except Exception as e:
            flash('An unexpected error occurred. Please try again.', 'danger')
            logger.error(f'Unexpected error in page numbers route: {str(e)}')

    return render_template('edit/page_numbers.html', form=form, result=result,
                           output_filename=output_filename, position_name=position_name,
                           font_name=font_name)

@edit_bp.route('/download_numbered/<filename>')
def download_numbered(filename):
    """Download a PDF with page numbers."""
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@edit_bp.route('/watermark', methods=['GET', 'POST'])
def watermark():
    """Render the watermark page and handle form submission."""
    form = WatermarkForm()
    result = None
    output_filename = None
    position_name = ""

    if form.validate_on_submit():
        try:
            # Save the uploaded file
            input_file = form.file.data
            input_path = save_uploaded_file(input_file)

            # Generate output filename
            output_filename = get_unique_filename('watermarked_' + secure_filename(input_file.filename))
            output_path = os.path.join(current_app.config['UPLOAD_FOLDER'], output_filename)

            # Get form data
            text = form.text.data
            position = form.position.data
            font = form.font.data
            font_size = form.font_size.data
            opacity = form.opacity.data / 100.0  # Convert from percentage to decimal
            rotation = form.rotation.data
            pages = form.pages.data

            # Add watermark to the PDF
            result = add_watermark(
                input_path, output_path, text, position, font, font_size,
                opacity, rotation, (128, 128, 128), pages
            )

            # Get human-readable position name for display
            position_name = get_watermark_position_name(position)

            flash('Watermark added successfully!', 'success')

        except PDFProcessingError as e:
            flash(f'Error adding watermark: {str(e)}', 'danger')
            logger.error(f'Error adding watermark: {str(e)}')
        except Exception as e:
            flash('An unexpected error occurred. Please try again.', 'danger')
            logger.error(f'Unexpected error in watermark route: {str(e)}')

    return render_template('edit/watermark.html', form=form, result=result,
                           output_filename=output_filename, position_name=position_name)

@edit_bp.route('/download_watermarked/<filename>')
def download_watermarked(filename):
    """Download a watermarked PDF file."""
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@edit_bp.route('/text-editor', methods=['GET', 'POST'])
def text_editor():
    """Render the text editor page and handle form submission."""
    form = ContentEditForm()
    pdf_uploaded = False
    preview_image = None
    filename = None
    output_filename = None
    current_page = 1
    total_pages = 1
    pdf_width = 595  # Default A4 width in points
    pdf_height = 842  # Default A4 height in points
    text_blocks = []

    # Check if we're viewing an already uploaded PDF
    if request.args.get('filename'):
        filename = request.args.get('filename')
        pdf_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

        if os.path.exists(pdf_path):
            pdf_uploaded = True

            # Get the page number from the query string
            page_str = request.args.get('page', '1')
            try:
                current_page = int(page_str)
                if current_page < 1:
                    current_page = 1
            except ValueError:
                current_page = 1

            try:
                # Get PDF dimensions
                pdf_width, pdf_height = get_text_editor_pdf_dimensions(pdf_path, current_page)

                # Get PDF preview
                preview_image = get_text_editor_pdf_preview(pdf_path, current_page)

                # Get total pages
                import fitz
                doc = fitz.open(pdf_path)
                total_pages = doc.page_count
                doc.close()

                # Extract text blocks
                text_blocks = extract_text_blocks(pdf_path, current_page)

                # Set output filename
                if not request.args.get('output'):
                    output_filename = get_unique_filename('edited_' + filename)
                else:
                    output_filename = request.args.get('output')
            except Exception as e:
                flash(f'Error processing PDF: {str(e)}', 'danger')
                pdf_uploaded = False

    # Handle form submission
    if form.validate_on_submit():
        try:
            # Save the uploaded file
            input_file = form.file.data
            filename = get_unique_filename(secure_filename(input_file.filename))
            input_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

            # Save the file
            input_file.save(input_path)

            # Redirect to the same page with the filename in the query string
            return redirect(url_for('edit.text_editor', filename=filename))

        except Exception as e:
            flash(f'Error uploading PDF: {str(e)}', 'danger')

    return render_template('edit/text_editor.html', form=form, pdf_uploaded=pdf_uploaded,
                           preview_image=preview_image, filename=filename,
                           output_filename=output_filename, current_page=current_page,
                           total_pages=total_pages, pdf_width=pdf_width,
                           pdf_height=pdf_height, text_blocks=text_blocks)

@edit_bp.route('/update-text-blocks', methods=['POST'])
def update_text_blocks():
    """Update text blocks in a PDF."""
    # Get form data
    filename = request.form.get('filename')
    text_blocks_json = request.form.get('text_blocks')

    # Debug: Log raw request data
    current_app.logger.info(f"Raw request data - filename: {filename}")
    current_app.logger.info(f"Raw request data - text_blocks_json length: {len(text_blocks_json) if text_blocks_json else 0}")

    # Debug: Check for output parameter
    output_param = request.args.get('output')
    current_app.logger.info(f"Output parameter from URL: {output_param}")

    try:
        # Parse text blocks
        text_blocks = json.loads(text_blocks_json)

        # Log the received data for debugging
        current_app.logger.info(f"Received update request for file: {filename}")
        current_app.logger.info(f"Number of text blocks: {len(text_blocks)}")

        # Get input path
        input_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

        # Check if the input file exists
        if not os.path.exists(input_path):
            current_app.logger.error(f"Input file not found: {input_path}")
            return jsonify({'error': f"Input file not found: {filename}"}), 404

        # Check if there's already an output file
        output_filename = request.args.get('output')
        if not output_filename:
            output_filename = get_unique_filename('edited_' + filename)

        output_path = os.path.join(current_app.config['UPLOAD_FOLDER'], output_filename)
        current_app.logger.info(f"Output path: {output_path}")

        # If the output file already exists, use it as the input
        if os.path.exists(output_path):
            current_app.logger.info(f"Using existing output file as input: {output_path}")
            input_path = output_path

        # Create a simple copy first to ensure we have a valid output file
        try:
            import shutil
            shutil.copy2(input_path, output_path)
            current_app.logger.info(f"Created initial copy of PDF: {input_path} -> {output_path}")
        except Exception as copy_error:
            current_app.logger.error(f"Error creating initial copy: {str(copy_error)}")
            return jsonify({'error': f"Error creating initial copy: {str(copy_error)}"}), 500

        # Replace text in the PDF
        try:
            # Debug: Log first few text blocks
            if text_blocks:
                current_app.logger.info(f"First text block: {text_blocks[0]}")

            result = replace_text_in_pdf(input_path, output_path, text_blocks)
            current_app.logger.info(f"Text replacement result: {result}")

            # Add output filename to result
            result['output_filename'] = output_filename

            # Return the result as JSON
            return jsonify(result)
        except Exception as pdf_error:
            current_app.logger.error(f"Error replacing text in PDF: {str(pdf_error)}")
            # Return the output filename anyway since we have a valid copy
            return jsonify({
                'error': f"Error replacing text in PDF: {str(pdf_error)}",
                'output_filename': output_filename,
                'success': False,
                'blocks_replaced': 0
            })

    except json.JSONDecodeError as json_error:
        current_app.logger.error(f"Invalid JSON data: {str(json_error)}")
        return jsonify({'error': f"Invalid JSON data: {str(json_error)}"}), 400

    except Exception as e:
        current_app.logger.error(f"Unexpected error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@edit_bp.route('/content', methods=['GET', 'POST'])
def content():
    """Render the content editing page and handle form submission."""
    form = ContentEditForm()
    pdf_uploaded = False
    preview_image = None
    filename = None
    output_filename = None
    current_page = 1
    total_pages = 1
    pdf_width = 595  # Default A4 width in points
    pdf_height = 842  # Default A4 height in points
    available_fonts = get_available_fonts()

    # Check if we're viewing an already uploaded PDF
    if request.args.get('filename'):
        filename = request.args.get('filename')
        pdf_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

        if os.path.exists(pdf_path):
            pdf_uploaded = True

            # Get the page number from the query string
            page_str = request.args.get('page', '1')
            try:
                current_page = int(page_str)
                if current_page < 1:
                    current_page = 1
            except ValueError:
                current_page = 1

            try:
                # Get PDF dimensions
                pdf_width, pdf_height = get_pdf_dimensions(pdf_path, current_page)

                # Get PDF preview
                preview_image = get_pdf_preview(pdf_path, current_page)

                # Get total pages
                import fitz
                doc = fitz.open(pdf_path)
                total_pages = doc.page_count
                doc.close()

                # Set output filename
                if not request.args.get('output'):
                    output_filename = get_unique_filename('edited_' + filename)
                else:
                    output_filename = request.args.get('output')
            except Exception as e:
                flash(f'Error processing PDF: {str(e)}', 'danger')
                pdf_uploaded = False

    # Handle form submission
    if form.validate_on_submit():
        try:
            # Save the uploaded file
            input_file = form.file.data
            filename = get_unique_filename(secure_filename(input_file.filename))
            input_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

            # Save the file
            input_file.save(input_path)

            # Redirect to the same page with the filename in the query string
            return redirect(url_for('edit.content', filename=filename))

        except Exception as e:
            flash(f'Error uploading PDF: {str(e)}', 'danger')

    return render_template('edit/content.html', form=form, pdf_uploaded=pdf_uploaded,
                           preview_image=preview_image, filename=filename,
                           output_filename=output_filename, current_page=current_page,
                           total_pages=total_pages, pdf_width=pdf_width,
                           pdf_height=pdf_height, available_fonts=available_fonts)

@edit_bp.route('/add-text', methods=['POST'])
def add_text():
    """Add text to a PDF."""
    # Get form data
    filename = request.form.get('filename')
    page_number = int(request.form.get('page_number', 1))
    text = request.form.get('text')
    font_name = request.form.get('font_name', 'helv')
    font_size = int(request.form.get('font_size', 12))
    color_hex = request.form.get('color', '#000000')
    align = request.form.get('align', 'left')
    rotate = int(request.form.get('rotate', 0))
    x = float(request.form.get('x', 100))
    y = float(request.form.get('y', 100))

    # Convert hex color to RGB tuple (0-1 range)
    color = tuple(int(color_hex.lstrip('#')[i:i+2], 16) / 255 for i in (0, 2, 4))

    try:
        # Get input and output paths
        input_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

        # Check if there's already an output file
        output_filename = request.args.get('output')
        if not output_filename:
            output_filename = get_unique_filename('edited_' + filename)

        output_path = os.path.join(current_app.config['UPLOAD_FOLDER'], output_filename)

        # If the output file already exists, use it as the input
        if os.path.exists(output_path):
            input_path = output_path

        # Add text to the PDF
        result = add_text_to_pdf(input_path, output_path, text, page_number, x, y,
                                font_name, font_size, color, align, rotate)

        flash('Text added successfully!', 'success')

        # Redirect back to the editor with the output filename
        return redirect(url_for('edit.content', filename=filename, page=page_number, output=output_filename))

    except Exception as e:
        flash(f'Error adding text: {str(e)}', 'danger')
        return redirect(url_for('edit.content', filename=filename, page=page_number))

@edit_bp.route('/add-image', methods=['POST'])
def add_image():
    """Add an image to a PDF."""
    # Get form data
    filename = request.form.get('filename')
    page_number = int(request.form.get('page_number', 1))
    x = float(request.form.get('x', 100))
    y = float(request.form.get('y', 100))
    width = request.form.get('width')
    height = request.form.get('height')
    rotate = int(request.form.get('rotate', 0))

    # Convert width and height to float if provided
    if width:
        width = float(width)
    if height:
        height = float(height)

    try:
        # Save the uploaded image to a temporary file
        image_file = request.files.get('image')
        if not image_file:
            flash('No image file provided.', 'danger')
            return redirect(url_for('edit.content', filename=filename, page=page_number))

        image_filename = get_unique_filename(secure_filename(image_file.filename))
        image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], image_filename)
        image_file.save(image_path)

        # Get input and output paths
        input_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

        # Check if there's already an output file
        output_filename = request.args.get('output')
        if not output_filename:
            output_filename = get_unique_filename('edited_' + filename)

        output_path = os.path.join(current_app.config['UPLOAD_FOLDER'], output_filename)

        # If the output file already exists, use it as the input
        if os.path.exists(output_path):
            input_path = output_path

        # Add image to the PDF
        result = add_image_to_pdf(input_path, output_path, image_path, page_number,
                                 x, y, width, height, rotate)

        # Clean up the temporary image file
        os.remove(image_path)

        flash('Image added successfully!', 'success')

        # Redirect back to the editor with the output filename
        return redirect(url_for('edit.content', filename=filename, page=page_number, output=output_filename))

    except Exception as e:
        flash(f'Error adding image: {str(e)}', 'danger')
        return redirect(url_for('edit.content', filename=filename, page=page_number))

@edit_bp.route('/remove-content', methods=['POST'])
def remove_content():
    """Remove content from a PDF."""
    # Get form data
    filename = request.form.get('filename')
    page_number = int(request.form.get('page_number', 1))
    x1 = float(request.form.get('x1', 100))
    y1 = float(request.form.get('y1', 100))
    x2 = float(request.form.get('x2', 200))
    y2 = float(request.form.get('y2', 200))

    try:
        # Get input and output paths
        input_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

        # Check if there's already an output file
        output_filename = request.args.get('output')
        if not output_filename:
            output_filename = get_unique_filename('edited_' + filename)

        output_path = os.path.join(current_app.config['UPLOAD_FOLDER'], output_filename)

        # If the output file already exists, use it as the input
        if os.path.exists(output_path):
            input_path = output_path

        # Remove content from the PDF
        result = remove_content_from_pdf(input_path, output_path, page_number, x1, y1, x2, y2)

        flash('Content removed successfully!', 'success')

        # Redirect back to the editor with the output filename
        return redirect(url_for('edit.content', filename=filename, page=page_number, output=output_filename))

    except Exception as e:
        flash(f'Error removing content: {str(e)}', 'danger')
        return redirect(url_for('edit.content', filename=filename, page=page_number))

@edit_bp.route('/download-edited/<filename>')
def download_edited(filename):
    """Download an edited PDF file."""
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@edit_bp.route('/extract-text', methods=['POST'])
def extract_text():
    """Extract text with attributes from a PDF."""
    # Get form data
    filename = request.form.get('filename')
    page_number = int(request.form.get('page_number', 1))
    x1 = float(request.form.get('x1', 0))
    y1 = float(request.form.get('y1', 0))
    x2 = float(request.form.get('x2', 0))
    y2 = float(request.form.get('y2', 0))

    try:
        # Get input path
        input_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

        # Extract text with attributes
        result = extract_text_with_attributes(input_path, page_number, x1, y1, x2, y2)

        # Return the result as JSON
        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 400

@edit_bp.route('/get-all-text', methods=['POST'])
def get_all_text():
    """Get all text on a page with positions."""
    # Get form data
    filename = request.form.get('filename')
    page_number = int(request.form.get('page_number', 1))

    try:
        # Get input path
        input_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

        # Get all text with positions
        result = get_all_text_with_positions(input_path, page_number)

        # Return the result as JSON
        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 400

@edit_bp.route('/replace-text', methods=['POST'])
def replace_text():
    """Replace text in a PDF while preserving attributes."""
    # Get form data
    filename = request.form.get('filename')
    page_number = int(request.form.get('page_number', 1))
    original_rect = json.loads(request.form.get('original_rect', '[0, 0, 0, 0]'))
    new_text = request.form.get('new_text', '')
    text_attributes = json.loads(request.form.get('text_attributes', '{}'))

    try:
        # Get input path
        input_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

        # Check if there's already an output file
        output_filename = request.args.get('output')
        if not output_filename:
            output_filename = get_unique_filename('edited_' + filename)

        output_path = os.path.join(current_app.config['UPLOAD_FOLDER'], output_filename)

        # If the output file already exists, use it as the input
        if os.path.exists(output_path):
            input_path = output_path

        # Replace text
        result = replace_text_preserving_attributes(input_path, output_path, page_number,
                                                  original_rect, new_text, text_attributes)

        # Add output filename to result
        result['output_filename'] = output_filename

        # Return the result as JSON
        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 400

@edit_bp.route('/signature', methods=['GET', 'POST'])
def signature():
    """Render the signature page and handle form submission."""
    form = SignatureForm()
    pdf_uploaded = False
    preview_image = None
    filename = None
    output_filename = None
    current_page = 1
    total_pages = 1
    pdf_width = 595  # Default A4 width in points
    pdf_height = 842  # Default A4 height in points

    # Check if we're viewing an already uploaded PDF
    if request.args.get('filename'):
        filename = request.args.get('filename')
        pdf_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

        if os.path.exists(pdf_path):
            pdf_uploaded = True

            # Get the page number from the query string
            page_str = request.args.get('page', '1')
            try:
                current_page = int(page_str)
                if current_page < 1:
                    current_page = 1
            except ValueError:
                current_page = 1

            try:
                # Get PDF dimensions
                pdf_width, pdf_height = get_signature_pdf_dimensions(pdf_path, current_page)

                # Get PDF preview
                preview_image = get_signature_pdf_preview(pdf_path, current_page)

                # Get total pages
                import fitz
                doc = fitz.open(pdf_path)
                total_pages = doc.page_count
                doc.close()

                # Set output filename
                if not request.args.get('output'):
                    output_filename = get_unique_filename('signed_' + filename)
                else:
                    output_filename = request.args.get('output')
            except Exception as e:
                flash(f'Error processing PDF: {str(e)}', 'danger')
                pdf_uploaded = False

    # Handle form submission
    if form.validate_on_submit():
        try:
            # Save the uploaded file
            input_file = form.file.data
            filename = get_unique_filename(secure_filename(input_file.filename))
            input_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

            # Save the file
            input_file.save(input_path)

            # Redirect to the same page with the filename in the query string
            return redirect(url_for('edit.signature', filename=filename))

        except Exception as e:
            flash(f'Error uploading PDF: {str(e)}', 'danger')

    return render_template('edit/signature.html', form=form, pdf_uploaded=pdf_uploaded,
                           preview_image=preview_image, filename=filename,
                           output_filename=output_filename, current_page=current_page,
                           total_pages=total_pages, pdf_width=pdf_width,
                           pdf_height=pdf_height)

@edit_bp.route('/add-signature', methods=['POST'])
def add_signature():
    """Add a signature to a PDF."""
    # Get form data
    filename = request.form.get('filename')
    page_number = int(request.form.get('page_number', 1))
    signature_data = request.form.get('signature_data')
    x = float(request.form.get('x', 100))
    y = float(request.form.get('y', 100))
    width = request.form.get('width')
    height = request.form.get('height')

    # Convert width and height to float if provided
    if width:
        width = float(width)
    if height:
        height = float(height)

    try:
        # Validate signature data
        if not signature_data or not signature_data.startswith('data:image/'):
            flash('No signature data provided.', 'danger')
            return redirect(url_for('edit.signature', filename=filename, page=page_number))

        # Get input and output paths
        input_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

        # Check if there's already an output file
        output_filename = request.args.get('output')
        if not output_filename:
            output_filename = get_unique_filename('signed_' + filename)

        output_path = os.path.join(current_app.config['UPLOAD_FOLDER'], output_filename)

        # If the output file already exists, use it as the input
        if os.path.exists(output_path):
            input_path = output_path

        # Add signature to the PDF
        result = add_signature_from_data_url(input_path, output_path, signature_data,
                                           page_number, x, y, width, height)

        flash('Signature added successfully!', 'success')

        # Redirect back to the editor with the output filename
        return redirect(url_for('edit.signature', filename=filename, page=page_number, output=output_filename))

    except Exception as e:
        flash(f'Error adding signature: {str(e)}', 'danger')
        return redirect(url_for('edit.signature', filename=filename, page=page_number))

@edit_bp.route('/download-signed/<filename>')
def download_signed(filename):
    """Download a signed PDF file."""
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

# Organize routes
@organize_bp.route('/')
def index():
    """Render the organize index page."""
    return render_template('organise/index.html')

@organize_bp.route('/merge', methods=['GET', 'POST'])
def merge():
    """Render the merge page and handle form submission."""
    result = None
    output_filename = None

    if request.method == 'POST':
        try:
            # Get files from the request
            files = request.files.getlist('files[]')

            # Check if files were provided
            if not files or all(not f.filename for f in files):
                flash('Please select at least one PDF file.', 'danger')
                form = MergeForm()
                return render_template('organise/merge.html', form=form)

            # Save uploaded files
            input_paths = []
            for file in files:
                if file and file.filename:
                    # Check if the file is a PDF
                    if not file.filename.lower().endswith('.pdf'):
                        flash('Only PDF files are allowed.', 'danger')
                        continue

                    # Save the file
                    file_path = save_uploaded_file(file)
                    input_paths.append(file_path)

            # Check if any valid files were uploaded
            if not input_paths:
                flash('No valid PDF files were uploaded.', 'danger')
                return render_template('organise/merge.html')

            # Generate output filename
            output_filename = get_unique_filename('merged.pdf')
            output_path = os.path.join(current_app.config['UPLOAD_FOLDER'], output_filename)

            # Get table of contents option
            create_toc = 'create_toc' in request.form

            # Merge the PDFs
            result = merge_pdfs(input_paths, output_path, toc=create_toc)

            flash('PDFs merged successfully!', 'success')

        except PDFProcessingError as e:
            flash(f'Error merging PDFs: {str(e)}', 'danger')
            logger.error(f'Error merging PDFs: {str(e)}')
        except Exception as e:
            flash('An unexpected error occurred. Please try again.', 'danger')
            logger.error(f'Unexpected error in merge route: {str(e)}')

    form = MergeForm()
    return render_template('organise/merge.html', form=form, result=result, output_filename=output_filename)

@organize_bp.route('/download_merged/<filename>')
def download_merged(filename):
    """Download a merged PDF file."""
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@organize_bp.route('/split', methods=['GET', 'POST'])
def split():
    """Render the split page and handle form submission."""
    form = SplitForm()
    result = None
    job_id = None

    if form.validate_on_submit():
        try:
            # Save the uploaded file
            input_file = form.file.data
            input_path = save_uploaded_file(input_file)

            # Generate a unique job ID for this split operation
            job_id = uuid.uuid4().hex

            # Create a directory for the split files
            output_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], f'split_{job_id}')
            os.makedirs(output_dir, exist_ok=True)

            # Get split parameters
            split_method = form.split_method.data
            page_ranges = form.page_ranges.data if split_method == 'range' else None
            max_size = form.max_size.data if split_method == 'size' else None

            # Split the PDF
            result = split_pdf(input_path, output_dir, split_method, page_ranges, max_size)

            flash('PDF split successfully!', 'success')

        except PDFProcessingError as e:
            flash(f'Error splitting PDF: {str(e)}', 'danger')
            logger.error(f'Error splitting PDF: {str(e)}')
        except Exception as e:
            flash('An unexpected error occurred. Please try again.', 'danger')
            logger.error(f'Unexpected error in split route: {str(e)}')

    return render_template('organise/split.html', form=form, result=result, job_id=job_id)

@organize_bp.route('/download_split/<filename>')
def download_split(filename):
    """Download a split PDF file."""
    # Find the file in any of the split directories
    for dir_name in os.listdir(current_app.config['UPLOAD_FOLDER']):
        if dir_name.startswith('split_'):
            dir_path = os.path.join(current_app.config['UPLOAD_FOLDER'], dir_name)
            file_path = os.path.join(dir_path, filename)
            if os.path.exists(file_path):
                return send_from_directory(dir_path, filename, as_attachment=True)

    # If file not found, return 404
    flash('File not found.', 'danger')
    return redirect(url_for('organize.split'))

@organize_bp.route('/download_all_split/<job_id>')
def download_all_split(job_id):
    """Download all split PDF files as a ZIP archive."""
    # Check if the split directory exists
    split_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], f'split_{job_id}')
    if not os.path.exists(split_dir):
        flash('Files not found.', 'danger')
        return redirect(url_for('organize.split'))

    # Create a ZIP file in memory
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        for filename in os.listdir(split_dir):
            file_path = os.path.join(split_dir, filename)
            zf.write(file_path, filename)

    # Seek to the beginning of the file
    memory_file.seek(0)

    # Return the ZIP file
    return send_file(
        memory_file,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f'split_pdfs_{job_id}.zip'
    )

@organize_bp.route('/extract', methods=['GET', 'POST'])
def extract():
    """Render the extract page and handle form submission."""
    form = ExtractForm()
    result = None
    output_filename = None
    formatted_pages = ""

    if form.validate_on_submit():
        try:
            # Save the uploaded file
            input_file = form.file.data
            input_path = save_uploaded_file(input_file)

            # Generate output filename
            output_filename = get_unique_filename('extracted_' + secure_filename(input_file.filename))
            output_path = os.path.join(current_app.config['UPLOAD_FOLDER'], output_filename)

            # Extract the pages
            pages = form.pages.data
            result = extract_pages(input_path, output_path, pages)

            # Format the extracted pages for display
            formatted_pages = format_page_list(result['extracted_pages'])

            flash('Pages extracted successfully!', 'success')

        except PDFProcessingError as e:
            flash(f'Error extracting pages: {str(e)}', 'danger')
            logger.error(f'Error extracting pages: {str(e)}')
        except Exception as e:
            flash('An unexpected error occurred. Please try again.', 'danger')
            logger.error(f'Unexpected error in extract route: {str(e)}')

    return render_template('organise/extract.html', form=form, result=result, output_filename=output_filename, formatted_pages=formatted_pages)

@organize_bp.route('/download_extracted/<filename>')
def download_extracted(filename):
    """Download an extracted PDF file."""
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@organize_bp.route('/rotate', methods=['GET', 'POST'])
def rotate():
    """Render the rotate page and handle form submission."""
    form = RotateForm()
    result = None
    output_filename = None
    rotation_description = ""
    formatted_pages = ""

    if form.validate_on_submit():
        try:
            # Save the uploaded file
            input_file = form.file.data
            input_path = save_uploaded_file(input_file)

            # Generate output filename
            output_filename = get_unique_filename('rotated_' + secure_filename(input_file.filename))
            output_path = os.path.join(current_app.config['UPLOAD_FOLDER'], output_filename)

            # Rotate the pages
            rotation = int(form.rotation.data)
            pages = form.pages.data
            result = rotate_pages(input_path, output_path, rotation, pages)

            # Get rotation description
            rotation_description = get_rotation_description(rotation)

            # Format the rotated pages for display
            formatted_pages = format_page_list(result['rotated_pages'])

            flash('Pages rotated successfully!', 'success')

        except PDFProcessingError as e:
            flash(f'Error rotating pages: {str(e)}', 'danger')
            logger.error(f'Error rotating pages: {str(e)}')
        except Exception as e:
            flash('An unexpected error occurred. Please try again.', 'danger')
            logger.error(f'Unexpected error in rotate route: {str(e)}')

    return render_template('organise/rotate.html', form=form, result=result, output_filename=output_filename,
                           rotation_description=rotation_description, formatted_pages=formatted_pages)

@organize_bp.route('/download_rotated/<filename>')
def download_rotated(filename):
    """Download a rotated PDF file."""
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

# Convert from PDF routes
@convert_from_pdf_bp.route('/')
def index():
    """Render the convert from PDF index page."""
    return render_template('convert_from_pdf/index.html')

@convert_from_pdf_bp.route('/pdf-to-image', methods=['GET', 'POST'])
def pdf_to_image():
    """Render the PDF to image page and handle form submission."""
    form = PDFToImageForm()
    result = None
    job_id = None

    if form.validate_on_submit():
        try:
            # Save the uploaded file
            input_file = form.file.data
            input_path = save_uploaded_file(input_file)

            # Generate a unique job ID for this conversion
            job_id = uuid.uuid4().hex

            # Create a directory for the output images
            output_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], f'pdf_to_image_{job_id}')
            os.makedirs(output_dir, exist_ok=True)

            # Get conversion parameters
            image_format = form.format.data
            dpi = form.dpi.data
            pages = form.pages.data

            # Convert the PDF to images
            result = convert_pdf_to_images(input_path, output_dir, image_format, dpi, pages)

            # Create a ZIP file of all images
            zip_filename = f"images_{job_id}.zip"
            zip_path = os.path.join(current_app.config['UPLOAD_FOLDER'], zip_filename)
            create_images_zip(result['output_files'], zip_path)

            flash('PDF converted to images successfully!', 'success')

        except PDFProcessingError as e:
            flash(f'Error converting PDF to images: {str(e)}', 'danger')
            logger.error(f'Error converting PDF to images: {str(e)}')
        except Exception as e:
            flash('An unexpected error occurred. Please try again.', 'danger')
            logger.error(f'Unexpected error in PDF to image route: {str(e)}')

    return render_template('convert_from_pdf/pdf_to_image.html', form=form, result=result, job_id=job_id)

@convert_from_pdf_bp.route('/get_image/<job_id>/<filename>')
def get_image(job_id, filename):
    """Get an image for display in the browser."""
    directory = os.path.join(current_app.config['UPLOAD_FOLDER'], f'pdf_to_image_{job_id}')
    return send_from_directory(directory, filename)

@convert_from_pdf_bp.route('/download_image/<job_id>/<filename>')
def download_image(job_id, filename):
    """Download a single image."""
    directory = os.path.join(current_app.config['UPLOAD_FOLDER'], f'pdf_to_image_{job_id}')
    return send_from_directory(directory, filename, as_attachment=True)

@convert_from_pdf_bp.route('/download_images_zip/<job_id>')
def download_images_zip(job_id):
    """Download all images as a ZIP archive."""
    zip_filename = f"images_{job_id}.zip"
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], zip_filename, as_attachment=True)

@convert_from_pdf_bp.route('/pdf-to-panoramic', methods=['GET', 'POST'])
def pdf_to_panoramic():
    """Render the PDF to panoramic page and handle form submission."""
    form = PDFToPanoramicForm()
    result = None
    output_filename = None

    if form.validate_on_submit():
        try:
            # Save the uploaded file
            input_file = form.file.data
            input_path = save_uploaded_file(input_file)

            # Get form data
            image_format = form.format.data
            dpi = form.dpi.data
            direction = form.direction.data
            spacing = form.spacing.data
            pages = form.pages.data

            # Generate output filename with appropriate extension
            base_filename = os.path.splitext(secure_filename(input_file.filename))[0]
            output_filename = get_unique_filename(f'panoramic_{base_filename}.{image_format}')
            output_path = os.path.join(current_app.config['UPLOAD_FOLDER'], output_filename)

            # Create panoramic image
            result = create_panoramic_image(
                input_path, output_path, image_format, dpi, direction, pages, spacing
            )

            flash('Panoramic image created successfully!', 'success')

        except PDFProcessingError as e:
            flash(f'Error creating panoramic image: {str(e)}', 'danger')
            logger.error(f'Error creating panoramic image: {str(e)}')
        except Exception as e:
            flash('An unexpected error occurred. Please try again.', 'danger')
            logger.error(f'Unexpected error in PDF to panoramic route: {str(e)}')

    return render_template('convert_from_pdf/pdf_to_panoramic.html', form=form, result=result, output_filename=output_filename)

@convert_from_pdf_bp.route('/get_panoramic/<filename>')
def get_panoramic(filename):
    """Get a panoramic image for display in the browser."""
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

@convert_from_pdf_bp.route('/download_panoramic/<filename>')
def download_panoramic(filename):
    """Download a panoramic image."""
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@convert_from_pdf_bp.route('/pdf-to-pdfa', methods=['GET', 'POST'])
def pdf_to_pdfa():
    """Render the PDF to PDF/A page and handle form submission."""
    form = PDFToPDFAForm()
    result = None
    output_filename = None
    conformance_description = ""

    if form.validate_on_submit():
        try:
            # Save the uploaded file
            input_file = form.file.data
            input_path = save_uploaded_file(input_file)

            # Generate output filename
            output_filename = get_unique_filename('pdfa_' + secure_filename(input_file.filename))
            output_path = os.path.join(current_app.config['UPLOAD_FOLDER'], output_filename)

            # Get conformance level
            conformance = form.conformance.data

            # Convert to PDF/A
            result = convert_to_pdfa(input_path, output_path, conformance)

            # Get human-readable conformance description
            conformance_description = get_conformance_description(conformance)

            flash('PDF converted to PDF/A successfully!', 'success')

        except PDFProcessingError as e:
            flash(f'Error converting to PDF/A: {str(e)}', 'danger')
            logger.error(f'Error converting to PDF/A: {str(e)}')
        except Exception as e:
            flash('An unexpected error occurred. Please try again.', 'danger')
            logger.error(f'Unexpected error in PDF to PDF/A route: {str(e)}')

    return render_template('convert_from_pdf/pdf_to_pdfa.html', form=form, result=result,
                           output_filename=output_filename, conformance_description=conformance_description)

@convert_from_pdf_bp.route('/download_pdfa/<filename>')
def download_pdfa(filename):
    """Download a PDF/A file."""
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@convert_from_pdf_bp.route('/pdf-to-text', methods=['GET', 'POST'])
def pdf_to_text():
    """Render the PDF to text page and handle form submission."""
    form = PDFToTextForm()
    result = None
    output_filename = None
    text_preview = ""

    if form.validate_on_submit():
        try:
            # Save the uploaded file
            input_file = form.file.data
            input_path = save_uploaded_file(input_file)

            # Generate output filename
            output_filename = get_unique_filename('text_' + os.path.splitext(secure_filename(input_file.filename))[0] + '.txt')
            output_path = os.path.join(current_app.config['UPLOAD_FOLDER'], output_filename)

            # Get extraction parameters
            pages = form.pages.data
            include_page_numbers = form.include_page_numbers.data

            # Extract text from the PDF
            result = extract_text_from_pdf(input_path, output_path, pages, include_page_numbers)

            # Get a preview of the extracted text
            with open(output_path, 'r', encoding='utf-8') as f:
                text = f.read()
                # Limit preview to first 1000 characters
                text_preview = text[:1000]
                if len(text) > 1000:
                    text_preview += "\n\n[...] Text truncated for preview. Download the full text file."

            flash('Text extracted successfully!', 'success')

        except PDFProcessingError as e:
            flash(f'Error extracting text: {str(e)}', 'danger')
            logger.error(f'Error extracting text: {str(e)}')
        except Exception as e:
            flash('An unexpected error occurred. Please try again.', 'danger')
            logger.error(f'Unexpected error in PDF to text route: {str(e)}')

    return render_template('convert_from_pdf/pdf_to_text.html', form=form, result=result,
                           output_filename=output_filename, text_preview=text_preview)

@convert_from_pdf_bp.route('/download_text/<filename>')
def download_text(filename):
    """Download an extracted text file."""
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

# Security routes
@security_bp.route('/')
def index():
    """Render the security index page."""
    return render_template('security/index.html')

@security_bp.route('/unlock', methods=['GET', 'POST'])
def unlock():
    """Render the unlock page and handle form submission."""
    form = UnlockForm()
    result = None
    output_filename = None

    if form.validate_on_submit():
        try:
            # Save the uploaded file
            input_file = form.file.data
            input_path = save_uploaded_file(input_file)

            # Check if the PDF is encrypted
            if not is_pdf_encrypted(input_path):
                flash('The PDF is not encrypted and does not need to be unlocked.', 'warning')
                return render_template('security/unlock.html', form=form)

            # Generate output filename
            output_filename = get_unique_filename('unlocked_' + secure_filename(input_file.filename))
            output_path = os.path.join(current_app.config['UPLOAD_FOLDER'], output_filename)

            # Get the password
            password = form.password.data

            # Unlock the PDF
            result = unlock_pdf(input_path, output_path, password)

            flash('PDF unlocked successfully!', 'success')

        except PDFProcessingError as e:
            flash(f'Error unlocking PDF: {str(e)}', 'danger')
            logger.error(f'Error unlocking PDF: {str(e)}')
        except Exception as e:
            flash('An unexpected error occurred. Please try again.', 'danger')
            logger.error(f'Unexpected error in unlock route: {str(e)}')

    return render_template('security/unlock.html', form=form, result=result, output_filename=output_filename)

@security_bp.route('/download_unlocked/<filename>')
def download_unlocked(filename):
    """Download an unlocked PDF file."""
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@security_bp.route('/protect', methods=['GET', 'POST'])
def protect():
    """Render the protect page and handle form submission."""
    form = ProtectForm()
    result = None
    output_filename = None

    if form.validate_on_submit():
        try:
            # Validate passwords
            user_password = form.user_password.data
            owner_password = form.owner_password.data
            confirm_password = form.confirm_password.data

            if not user_password and not owner_password:
                flash('Please provide at least one password (user or owner).', 'danger')
                return render_template('security/protect.html', form=form)

            if user_password and user_password != confirm_password:
                flash('Passwords do not match.', 'danger')
                return render_template('security/protect.html', form=form)

            # Save the uploaded file
            input_file = form.file.data
            input_path = save_uploaded_file(input_file)

            # Generate output filename
            output_filename = get_unique_filename('protected_' + secure_filename(input_file.filename))
            output_path = os.path.join(current_app.config['UPLOAD_FOLDER'], output_filename)

            # Get permission settings
            allow_print = form.allow_print.data
            allow_modify = form.allow_modify.data
            allow_copy = form.allow_copy.data
            allow_annotate = form.allow_annotate.data
            allow_forms = form.allow_forms.data
            allow_accessibility = form.allow_accessibility.data
            allow_assemble = form.allow_assemble.data
            allow_print_hq = form.allow_print_hq.data

            # Protect the PDF
            result = protect_pdf(
                input_path, output_path, user_password, owner_password,
                allow_print, allow_modify, allow_copy, allow_annotate,
                allow_forms, allow_accessibility, allow_assemble, allow_print_hq
            )

            flash('PDF protected successfully!', 'success')

        except PDFProcessingError as e:
            flash(f'Error protecting PDF: {str(e)}', 'danger')
            logger.error(f'Error protecting PDF: {str(e)}')
        except Exception as e:
            flash('An unexpected error occurred. Please try again.', 'danger')
            logger.error(f'Unexpected error in protect route: {str(e)}')

    return render_template('security/protect.html', form=form, result=result, output_filename=output_filename)

@security_bp.route('/download_protected/<filename>')
def download_protected(filename):
    """Download a protected PDF file."""
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@security_bp.route('/redact', methods=['GET', 'POST'])
def redact():
    """Render the redact page and handle form submission."""
    form = RedactForm()
    result = None
    output_filename = None

    if form.validate_on_submit():
        try:
            # Save the uploaded file
            input_file = form.file.data
            input_path = save_uploaded_file(input_file)

            # Generate output filename
            output_filename = get_unique_filename('redacted_' + secure_filename(input_file.filename))
            output_path = os.path.join(current_app.config['UPLOAD_FOLDER'], output_filename)

            # Get form data
            redaction_type = form.redaction_type.data
            case_sensitive = form.case_sensitive.data
            whole_words = form.whole_words.data

            # Process based on redaction type
            if redaction_type == 'text':
                # Text search redaction
                search_text = form.search_text.data
                if not search_text:
                    flash('Please enter text to redact.', 'danger')
                    return render_template('security/redact.html', form=form)

                result = redact_pdf(input_path, output_path, search_text, case_sensitive, whole_words)

            elif redaction_type == 'pattern':
                # Pattern redaction
                pattern = form.pattern.data
                if not pattern:
                    flash('Please enter a regular expression pattern.', 'danger')
                    return render_template('security/redact.html', form=form)

                result = redact_pattern(input_path, output_path, pattern, case_sensitive)

            elif redaction_type == 'common_pattern':
                # Common pattern redaction
                pattern_name = form.common_pattern.data
                patterns = get_common_patterns()

                if pattern_name not in patterns:
                    flash('Invalid pattern selected.', 'danger')
                    return render_template('security/redact.html', form=form)

                pattern = patterns[pattern_name]
                result = redact_pattern(input_path, output_path, pattern, case_sensitive)

            if result['redacted_count'] == 0:
                flash('No matching text found to redact.', 'warning')
            else:
                flash(f'Successfully redacted {result["redacted_count"]} instances of text.', 'success')

        except PDFProcessingError as e:
            flash(f'Error redacting PDF: {str(e)}', 'danger')
            logger.error(f'Error redacting PDF: {str(e)}')
        except Exception as e:
            flash('An unexpected error occurred. Please try again.', 'danger')
            logger.error(f'Unexpected error in redact route: {str(e)}')

    return render_template('security/redact.html', form=form, result=result, output_filename=output_filename)

@security_bp.route('/download_redacted/<filename>')
def download_redacted(filename):
    """Download a redacted PDF file."""
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@security_bp.route('/flatten', methods=['GET', 'POST'])
def flatten():
    """Render the flatten page and handle form submission."""
    form = FlattenForm()
    result = None
    output_filename = None

    if form.validate_on_submit():
        try:
            # Save the uploaded file
            input_file = form.file.data
            input_path = save_uploaded_file(input_file)

            # Check if the PDF has form fields or annotations
            pdf_info = has_form_fields_or_annotations(input_path)

            if not pdf_info['has_form_fields'] and not pdf_info['has_annotations']:
                flash('The PDF does not have any form fields or annotations to flatten.', 'warning')
                return render_template('security/flatten.html', form=form)

            # Generate output filename
            output_filename = get_unique_filename('flattened_' + secure_filename(input_file.filename))
            output_path = os.path.join(current_app.config['UPLOAD_FOLDER'], output_filename)

            # Get flattening options
            flatten_form_fields = form.flatten_form_fields.data
            flatten_annotations = form.flatten_annotations.data

            # Flatten the PDF
            result = flatten_pdf(input_path, output_path, flatten_annotations, flatten_form_fields)

            flash('PDF flattened successfully!', 'success')

        except PDFProcessingError as e:
            flash(f'Error flattening PDF: {str(e)}', 'danger')
            logger.error(f'Error flattening PDF: {str(e)}')
        except Exception as e:
            flash('An unexpected error occurred. Please try again.', 'danger')
            logger.error(f'Unexpected error in flatten route: {str(e)}')

    return render_template('security/flatten.html', form=form, result=result, output_filename=output_filename)

@security_bp.route('/download_flattened/<filename>')
def download_flattened(filename):
    """Download a flattened PDF file."""
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename, as_attachment=True)
