# RevisePDF

A full-featured PDF processing website built with Python and Flask.

## Features

RevisePDF provides a comprehensive suite of PDF processing tools, including:

### Optimize
- **Compress**: Reduce PDF file size while maintaining quality
- **Repair**: Fix corrupted or damaged PDF files
- **OCR**: Add text recognition to scanned PDFs

### Convert to PDF
- **JPG to PDF**: Convert images to PDF
- **Word/PPT/Excel to PDF**: Convert Office documents to PDF
- **HTML to PDF**: Convert HTML to PDF
- **ZIP of Images to PDF**: Convert a ZIP file containing images to a multipage PDF

### Edit
- **Page Numbers**: Add page numbers to PDF
- **Watermark**: Add text watermarks to PDF
- **Edit Content**: Basic editing of PDF content

### Organize
- **Merge**: Combine multiple PDFs into one
- **Split**: Split a PDF into multiple files
- **Extract**: Extract specific pages from a PDF
- **Rotate**: Rotate pages in a PDF

### Convert from PDF
- **PDF to JPG**: Convert PDF pages to images
- **PDF to Panoramic**: Create panoramic images from PDF pages
- **PDF to PDF/A**: Convert standard PDFs to PDF/A format

### Security
- **Unlock**: Remove password protection from PDFs
- **Protect**: Add password protection to PDFs
- **Redact**: Redact sensitive information from PDFs
- **Flatten**: Flatten form fields in PDFs

## Technology Stack

- **Backend**: Python, Flask
- **PDF Processing**: PyMuPDF, Ghostscript, Tesseract OCR
- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **Deployment**: Heroku

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/revisepdf.git
   cd revisepdf
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up Ghostscript:
   ```
   python setup_ghostscript.py
   ```
   This script will download and extract the Ghostscript source code to the `ghostscript` directory.

   Alternatively, if you already have Ghostscript installed on your system, the application will use that installation.

5. Set up environment variables:
   ```
   export FLASK_APP=run.py
   export FLASK_ENV=development
   ```
   On Windows (PowerShell):
   ```
   $env:FLASK_APP = "run.py"
   $env:FLASK_ENV = "development"
   ```

6. Run the application:
   ```
   flask run
   ```

## Project Structure

```
/revisepdf/
├── app/                  # Flask application
│   ├── __init__.py       # Flask app initialization
│   ├── routes.py         # Route definitions
│   ├── forms.py          # Form definitions
│   ├── errors.py         # Error handlers
│   ├── config.py         # Configuration settings
│   ├── static/           # Static files (CSS, JS, images)
│   └── templates/        # HTML templates
├── tools/                # PDF processing tools
│   ├── optimize/         # Optimization tools
│   ├── convert_to_pdf/   # Conversion to PDF tools
│   ├── edit/             # PDF editing tools
│   ├── organize/         # PDF organization tools
│   ├── convert_from_pdf/ # Conversion from PDF tools
│   └── security/         # PDF security tools
├── ghostscript/          # Local Ghostscript source
│   ├── ghostscript-x.xx.x/ # Ghostscript source code
│   └── README.md          # Ghostscript integration documentation
├── instance/             # Instance-specific files
│   ├── uploads/          # Uploaded files
│   └── temp/             # Temporary files
├── tests/                # Unit tests
├── .gitignore            # Git ignore file
├── requirements.txt      # Python dependencies
├── Procfile              # Heroku Procfile
├── runtime.txt           # Python runtime for Heroku
├── run.py                # Application entry point
├── setup_ghostscript.py  # Script to download and extract Ghostscript
└── test_ghostscript.py   # Script to test Ghostscript setup
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [PyMuPDF](https://github.com/pymupdf/PyMuPDF) for PDF processing
- [Ghostscript](https://www.ghostscript.com/) for PDF compression and conversion
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) for optical character recognition
- [Flask](https://flask.palletsprojects.com/) for the web framework
- [Bootstrap](https://getbootstrap.com/) for the frontend framework
