# Elli Billing Tool

Automated charging report generation for company car reimbursement.

This tool uses the `elli-client` package to download monthly charging records from your Elli wallbox and automatically generate filled reimbursement forms.

## Features

- List all available charging stations and RFID cards
- Download charging records as PDF for any date range with correct timezone handling
- Extract total kWh from charging records
- Automatically fill reimbursement form template with calculated costs
- German number formatting (commas for decimals)
- German month names using locale

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd elli-billing-tool
```

2. Create a virtual environment and install dependencies:
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .
```

3. Place your reimbursement form template PDF in the `template` folder with the name:
   `Template_Abrechnungsformular-Energiekosten-Firmenwagen-zuhause.pdf`

4. Configure your environment variables:
```bash
cp .env.example .env
# Edit .env with your credentials
```

## Configuration

Copy `.env.example` to `.env` and fill in your details:

### Required Configuration

- `ELLI_EMAIL`: Your Elli account email
- `ELLI_PASSWORD`: Your Elli account password
- `ELLI_STATION_ID`: Your charging station ID (use `list` command to find it)
- `ELLI_RFID_CARD_ID`: Your RFID card ID (use `list` command to find it)
- `ELLI_KWH_PRICE_CENTS`: Price per kWh in cents (e.g., 33.33 for 0.3333 EUR)
- `ELLI_LOCATION`: Location for signature on form (e.g., Sankt Ingbert)

### Email Configuration

- `EMAIL_SUBJECT`: Email subject line (supports placeholders: {MONTH}, {YEAR}, {NAME})
- `EMAIL_RECIPIENTS`: Comma-separated list of recipient email addresses
- `EMAIL_CC`: Comma-separated list of CC email addresses (optional)
- `EMAIL_NAME`: Your name for email signature

## Usage

### List available stations and RFID cards

```bash
python -m elli_billing_tool.cli list
```

This will show all your charging stations and RFID cards with their IDs.

### Generate filled reimbursement form

Generate form for last month (default):
```bash
python -m elli_billing_tool.cli generate
```

Generate for specific date range:
```bash
python -m elli_billing_tool.cli generate --start-date 2025-11-01 --end-date 2025-11-30
```

This will:
1. Download the charging records PDF from Elli
2. Extract the total kWh consumption
3. Calculate the reimbursement amount
4. Fill the template PDF with:
   - Month name (in German)
   - Total kWh (with German decimal formatting)
   - Total amount in EUR (with German decimal formatting)
   - Current date and location
5. Save both PDFs to `output/YYYY/MM/`
6. Open your email client with pre-filled email (recipients, CC, subject, body)
7. Open the output folder so you can drag & drop the PDFs into the email

**Note:** The tool automatically converts dates to UTC timestamps to ensure all charging sessions are captured, including those started late in the evening.

## Development

The project structure:

```
elli-billing-tool/
├── src/
│   └── elli_billing_tool/
│       ├── __init__.py
│       ├── cli.py              # Command-line interface
│       ├── config.py           # Configuration management
│       ├── elli_service.py     # Elli API wrapper
│       ├── pdf_parser.py       # PDF parsing (extract kWh)
│       ├── pdf_generator.py    # PDF form generation
│       └── mail_generator.py   # Email template handling
├── template/                   # PDF template folder
│   ├── mail.txt               # Email template
│   └── Template_Abrechnungsformular-Energiekosten-Firmenwagen-zuhause.pdf  # Form template (add your own)
├── output/                     # Generated PDFs (gitignored)
├── .env                        # Your configuration (gitignored)
├── .env.example               # Example configuration
├── pyproject.toml             # Project metadata and dependencies
└── README.md
```

## License

MIT
