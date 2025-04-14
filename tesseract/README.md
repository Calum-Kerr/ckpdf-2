# Tesseract OCR Integration

This directory contains the Tesseract OCR integration for RevisePDF.

## Directory Structure

- `bin/`: Contains the Tesseract executable and related DLLs
- `tessdata/`: Contains language data files for OCR

## Setup Instructions

### Option 1: Install Tesseract on Your System (Recommended)

1. Download Tesseract from [UB-Mannheim's GitHub repository](https://github.com/UB-Mannheim/tesseract/wiki)
2. Install it to your system (the default installation location is usually fine)
3. The application will automatically detect the installed Tesseract

### Option 2: Use Bundled Tesseract

1. Download Tesseract from [UB-Mannheim's GitHub repository](https://github.com/UB-Mannheim/tesseract/wiki)
2. Extract the following files to the `bin/` directory:
   - `tesseract.exe`
   - All required DLL files
3. Download language data files from [tesseract-ocr/tessdata](https://github.com/tesseract-ocr/tessdata) and place them in the `tessdata/` directory

## Language Data Files

At minimum, you need the following language data files in the `tessdata/` directory:

- `eng.traineddata` (English)
- `osd.traineddata` (Orientation and script detection)

Additional languages can be added by downloading the corresponding `.traineddata` files.

## Supported Languages

The OCR tool supports the following languages:

- English (eng)
- French (fra)
- German (deu)
- Spanish (spa)
- Italian (ita)
- Portuguese (por)
- Russian (rus)
- Chinese Simplified (chi_sim)
- Chinese Traditional (chi_tra)
- Japanese (jpn)
- Korean (kor)

## Note for Developers

The Tesseract binary files and language data files are excluded from version control. When deploying the application, you'll need to:

1. Include the necessary Tesseract files in your deployment package, or
2. Ensure Tesseract is installed on the server

The application will work without Tesseract, but OCR functionality will be limited.
