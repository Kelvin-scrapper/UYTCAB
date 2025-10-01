# UYTCAB - Automated PDF Data Extraction Pipeline

Automated pipeline for downloading and processing daily financial signal reports from Ueda Yagi Tanshi (上田八木短資).

## Overview

This project automates the process of:
1. Downloading the latest daily signal PDF report from [uedayagi.com](https://www.uedayagi.com/dailysignal)
2. Extracting fiscal forecast data from the PDF
3. Outputting structured data in CSV format

## Features

- **Automated PDF Download**: Uses undetected Chrome driver to download the most recent report
- **Universal PDF Parser**: Intelligently locates and extracts target data regardless of PDF layout variations
- **Structured Output**: Generates CSV with standardized headers and format
- **Pipeline Orchestration**: Single command to run the entire workflow

## Project Structure

```
UYTCAB/
├── orchestrator.py          # Main pipeline orchestrator
├── main.py                  # PDF download script
├── map.py                   # PDF data extraction and mapping script
├── requirements.txt         # Python dependencies
├── README.md               # This file
├── downloads/              # Downloaded PDFs (auto-created)
└── output_mapped_data.csv  # Final output (auto-generated)
```

## Installation

1. **Clone or download this repository**

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Chrome/Chromium** (required for web automation)

## Usage

### Quick Start - Run Full Pipeline

```bash
python orchestrator.py
```

This will:
1. Download the latest PDF report
2. Extract fiscal forecast data
3. Generate `output_mapped_data.csv`

### Run Individual Scripts

**Download PDF only**:
```bash
python main.py
```

**Process existing PDF**:
```bash
python map.py
```

## Configuration

### main.py Configuration

Edit the following variables in `main.py`:

```python
# Run browser in headless mode (True = no GUI, False = show browser)
HEADLESS = False

# Target website URL
BASE_URL = "https://www.uedayagi.com/dailysignal"
```

### map.py Configuration

Edit search keywords in `map.py` if PDF structure changes:

```python
# Row identifier keywords
TARGET_ROW_KEYWORDS = ['財政']

# Column identifier keywords
TARGET_COLUMN_KEYWORDS = ['当社需給予想', '需給予想']
```

## Output Format

The generated CSV file (`output_mapped_data.csv`) has the following structure:

```csv
,UYTCAB.DEMANDFORECAST.CHANGECURRBAL.JPN.B
,Supply and demand forecast: Change in current account balance
2025-10-03,-26000
```

**Format details**:
- Row 1: Header 1 (with empty first column)
- Row 2: Header 2 (with empty first column)
- Row 3+: Date (YYYY-MM-DD) and numeric value

## Data Extraction Logic

The pipeline extracts the following data point from each PDF:

- **Source Table**: 資金需給 (Money Supply/Demand)
- **Target Row**: 財政 (Fiscal/Treasury)
- **Target Column**: 当社需給予想 (Company Forecast)
- **Data**: Forecast value and associated date

## Troubleshooting

### PDF Download Issues

- Ensure Chrome/Chromium is installed
- Try setting `HEADLESS = False` in `main.py` to see the browser
- Check internet connection

### PDF Parsing Issues

- The parser uses keyword-based search and is resilient to layout changes
- If extraction fails, check that the PDF contains the target keywords (財政, 当社需給予想)
- PDF warnings about gray colors can be ignored (cosmetic only)

### Dependencies Issues

```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

## Technical Details

### Technologies Used

- **Python 3.7+**
- **Selenium + undetected-chromedriver**: Web automation and bot detection bypass
- **pdfplumber**: PDF text and table extraction
- **pandas**: Data manipulation and CSV output

### Key Scripts

**orchestrator.py**:
- Coordinates the pipeline execution
- Handles errors and provides progress feedback

**main.py**:
- Automated Chrome browser control
- Locates and downloads the most recent PDF report
- Multiple fallback strategies for finding download buttons

**map.py**:
- Universal PDF table parser
- Keyword-based data location
- Multi-format date extraction
- Custom CSV formatting

## License

This project is for educational and research purposes.

## Support

For issues or questions, please check:
- PDF structure matches expected format
- All dependencies are installed correctly
- Chrome browser is up to date
