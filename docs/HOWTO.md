# How to Use Elli Billing Tool

This guide will walk you through the complete setup and usage of the Elli Billing Tool.

## Step 1: Extract the ZIP File

1. Download the appropriate ZIP file for your operating system:
   - `macOS_elli_billing_tool.zip` for macOS
   - `windows_elli_billing_tool.zip` for Windows

2. Extract the ZIP file to a location of your choice (e.g., `Documents/elli-billing-tool`)

3. The extracted folder contains:
   - `elli-billing-tool` (macOS) or `elli-billing-tool.exe` (Windows) - the main executable
   - `run.sh` (macOS) or `run.bat` (Windows) - the launcher script
   - `settings.json` - configuration file with example values
   - `template/` - folder for your PDF template and email template
   - `output/` - folder where generated reports will be saved

## Step 2: Configure Your Credentials

1. Open `settings.json` in a text editor (Notepad, TextEdit, VS Code, etc.)

2. Replace the example values with your actual Elli account credentials:

```json
{
  "ELLI_EMAIL": "your.actual.email@example.com",
  "ELLI_PASSWORD": "your_actual_password",
```

3. Save the file

**Note:** Do not modify the `_comment` fields - they are ignored by the tool and exist only for documentation.

## Step 3: Find Your Station and RFID Card IDs

1. Run the launcher script to retrieve your IDs:
   - **macOS:** Double-click `run.sh` or run `./run.sh` in Terminal
   - **Windows:** Double-click `run.bat`

2. The script will detect that Station ID and RFID Card ID are missing and automatically run the `list` command

3. The output will show your available charging stations and RFID cards:

```
=== Charging Stations ===

Station ID: ff584b2f-29bd-4df7-b761-a38963961884
  Name: Home Charger
  Serial: ABC123

=== RFID Cards (from Charging Sessions) ===

RFID Card ID: 652bd33e-821c-4595-ab7a-849176fc7bd8
  Serial: XYZ789
```

4. Copy the Station ID and RFID Card ID values

## Step 4: Update Settings with IDs

1. Open `settings.json` again

2. Paste the IDs you copied:

```json
  "ELLI_STATION_ID": "ff584b2f-29bd-4df7-b761-a38963961884",
  "ELLI_RFID_CARD_ID": "652bd33e-821c-4595-ab7a-849176fc7bd8",
```

3. Review and update other settings as needed:
   - `ELLI_KWH_PRICE_CENTS`: Your electricity price in cents per kWh (e.g., "33.33" for 0.3333 EUR/kWh)
   - `ELLI_LOCATION`: Location for the form signature (e.g., "Berlin")
   - `EMAIL_SUBJECT`: Email subject line (supports placeholders: {MONTH}, {YEAR}, {NAME})
   - `EMAIL_RECIPIENTS`: Comma-separated list of recipient emails
   - `EMAIL_CC`: Comma-separated list of CC emails (optional)
   - `EMAIL_NAME`: Your name for the email signature

4. Save the file

## Step 5: Add Your PDF Template

1. Obtain your reimbursement form PDF template

2. Rename it to: `Template_Abrechnungsformular-Energiekosten-Firmenwagen-zuhause.pdf`

3. Copy the file into the `template/` folder

**Important:** The filename must match exactly as shown above.

## Step 6: Generate Your First Report

1. Run the launcher script:
   - **macOS:** Double-click `run.sh` or run `./run.sh` in Terminal
   - **Windows:** Double-click `run.bat`

2. The tool will:
   - Download charging records for the previous month from Elli
   - Extract total kWh consumption
   - Calculate reimbursement amount
   - Fill your PDF template with the data
   - Save both PDFs to `output/YYYY/MM/`
   - Open your email client with pre-filled email
   - Open the output folder for easy drag-and-drop of attachments

3. Check the `output/` folder for your generated files:
   - `Abrechnungsformular-Energiekosten-Firmenwagen-zuhause.pdf` - filled reimbursement form
   - `charging_records_YYYY-MM-DD_to_YYYY-MM-DD.pdf` - original charging records from Elli

## Step 7: Send Your Report

1. Your default email client will open with a pre-filled email containing:
   - Recipients and CC addresses from your settings
   - Subject line with the month and year
   - Email body from the template

2. A file browser window will open showing the output folder

3. Drag and drop the two PDF files from the folder into your email as attachments

4. Review and send the email

## Troubleshooting

### macOS: "Apple could not verify..."

If you see a security warning on macOS:

1. Right-click on `run.sh` and select "Open"
2. Click "Open" in the security dialog
3. Or go to System Preferences > Privacy & Security and click "Open Anyway"

The `run.sh` script will automatically remove the quarantine flag from the executable.

## Support

For issues or questions, please visit: https://github.com/marcszy91/elli-billing-tool/issues
