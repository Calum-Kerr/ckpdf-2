# Ghostscript Integration for RevisePDF

This directory contains the Ghostscript source code used by RevisePDF for PDF processing operations such as compression, repair, and PDF/A conversion.

## About Ghostscript

Ghostscript is a high-quality, open-source interpreter for PostScript and PDF files. It's used in RevisePDF for various PDF processing tasks, particularly for optimizing and converting PDF files.

## Directory Structure

The Ghostscript source code is organized as follows:

```
/ghostscript/
├── ghostscript-x.xx.x/  # Ghostscript source code (version-specific)
│   ├── base/           # Core Ghostscript files
│   ├── devices/        # Output device implementations
│   ├── doc/            # Documentation
│   ├── lib/            # PostScript library files
│   ├── ...             # Other Ghostscript directories
└── README.md           # This file
```

## How RevisePDF Uses Ghostscript

RevisePDF uses Ghostscript for the following operations:

1. **PDF Compression**: Reducing the file size of PDF documents while maintaining acceptable quality
2. **PDF Repair**: Fixing corrupted or damaged PDF files
3. **PDF/A Conversion**: Converting standard PDFs to PDF/A format for long-term archiving

## Ghostscript Detection

The application will look for Ghostscript in the following order:

1. First, it checks for a local Ghostscript installation in the `ghostscript/` directory
2. If not found locally, it looks for Ghostscript in the system PATH

## Building Ghostscript (Optional)

If you need to build Ghostscript from source:

### On Windows:

1. Navigate to the Ghostscript source directory:
   ```
   cd ghostscript/ghostscript-x.xx.x
   ```

2. Build using Visual Studio:
   ```
   nmake -f psi/msvc32.mak
   ```

### On Linux/macOS:

1. Navigate to the Ghostscript source directory:
   ```
   cd ghostscript/ghostscript-x.xx.x
   ```

2. Configure and build:
   ```
   ./configure
   make
   ```

## License

Ghostscript is licensed under the GNU Affero General Public License (AGPL). See the LICENSE file in the Ghostscript source directory for details.
