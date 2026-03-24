"""
extract_pdf.py
Extract ride data table from a PDF file and save to CSV.

Usage:
    python extract_pdf.py                             # auto-discovers PDF in same folder
    python extract_pdf.py --pdf path/to/file.pdf
    python extract_pdf.py --pdf file.pdf --out output.csv
"""
import argparse
from pathlib import Path

import pandas as pd
import pdfplumber


def extract_first_table(pdf_path: Path, out_csv: Path) -> None:
    """Extract the first table from the first page of a PDF and save as CSV."""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            if not tables:
                print(f"No tables found on page {page.page_number}")
                continue
            table = tables[0]
            df = pd.DataFrame(table[1:], columns=table[0])  # first row = header
            df.to_csv(out_csv, index=False)
            print(f"Extracted {len(df)} rows -> {out_csv}")
            return
    print("No tables found in the PDF.")


def parse_args():
    # BUG FIX: was a hardcoded Windows path  d:\urbanblack-aiml\...\dataset - Sheet1.pdf
    # Now accepts a CLI argument or auto-discovers a PDF in the same directory.
    p = argparse.ArgumentParser(description="Extract table from PDF to CSV")
    here = Path(__file__).parent
    p.add_argument(
        "--pdf",
        type=Path,
        default=None,
        help="Path to the input PDF (default: first .pdf found in script directory)",
    )
    p.add_argument(
        "--out",
        type=Path,
        default=here / "extracted_dataset.csv",
        help="Output CSV path (default: extracted_dataset.csv in script directory)",
    )
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()

    pdf_path = args.pdf
    if pdf_path is None:
        # Auto-discover the first PDF in the same folder
        candidates = list(Path(__file__).parent.glob("*.pdf"))
        if not candidates:
            raise FileNotFoundError(
                "No PDF found in script directory. "
                "Pass --pdf <path> to specify the file."
            )
        pdf_path = candidates[0]
        print(f"Auto-discovered PDF: {pdf_path}")

    extract_first_table(pdf_path, args.out)
