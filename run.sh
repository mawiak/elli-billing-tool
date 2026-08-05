#!/bin/bash

# Elli Billing Tool Launcher for macOS/Linux
# This script intelligently decides whether to run 'list' or 'generate'

cd "$(dirname "$0")"

BINARY="./elli-billing-tool.exec"
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

case "${1:-}" in
    login|logout|status|oauth-callback)
        "$BINARY" "$@"
        exit $?
        ;;
esac

# Read settings and check for required business values
STATION_ID=$(grep -o '"ELLI_STATION_ID"[[:space:]]*:[[:space:]]*"[^"]*"' "$SETTINGS" | cut -d'"' -f4)
RFID_CARD_ID=$(grep -o '"ELLI_RFID_CARD_ID"[[:space:]]*:[[:space:]]*"[^"]*"' "$SETTINGS" | cut -d'"' -f4)

if [[ "$OSTYPE" == "darwin"* ]] && [ -d "Elli Login Callback.app" ]; then
    LSREGISTER="/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister"
    "$LSREGISTER" -f "$(pwd)/Elli Login Callback.app" || exit 1
fi

# Check if Station ID is missing (RFID Card ID is optional)
if [ -z "$STATION_ID" ]; then
    echo "⚠️  Station ID not configured."
    echo ""
    echo "Running 'list' command to show your available IDs..."
    echo ""
    "$BINARY" list
    echo ""
    echo "Please copy the Station ID into your $SETTINGS file:"
    echo "  - ELLI_STATION_ID (required)"
    echo "  - ELLI_RFID_CARD_ID (optional - leave empty to include all sessions)"
    echo ""
    read -p "Press Enter to exit..."
    exit 0
fi

# All settings look good, run generate
echo "✓ Configuration looks good, generating report..."
echo ""
if [ "$#" -eq 0 ]; then
    "$BINARY" generate
else
    "$BINARY" "$@"
fi

echo ""
read -p "Press Enter to exit..."
