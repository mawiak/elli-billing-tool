"""PDF parsing utilities for extracting charging data."""

import re
from pathlib import Path
from PyPDF2 import PdfReader


def extract_total_kwh(pdf_path: Path) -> float:
    """
    Extract total consumption in kWh from charging PDF.

    Args:
        pdf_path: Path to the charging history PDF file.

    Returns:
        Total consumption in kWh.

    Raises:
        ValueError: If total consumption cannot be found in PDF.
    """
    reader = PdfReader(str(pdf_path))

    if len(reader.pages) == 0:
        raise ValueError("PDF has no pages")

    text = reader.pages[0].extract_text()
    match = re.search(r"Total consumption:\s*(\d+(?:\.\d+)?)\s*kWh", text)

    if not match:
        raise ValueError("Could not find 'Total consumption' in PDF")

    return float(match.group(1))
