"""
Command-line interface for the Elli Billing Tool.
"""

import sys
import argparse
import locale
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

from .config import Config, ConfigError
from .elli_service import ElliService
from .pdf_parser import extract_total_kwh
from .pdf_generator import generate_reimbursement_form
from .mail_generator import load_mail_template


class CLI:
    """
    Command-line interface handler.
    """

    def __init__(self, config: Config):
        """
        Initialize CLI with configuration.

        Args:
            config: Application configuration.
        """
        self.config = config

    def list_resources(self) -> None:
        """
        List all available stations and RFID cards.
        """
        print("Connecting to Elli API...")

        with ElliService(self.config.username, self.config.password) as service:
            print("\n=== Charging Stations ===")
            stations = service.get_stations()

            if not stations:
                print("No stations found.")
            else:
                for station in stations:
                    print(f"\nStation ID: {station.id}")
                    if hasattr(station, 'name') and station.name:
                        print(f"  Name: {station.name}")
                    if hasattr(station, 'serial_number') and station.serial_number:
                        print(f"  Serial: {station.serial_number}")

            print("\n=== RFID Cards (from Charging Sessions) ===")
            sessions = service.get_charging_sessions()

            rfid_cards = {}
            for session in sessions:
                if session.rfid_card_id and session.rfid_card_id not in rfid_cards:
                    rfid_cards[session.rfid_card_id] = session.rfid_card_serial_number

            if not rfid_cards:
                print("No RFID cards found in charging sessions.")
            else:
                for card_id, serial in rfid_cards.items():
                    print(f"\nRFID Card ID: {card_id}")
                    if serial:
                        print(f"  Serial: {serial}")

        print("\nUse these IDs in your .env file:")
        print("  ELLI_STATION_ID=<station-id>")
        print("  ELLI_RFID_CARD_ID=<rfid-card-id>")

    def generate_form(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        output_dir: Optional[Path] = None
    ) -> tuple[Path, Path]:
        """
        Generate filled reimbursement form.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            output_dir: Directory for output. Defaults to ./output

        Returns:
            Tuple of (reimbursement_form_path, charging_pdf_path)
        """
        # Template must be in template/ directory with fixed name
        template = Path("template/Template_Abrechnungsformular-Energiekosten-Firmenwagen-zuhause.pdf")

        if not template.exists():
            raise FileNotFoundError(
                f"Template not found: {template}\n"
                "Please place your template PDF at: template/Template_Abrechnungsformular-Energiekosten-Firmenwagen-zuhause.pdf"
            )

        # Calculate default dates (last month) if not provided
        if not start_date or not end_date:
            today = datetime.now()
            first_of_current_month = today.replace(day=1)
            last_day_of_last_month = first_of_current_month - timedelta(days=1)
            first_of_last_month = last_day_of_last_month.replace(day=1)

            start_date = start_date or first_of_last_month.strftime("%Y-%m-%d")
            end_date = end_date or last_day_of_last_month.strftime("%Y-%m-%d")

        # Determine month from date range
        month_date = datetime.strptime(start_date, "%Y-%m-%d")

        # Create output directory structure: output/YYYY/MM/
        if not output_dir:
            output_dir = Path("output")

        year_dir = output_dir / str(month_date.year)
        month_dir = year_dir / f"{month_date.month:02d}"
        month_dir.mkdir(parents=True, exist_ok=True)

        # Download charging records PDF to month directory
        filename = f"charging_records_{start_date}_to_{end_date}.pdf"
        charging_pdf = month_dir / filename

        print(f"Downloading charging records from {start_date} to {end_date}...")
        print(f"Station ID: {self.config.station_id}")
        print(f"RFID Card ID: {self.config.rfid_card_id}")

        with ElliService(self.config.username, self.config.password) as service:
            pdf_content = service.get_charging_records_pdf(
                station_id=self.config.station_id,
                rfid_card_id=self.config.rfid_card_id,
                start_date=start_date,
                end_date=end_date
            )

            with open(charging_pdf, 'wb') as f:
                f.write(pdf_content)

        print(f"PDF saved to: {charging_pdf}")

        # Extract total kWh
        print(f"\nExtracting data from {charging_pdf}...")
        total_kwh = extract_total_kwh(charging_pdf)
        print(f"Total consumption: {total_kwh} kWh")

        # Calculate amount
        total_amount = round((total_kwh * self.config.kwh_price_cents) / 100, 2)
        print(f"Price: {self.config.kwh_price_cents} ct/kWh")
        print(f"Total amount: {total_amount} Euro")

        # Get German month name
        old_locale = locale.getlocale(locale.LC_TIME)
        try:
            locale.setlocale(locale.LC_TIME, 'de_DE.UTF-8')
            month_name_de = month_date.strftime("%B")
        finally:
            locale.setlocale(locale.LC_TIME, old_locale)

        # Generate output filename from template name (remove "Template_" prefix)
        template_name = template.stem  # e.g., "Template_Abrechnungsformular-..."
        if template_name.startswith("Template_"):
            form_name = template_name[9:]  # Remove "Template_" prefix
        else:
            form_name = template_name

        output_path = month_dir / f"{form_name}.pdf"

        # Generate form
        print(f"\nGenerating reimbursement form...")
        generate_reimbursement_form(
            template_path=template,
            output_path=output_path,
            total_kwh=total_kwh,
            kwh_price_cents=self.config.kwh_price_cents,
            month=month_name_de,
            location=self.config.location
        )

        print(f"Form saved to: {output_path}")
        print(f"\nAll files saved to: {month_dir}")

        # Open email client
        self._send_email_mailto(
            reimbursement_form=output_path,
            charging_pdf=charging_pdf,
            month_name=month_name_de,
            year=month_date.year,
            output_folder=month_dir
        )

        return output_path, charging_pdf

    def _send_email_mailto(
        self,
        reimbursement_form: Path,
        charging_pdf: Path,
        month_name: str,
        year: int,
        output_folder: Path
    ) -> None:
        """
        Open email client with mailto link and output folder for drag & drop.

        Args:
            reimbursement_form: Path to generated reimbursement form
            charging_pdf: Path to Elli charging records PDF
            month_name: Month name in German
            year: Year
            output_folder: Folder containing the files
        """
        import webbrowser
        from urllib.parse import quote

        # Load and fill mail template
        template_path = Path("template/mail.txt")
        placeholders = {
            "MONTH": month_name,
            "YEAR": str(year),
            "NAME": self.config.email_name
        }

        body = load_mail_template(template_path, placeholders)

        # Replace placeholders in subject
        subject = self.config.email_subject
        for placeholder, value in placeholders.items():
            subject = subject.replace(f"{{{placeholder}}}", value)

        # Build mailto URL
        to = ",".join(self.config.email_recipients)
        mailto = f"mailto:{to}"

        params = []
        if self.config.email_cc and self.config.email_cc[0]:
            params.append(f"cc={quote(','.join(self.config.email_cc))}")
        params.append(f"subject={quote(subject)}")
        params.append(f"body={quote(body)}")

        if params:
            mailto += "?" + "&".join(params)

        # Open mailto link
        print("\nOpening email client...")
        print(f"To: {', '.join(self.config.email_recipients)}")
        if self.config.email_cc and self.config.email_cc[0]:
            print(f"CC: {', '.join(self.config.email_cc)}")
        print(f"Subject: {subject}")

        webbrowser.open(mailto)

        # Open output folder
        import subprocess
        import platform

        print(f"\nOpening folder with attachments: {output_folder.resolve()}")
        system = platform.system()
        if system == "Darwin":  # macOS
            subprocess.run(["open", str(output_folder.resolve())])
        elif system == "Windows":
            subprocess.run(["explorer", str(output_folder.resolve())])
        elif system == "Linux":
            subprocess.run(["xdg-open", str(output_folder.resolve())])

        print("\nPlease drag & drop these files into your email:")
        print(f"  - {reimbursement_form.name}")
        print(f"  - {charging_pdf.name}")


def main() -> None:
    """
    Main entry point for the CLI application.
    """
    parser = argparse.ArgumentParser(
        description="Elli Billing Tool - Automate charging report generation"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # List command
    subparsers.add_parser(
        "list",
        help="List all available stations and RFID cards"
    )

    # Generate command
    generate_parser = subparsers.add_parser(
        "generate",
        help="Generate filled reimbursement form"
    )
    generate_parser.add_argument(
        "--start-date",
        help="Start date (YYYY-MM-DD). Defaults to first day of last month."
    )
    generate_parser.add_argument(
        "--end-date",
        help="End date (YYYY-MM-DD). Defaults to last day of last month."
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        config = Config.load_from_file()
        cli = CLI(config)

        if args.command == "list":
            cli.list_resources()

        elif args.command == "generate":
            cli.generate_form(
                start_date=args.start_date,
                end_date=args.end_date
            )

    except ConfigError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
