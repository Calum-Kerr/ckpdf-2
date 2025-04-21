"""
RevisePDF Forms Module

This module defines the forms used in the RevisePDF application.
It includes forms for file uploads and various PDF processing operations.
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, SelectField, IntegerField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional, EqualTo

class FileUploadForm(FlaskForm):
    """Base form for file uploads."""

    file = FileField('Select File', validators=[
        FileRequired('Please select a file'),
    ])
    submit = SubmitField('Upload')


class PDFUploadForm(FileUploadForm):
    """Form for PDF file uploads."""

    file = FileField('Select PDF File', validators=[
        FileRequired('Please select a PDF file'),
        FileAllowed(['pdf'], 'Only PDF files are allowed')
    ])


class ImageUploadForm(FileUploadForm):
    """Form for image file uploads."""

    file = FileField('Select Image File', validators=[
        FileRequired('Please select an image file'),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'tif'], 'Only image files are allowed')
    ])


class OfficeUploadForm(FileUploadForm):
    """Form for Office document uploads."""

    file = FileField('Select Office Document', validators=[
        FileRequired('Please select an Office document'),
        FileAllowed(['doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx'], 'Only Office documents are allowed')
    ])


class HTMLUploadForm(FileUploadForm):
    """Form for HTML file uploads."""

    file = FileField('Select HTML File', validators=[
        FileRequired('Please select an HTML file'),
        FileAllowed(['html', 'htm'], 'Only HTML files are allowed')
    ])


class ZipUploadForm(FileUploadForm):
    """Form for ZIP file uploads."""

    file = FileField('Select ZIP File', validators=[
        FileRequired('Please select a ZIP file'),
        FileAllowed(['zip'], 'Only ZIP files are allowed')
    ])


class CompressForm(PDFUploadForm):
    """Form for PDF compression."""

    compression_level = SelectField('Compression Level', choices=[
        ('screen', 'Screen (72 dpi)'),
        ('ebook', 'eBook (150 dpi)'),
        ('printer', 'Printer (300 dpi)'),
        ('prepress', 'Prepress (300 dpi, color preserving)'),
        ('default', 'Default')
    ], default='ebook')
    submit = SubmitField('Compress PDF')


class RepairForm(PDFUploadForm):
    """Form for PDF repair."""

    submit = SubmitField('Repair PDF')


class OCRForm(PDFUploadForm):
    """Form for OCR processing."""

    language = SelectField('OCR Language', choices=[
        ('eng', 'English'),
        ('fra', 'French'),
        ('deu', 'German'),
        ('spa', 'Spanish'),
        ('ita', 'Italian'),
        ('por', 'Portuguese'),
        ('rus', 'Russian'),
        ('chi_sim', 'Chinese (Simplified)'),
        ('chi_tra', 'Chinese (Traditional)'),
        ('jpn', 'Japanese'),
        ('kor', 'Korean')
    ], default='eng')
    submit = SubmitField('Perform OCR')


class ImageToPDFForm(ImageUploadForm):
    """Form for converting images to PDF."""

    page_size = SelectField('Page Size', choices=[
        ('a4', 'A4'),
        ('letter', 'Letter'),
        ('legal', 'Legal'),
        ('a3', 'A3'),
        ('a5', 'A5'),
        ('original', 'Original Image Size')
    ], default='a4')
    orientation = SelectField('Orientation', choices=[
        ('portrait', 'Portrait'),
        ('landscape', 'Landscape')
    ], default='portrait')
    submit = SubmitField('Convert to PDF')


class OfficeToPDFForm(OfficeUploadForm):
    """Form for converting Office documents to PDF."""

    submit = SubmitField('Convert to PDF')


class HTMLToPDFForm(HTMLUploadForm):
    """Form for converting HTML to PDF."""

    page_size = SelectField('Page Size', choices=[
        ('a4', 'A4'),
        ('letter', 'Letter'),
        ('legal', 'Legal'),
        ('a3', 'A3'),
        ('a5', 'A5')
    ], default='a4')
    orientation = SelectField('Orientation', choices=[
        ('portrait', 'Portrait'),
        ('landscape', 'Landscape')
    ], default='portrait')
    submit = SubmitField('Convert to PDF')


class ZipToPDFForm(ZipUploadForm):
    """Form for converting ZIP of images to PDF."""

    page_size = SelectField('Page Size', choices=[
        ('a4', 'A4'),
        ('letter', 'Letter'),
        ('legal', 'Legal'),
        ('a3', 'A3'),
        ('a5', 'A5'),
        ('original', 'Original Image Size')
    ], default='a4')
    orientation = SelectField('Orientation', choices=[
        ('portrait', 'Portrait'),
        ('landscape', 'Landscape')
    ], default='portrait')
    submit = SubmitField('Convert to PDF')


class PageNumbersForm(PDFUploadForm):
    """Form for adding page numbers to PDF."""

    position = SelectField('Position', choices=[
        ('bottom-center', 'Bottom Center'),
        ('bottom-right', 'Bottom Right'),
        ('bottom-left', 'Bottom Left'),
        ('top-center', 'Top Center'),
        ('top-right', 'Top Right'),
        ('top-left', 'Top Left')
    ], default='bottom-center')
    start_number = IntegerField('Start Number', default=1, validators=[
        NumberRange(min=1, message='Start number must be at least 1')
    ])
    font = SelectField('Font', choices=[
        ('helv', 'Helvetica'),
        ('tiro', 'Times Roman'),
        ('cour', 'Courier'),
        ('times', 'Times New Roman')
    ], default='helv')
    font_size = IntegerField('Font Size', default=12, validators=[
        NumberRange(min=6, max=72, message='Font size must be between 6 and 72')
    ])
    prefix = StringField('Prefix', default='')
    suffix = StringField('Suffix', default='')
    margin = IntegerField('Margin', default=36, validators=[
        NumberRange(min=0, max=100, message='Margin must be between 0 and 100')
    ])
    pages = StringField('Pages to Number', default='all', validators=[
        DataRequired('Please specify pages to number or "all"')
    ])
    submit = SubmitField('Add Page Numbers')


class WatermarkForm(PDFUploadForm):
    """Form for adding watermark to PDF."""

    text = StringField('Watermark Text', validators=[
        DataRequired('Please enter watermark text')
    ])
    position = SelectField('Position', choices=[
        ('center', 'Center'),
        ('top', 'Top'),
        ('bottom', 'Bottom'),
        ('left', 'Left'),
        ('right', 'Right'),
        ('top-left', 'Top Left'),
        ('top-right', 'Top Right'),
        ('bottom-left', 'Bottom Left'),
        ('bottom-right', 'Bottom Right')
    ], default='center')
    font = SelectField('Font', choices=[
        ('helv', 'Helvetica'),
        ('tiro', 'Times Roman'),
        ('cour', 'Courier'),
        ('times', 'Times New Roman')
    ], default='helv')
    font_size = IntegerField('Font Size', default=36, validators=[
        NumberRange(min=6, max=144, message='Font size must be between 6 and 144')
    ])
    opacity = IntegerField('Opacity', default=30, validators=[
        NumberRange(min=10, max=100, message='Opacity must be between 10 and 100')
    ])
    rotation = IntegerField('Rotation (degrees)', default=45, validators=[
        NumberRange(min=0, max=360, message='Rotation must be between 0 and 360 degrees')
    ])
    pages = StringField('Pages to Watermark', default='all', validators=[
        DataRequired('Please specify pages to watermark or "all"')
    ])
    submit = SubmitField('Add Watermark')


class ContentEditForm(PDFUploadForm):
    """Form for editing PDF content."""

    submit = SubmitField('Edit Content')


class MergeForm(FlaskForm):
    """Form for merging PDFs."""

    files = FileField('Select PDF Files', validators=[
        FileRequired('Please select at least one PDF file'),
        FileAllowed(['pdf'], 'Only PDF files are allowed')
    ])
    submit = SubmitField('Merge PDFs')


class SplitForm(PDFUploadForm):
    """Form for splitting PDF."""

    split_method = SelectField('Split Method', choices=[
        ('pages', 'Split into individual pages'),
        ('range', 'Split by page range'),
        ('size', 'Split by file size')
    ], default='pages')
    page_ranges = StringField('Page Ranges (e.g., 1-3,4-6)', validators=[Optional()])
    max_size = IntegerField('Maximum Size (MB)', default=10, validators=[
        Optional(),
        NumberRange(min=1, message='Size must be at least 1 MB')
    ])
    submit = SubmitField('Split PDF')


class ExtractForm(PDFUploadForm):
    """Form for extracting pages from PDF."""

    pages = StringField('Pages to Extract (e.g., 1,3,5-7)', validators=[
        DataRequired('Please specify pages to extract')
    ])
    submit = SubmitField('Extract Pages')


class RotateForm(PDFUploadForm):
    """Form for rotating PDF pages."""

    rotation = SelectField('Rotation', choices=[
        ('90', '90° Clockwise'),
        ('180', '180°'),
        ('270', '90° Counterclockwise')
    ], default='90')
    pages = StringField('Pages to Rotate (e.g., 1,3,5-7 or "all")', default='all', validators=[
        DataRequired('Please specify pages to rotate or "all"')
    ])
    submit = SubmitField('Rotate Pages')


class PDFToImageForm(PDFUploadForm):
    """Form for converting PDF to images."""

    format = SelectField('Image Format', choices=[
        ('jpg', 'JPEG'),
        ('png', 'PNG'),
        ('tiff', 'TIFF')
    ], default='jpg')
    dpi = IntegerField('Resolution (DPI)', default=150, validators=[
        NumberRange(min=72, max=600, message='DPI must be between 72 and 600')
    ])
    pages = StringField('Pages to Convert (e.g., 1,3,5-7 or "all")', default='all', validators=[
        DataRequired('Please specify pages to convert or "all"')
    ])
    submit = SubmitField('Convert to Images')


class PDFToPanoramicForm(PDFUploadForm):
    """Form for converting PDF to panoramic image."""

    format = SelectField('Image Format', choices=[
        ('jpg', 'JPEG'),
        ('png', 'PNG')
    ], default='jpg')
    dpi = IntegerField('Resolution (DPI)', default=150, validators=[
        NumberRange(min=72, max=600, message='DPI must be between 72 and 600')
    ])
    submit = SubmitField('Convert to Panoramic')


class PDFToPDFAForm(PDFUploadForm):
    """Form for converting PDF to PDF/A."""

    conformance = SelectField('Conformance Level', choices=[
        ('1b', 'PDF/A-1b (Basic)'),
        ('2b', 'PDF/A-2b (Basic)'),
        ('3b', 'PDF/A-3b (Basic)')
    ], default='1b')
    submit = SubmitField('Convert to PDF/A')


class UnlockForm(PDFUploadForm):
    """Form for unlocking password-protected PDF."""

    password = PasswordField('PDF Password', validators=[
        DataRequired('Please enter the PDF password')
    ])
    submit = SubmitField('Unlock PDF')


class ProtectForm(PDFUploadForm):
    """Form for protecting PDF with password."""

    user_password = PasswordField('User Password (for opening)', validators=[
        Optional()
    ])
    owner_password = PasswordField('Owner Password (for editing)', validators=[
        Optional()
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        Optional()
    ])

    # Permission settings
    allow_print = BooleanField('Allow Printing', default=True)
    allow_modify = BooleanField('Allow Content Modification', default=False)
    allow_copy = BooleanField('Allow Content Copying', default=True)
    allow_annotate = BooleanField('Allow Annotations', default=True)
    allow_forms = BooleanField('Allow Form Filling', default=True)
    allow_accessibility = BooleanField('Allow Accessibility Extraction', default=True)
    allow_assemble = BooleanField('Allow Document Assembly', default=False)
    allow_print_hq = BooleanField('Allow High-Quality Printing', default=True)

    submit = SubmitField('Protect PDF')


class RedactForm(PDFUploadForm):
    """Form for redacting content from PDF."""

    redaction_type = SelectField('Redaction Method', choices=[
        ('text', 'Text Search'),
        ('pattern', 'Regular Expression Pattern'),
        ('common_pattern', 'Common Pattern')
    ], default='text')

    search_text = StringField('Text to Redact', validators=[
        Optional()
    ])

    pattern = StringField('Regular Expression Pattern', validators=[
        Optional()
    ])

    common_pattern = SelectField('Common Pattern', choices=[
        ('email', 'Email Addresses'),
        ('phone', 'Phone Numbers'),
        ('ssn', 'Social Security Numbers'),
        ('credit_card', 'Credit Card Numbers'),
        ('date', 'Dates'),
        ('ip_address', 'IP Addresses'),
        ('url', 'URLs')
    ], default='email')

    case_sensitive = BooleanField('Case Sensitive', default=False)
    whole_words = BooleanField('Whole Words Only', default=True)
    submit = SubmitField('Redact PDF')


class FlattenForm(PDFUploadForm):
    """Form for flattening PDF form fields and annotations."""

    flatten_form_fields = BooleanField('Flatten Form Fields', default=True)
    flatten_annotations = BooleanField('Flatten Annotations', default=True)
    submit = SubmitField('Flatten PDF')


class PDFToTextForm(PDFUploadForm):
    """Form for extracting text from PDF."""

    pages = StringField('Pages to Extract Text From', default='all', validators=[
        DataRequired('Please specify pages to extract text from or "all"')
    ])
    include_page_numbers = BooleanField('Include Page Numbers', default=True)
    submit = SubmitField('Extract Text')


class PDFToPanoramicForm(PDFUploadForm):
    """Form for creating panoramic images from PDF pages."""

    format = SelectField('Image Format', choices=[
        ('jpg', 'JPEG (smaller file size)'),
        ('png', 'PNG (better quality)'),
        ('tiff', 'TIFF (highest quality)')
    ], default='jpg')

    dpi = IntegerField('Resolution (DPI)', default=300, validators=[
        NumberRange(min=72, max=600, message='Resolution must be between 72 and 600 DPI')
    ])

    direction = SelectField('Stitching Direction', choices=[
        ('horizontal', 'Horizontal (side by side)'),
        ('vertical', 'Vertical (stacked)')
    ], default='horizontal')

    spacing = IntegerField('Spacing Between Pages', default=0, validators=[
        NumberRange(min=0, max=100, message='Spacing must be between 0 and 100 pixels')
    ])

    pages = StringField('Pages to Include', default='all', validators=[
        DataRequired('Please specify pages to include or "all"')
    ])

    submit = SubmitField('Create Panoramic Image')


class ContentEditForm(PDFUploadForm):
    """Form for editing PDF content."""

    submit = SubmitField('Upload PDF')


class SignatureForm(PDFUploadForm):
    """Form for adding signatures to PDF."""

    submit = SubmitField('Upload PDF')


class LoginForm(FlaskForm):
    """Form for user login."""

    email = StringField('Email', validators=[
        DataRequired('Please enter your email'),
        Email('Please enter a valid email address')
    ])
    password = PasswordField('Password', validators=[
        DataRequired('Please enter your password')
    ])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Log In')


class RegisterForm(FlaskForm):
    """Form for user registration."""

    email = StringField('Email', validators=[
        DataRequired('Please enter your email'),
        Email('Please enter a valid email address')
    ])
    password = PasswordField('Password', validators=[
        DataRequired('Please enter a password'),
        Length(min=8, message='Password must be at least 8 characters long')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired('Please confirm your password'),
        EqualTo('password', message='Passwords must match')
    ])
    agree_terms = BooleanField('I agree to the Terms of Service', validators=[
        DataRequired('You must agree to the Terms of Service')
    ])
    submit = SubmitField('Register')
