import pdfplumber
import re
from datetime import datetime
import pandas as pd
import os

# ============================================================
# CONFIGURATION - Hardcoded headers and search terms
# ============================================================

# Output headers (these will always be present in the output)
HEADER_1 = "UYTCAB.DEMANDFORECAST.CHANGECURRBAL.JPN.B"
HEADER_2 = "Supply and demand forecast: Change in current account balance"

# Search configuration (can be adjusted for different documents)
TARGET_ROW_KEYWORDS = ['財政']  # Row identifier keywords
TARGET_COLUMN_KEYWORDS = ['当社需給予想', '需給予想']  # Column identifier keywords

# ============================================================
# UNIVERSAL DATA EXTRACTION FUNCTIONS
# ============================================================

def extract_date_from_pdf(pdf_path):
    """
    UNIVERSAL: Extract document date from PDF header
    Supports multiple date formats:
    - Japanese: 2025年10月1日
    - Dot format: 2024.05.16
    - Slash format: 2024/05/16
    """
    with pdfplumber.open(pdf_path) as pdf:
        first_page = pdf.pages[0]
        text = first_page.extract_text()

        # Pattern 1: Japanese format "2025年10月1日"
        date_pattern1 = r'(\d{4})年(\d{1,2})月(\d{1,2})日'
        match = re.search(date_pattern1, text)
        if match:
            year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
            return datetime(year, month, day)

        # Pattern 2: Dot format "2024.05.16"
        date_pattern2 = r'(\d{4})\.(\d{1,2})\.(\d{1,2})'
        match = re.search(date_pattern2, text)
        if match:
            year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
            return datetime(year, month, day)

        # Pattern 3: Slash format "2024/05/16"
        date_pattern3 = r'(\d{4})/(\d{1,2})/(\d{1,2})'
        match = re.search(date_pattern3, text)
        if match:
            year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
            return datetime(year, month, day)

    return None

def extract_forecast_date_universal(table, header_row_idx, col_idx, pdf_path):
    """
    UNIVERSAL: Extract forecast date from table
    Searches in multiple locations:
    1. Same cell as column header
    2. Row above/below header
    3. Date column if exists
    """
    doc_date = extract_date_from_pdf(pdf_path)
    if not doc_date:
        return None

    year = doc_date.year

    # Strategy 1: Check the header cell itself
    if header_row_idx < len(table):
        header_row = table[header_row_idx]
        if col_idx < len(header_row) and header_row[col_idx]:
            cell_text = str(header_row[col_idx])
            date = extract_date_from_cell(cell_text, year)
            if date:
                return date

    # Strategy 2: Check rows around the header for date info (prioritize row below)
    for offset in [1, -1, 2, -2, 3]:
        check_row_idx = header_row_idx + offset
        if 0 <= check_row_idx < len(table):
            row = table[check_row_idx]
            if col_idx < len(row) and row[col_idx]:
                cell_text = str(row[col_idx])
                date = extract_date_from_cell(cell_text, year)
                if date:
                    return date

    # Strategy 3: Look for date in rows above header
    for row_idx in range(max(0, header_row_idx - 5), header_row_idx):
        if row_idx < len(table):
            row = table[row_idx]
            if col_idx < len(row) and row[col_idx]:
                cell_text = str(row[col_idx])
                date = extract_date_from_cell(cell_text, year)
                if date:
                    return date

    return None

def extract_date_from_cell(cell_text, year):
    """
    UNIVERSAL: Extract date from cell text
    Handles various formats: 7月16日, 10月3日, etc.
    Converts to YYYY-MM-DD format
    """
    if not cell_text:
        return None

    # Japanese date format: "10月3日"
    date_pattern = r'(\d{1,2})月(\d{1,2})日'
    match = re.search(date_pattern, cell_text)

    if match:
        month = int(match.group(1))
        day = int(match.group(2))
        try:
            date_obj = datetime(year, month, day)
            return date_obj.strftime('%Y-%m-%d')
        except ValueError:
            return None

    return None

def clean_numeric_value(value_str):
    """
    UNIVERSAL: Clean numeric value from various formats
    Handles:
    - Japanese negative symbol: ▲
    - Plus signs: +
    - Commas: ,
    - Spaces and other separators
    """
    if not value_str:
        return None

    value_str = str(value_str).strip()

    # Check for negative indicators
    is_negative = '▲' in value_str or value_str.startswith('-')

    # Check for positive indicator (remove it)
    value_str = value_str.replace('+', '')

    # Remove all non-digit characters
    value_str = re.sub(r'[^\d]', '', value_str)

    if not value_str:
        return None

    # Convert to integer
    try:
        value = int(value_str)
        if is_negative and value > 0:
            value = -value
        return value
    except ValueError:
        return None

def find_fiscal_forecast_value(pdf_path):
    """
    UNIVERSAL FINDER: Find target data by row and column keywords

    This function searches ALL tables in the PDF and finds:
    1. A row containing any TARGET_ROW_KEYWORDS (e.g., '財政')
    2. A column containing any TARGET_COLUMN_KEYWORDS (e.g., '当社需給予想')
    3. Returns the intersection value and associated date

    Returns:
        tuple: (value, date_string) or (None, None) if not found
    """
    with pdfplumber.open(pdf_path) as pdf:
        first_page = pdf.pages[0]
        tables = first_page.extract_tables()

        for table_idx, table in enumerate(tables):
            if not table or len(table) < 2:
                continue

            # Step 1: Find all potential header rows
            header_candidates = []
            for row_idx in range(min(40, len(table))):  # Check first 40 rows
                row = table[row_idx]
                if row:
                    # Check if this row contains any column keywords
                    for cell in row:
                        if cell and any(keyword in str(cell) for keyword in TARGET_COLUMN_KEYWORDS):
                            header_candidates.append((row_idx, row))
                            break

            # Step 2: Find target data row (containing TARGET_ROW_KEYWORDS)
            target_row_idx = None
            target_row = None

            for row_idx, row in enumerate(table):
                if row:
                    # Check if any cell in this row contains target keywords
                    for cell in row:
                        if cell and any(keyword in str(cell) for keyword in TARGET_ROW_KEYWORDS):
                            target_row_idx = row_idx
                            target_row = row
                            break
                    if target_row_idx is not None:
                        break

            if target_row_idx is None or not target_row:
                continue

            # Step 3: Find intersection of target row and target column
            for header_idx, header_row in header_candidates:
                if header_idx >= target_row_idx:
                    # Header should be above the data row
                    continue

                for col_idx, cell in enumerate(header_row):
                    if cell and any(keyword in str(cell) for keyword in TARGET_COLUMN_KEYWORDS):
                        # Found target column! Extract the value
                        if col_idx < len(target_row):
                            value_cell = target_row[col_idx]

                            # Handle None or empty cells
                            if value_cell is None or not str(value_cell).strip():
                                continue

                            # Clean the numeric value
                            value = clean_numeric_value(value_cell)

                            if value is None:
                                continue

                            # Extract associated date
                            date_str = extract_forecast_date_universal(
                                table, header_idx, col_idx, pdf_path
                            )

                            if value is not None and date_str is not None:
                                return value, date_str

    return None, None

# ============================================================
# DATA MAPPING AND OUTPUT FUNCTIONS
# ============================================================

def create_mapped_data(pdf_path):
    """
    UNIVERSAL: Create mapped data with hardcoded headers

    Returns:
        dict: Dictionary with HEADER_1 (date) and HEADER_2 (value)
    """
    value, forecast_date = find_fiscal_forecast_value(pdf_path)

    if value is None or forecast_date is None:
        print(f"[!] Warning: Could not extract data from {os.path.basename(pdf_path)}")
        return None

    data = {
        HEADER_1: forecast_date,
        HEADER_2: value
    }

    return data

def process_pdf(pdf_path, output_format='dict'):
    """
    UNIVERSAL: Process a single PDF and return mapped data

    Args:
        pdf_path: Path to PDF file
        output_format: 'dict', 'dataframe', or 'csv'

    Returns:
        Mapped data in requested format
    """
    print(f"[*] Processing: {os.path.basename(pdf_path)}")

    data = create_mapped_data(pdf_path)

    if data is None:
        return None

    if output_format == 'dict':
        return data

    elif output_format == 'dataframe':
        df = pd.DataFrame([data])
        return df

    elif output_format == 'csv':
        df = pd.DataFrame([data])
        return df.to_csv(index=False)

    return data

def process_multiple_pdfs(pdf_folder, output_csv=None):
    """
    UNIVERSAL: Process multiple PDFs from a folder

    Args:
        pdf_folder: Folder containing PDF files
        output_csv: Optional output CSV file path

    Returns:
        DataFrame with all mapped data
    """
    all_data = []

    # Find all PDF files
    pdf_files = sorted([f for f in os.listdir(pdf_folder) if f.endswith('.pdf')])

    print(f"[*] Found {len(pdf_files)} PDF file(s) in {pdf_folder}")
    print("=" * 60)

    for pdf_file in pdf_files:
        pdf_path = os.path.join(pdf_folder, pdf_file)
        data = create_mapped_data(pdf_path)

        if data:
            all_data.append(data)
            print(f"[+] {pdf_file}: Date={data[HEADER_1]}, Value={data[HEADER_2]:,}")
        else:
            print(f"[-] {pdf_file}: Failed to extract data")

    print("=" * 60)

    # Create DataFrame
    if all_data:
        df = pd.DataFrame(all_data)

        # Reorder columns to match required format:
        # Column 1: HEADER_1 (date)
        # Column 2: HEADER_2 (value)
        df = df[[HEADER_1, HEADER_2]]

        # Save to CSV if requested
        if output_csv:
            save_custom_csv(df, output_csv)
            print(f"[*] Saved to: {output_csv}")

        return df
    else:
        print("[!] No data extracted from any PDF")
        return pd.DataFrame()

def save_custom_csv(df, output_path):
    """
    Save DataFrame to CSV in custom format:
    - Row 1: Empty cell, HEADER_1
    - Row 2: Empty cell, HEADER_2
    - Row 3+: Date (YYYY-MM-DD), Value
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        # Write header rows
        f.write(f",{HEADER_1}\n")
        f.write(f",{HEADER_2}\n")

        # Write data rows
        for _, row in df.iterrows():
            date_value = row[HEADER_1]
            numeric_value = row[HEADER_2]
            f.write(f"{date_value},{numeric_value}\n")

# ============================================================
# MAIN EXECUTION
# ============================================================

def main():
    """Main function for testing"""
    print("=" * 60)
    print("UNIVERSAL PDF MAPPER - UYTCAB")
    print("=" * 60)

    # Test with single PDF
    pdf_path = r"C:\Users\Execo Training\Desktop\UYTCAB\downloads\ds251001.pdf"

    if os.path.exists(pdf_path):
        print("\n[*] Testing single PDF processing...\n")

        result = process_pdf(pdf_path, output_format='dict')
        if result:
            print(f"\n[+] Result:")
            print(f"  {HEADER_1}: {result[HEADER_1]}")
            print(f"  {HEADER_2}: {result[HEADER_2]:,}")
    else:
        print(f"\n[!] PDF not found: {pdf_path}")

    # Test with multiple PDFs
    downloads_folder = r"C:\Users\Execo Training\Desktop\UYTCAB\downloads"
    if os.path.exists(downloads_folder):
        print("\n" + "=" * 60)
        print("[*] Processing all PDFs in downloads folder...\n")

        df = process_multiple_pdfs(
            downloads_folder,
            output_csv="output_mapped_data.csv"
        )

        if not df.empty:
            print(f"\n[*] Final DataFrame ({len(df)} rows):")
            print(df.to_string(index=False))

if __name__ == "__main__":
    main()
