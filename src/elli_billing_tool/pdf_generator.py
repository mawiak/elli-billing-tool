"""PDF form generator for reimbursement forms."""

from pathlib import Path
from datetime import datetime
from typing import Optional

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from PyPDF2 import PdfReader, PdfWriter
import io


def generate_reimbursement_form(
    template_path: Path,
    output_path: Path,
    total_kwh: float,
    kwh_price_cents: float,
    month: str,
    location: str = "Sankt Ingbert",
    date: Optional[datetime] = None,
) -> None:
    """
    Generate filled reimbursement form from template.

    Args:
        template_path: Path to the template PDF
        output_path: Path for the output PDF
        total_kwh: Total kWh consumed
        kwh_price_cents: Price per kWh in cents
        month: Month name (e.g., "November")
        location: Location for signature (default: "Sankt Ingbert")
        date: Date for signature (default: today)
    """
    if date is None:
        date = datetime.now()

    # Calculate total amount in Euro (rounded to 2 decimals)
    total_amount = round((total_kwh * kwh_price_cents) / 100, 2)

    # Create overlay PDF with form data
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=A4)
    can.setFont("Helvetica", 10)

    # Fill table fields
    # Format numbers with German decimal separator (comma instead of dot)
    kwh_str = f"{total_kwh:.2f}".replace(".", ",")
    amount_str = f"{total_amount:.2f}".replace(".", ",")

    can.drawString(80, 308, month)
    can.drawString(245, 308, kwh_str)
    can.drawString(380, 308, f"{amount_str} Euro")

    # Location/Date (Signature)
    date_str = f"{location}, {date.strftime('%d.%m.%Y')}"
    can.drawString(80, 200, date_str)

    can.save()

    # Merge with template
    packet.seek(0)
    overlay_pdf = PdfReader(packet)
    template_pdf = PdfReader(str(template_path))
    output = PdfWriter()

    page = template_pdf.pages[0]
    page.merge_page(overlay_pdf.pages[0])
    output.add_page(page)

    with open(output_path, "wb") as f:
        output.write(f)
