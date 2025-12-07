#!/bin/bash

# Elli Billing Tool Launcher for macOS/Linux
# This script intelligently decides whether to run 'list' or 'generate'

cd "$(dirname "$0")"

BINARY="./elli-billing-tool"
SETTINGS="settings.json"

echo "=========================================="
echo "Elli Billing Tool"
echo "=========================================="
echo ""

# Remove quarantine attribute on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    xattr -d com.apple.quarantine "$BINARY" 2>/dev/null || true
fi

# Check if settings.json exists
if [ ! -f "$SETTINGS" ]; then
    echo "❌ Error: $SETTINGS not found!"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

# Read settings and check for default values
EMAIL=$(grep -o '"ELLI_EMAIL"[[:space:]]*:[[:space:]]*"[^"]*"' "$SETTINGS" | cut -d'"' -f4)
PASSWORD=$(grep -o '"ELLI_PASSWORD"[[:space:]]*:[[:space:]]*"[^"]*"' "$SETTINGS" | cut -d'"' -f4)
STATION_ID=$(grep -o '"ELLI_STATION_ID"[[:space:]]*:[[:space:]]*"[^"]*"' "$SETTINGS" | cut -d'"' -f4)
RFID_CARD_ID=$(grep -o '"ELLI_RFID_CARD_ID"[[:space:]]*:[[:space:]]*"[^"]*"' "$SETTINGS" | cut -d'"' -f4)

# Check credentials first
if [ "$EMAIL" = "your.email@example.com" ] || [ -z "$EMAIL" ] || [ "$PASSWORD" = "your_password" ] || [ -z "$PASSWORD" ]; then
    echo "⚠️  Please configure your Elli account credentials first!"
    echo ""
    echo "Edit $SETTINGS and set:"
    echo "  - ELLI_EMAIL (your Elli account email)"
    echo "  - ELLI_PASSWORD (your Elli account password)"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

# Check if Station ID or RFID Card ID are missing or default
if [ -z "$STATION_ID" ] || [ -z "$RFID_CARD_ID" ]; then
    echo "⚠️  Station ID or RFID Card ID not configured."
    echo ""
    echo "Running 'list' command to show your available IDs..."
    echo ""
    "$BINARY" list
    echo ""
    echo "Please copy the IDs above into your $SETTINGS file:"
    echo "  - ELLI_STATION_ID"
    echo "  - ELLI_RFID_CARD_ID"
    echo ""
    read -p "Press Enter to exit..."
    exit 0
fi

# All settings look good, run generate
echo "✓ Configuration looks good, generating report..."
echo ""
"$BINARY" generate "$@"

echo ""
read -p "Press Enter to exit..."
