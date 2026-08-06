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
    xattr -dr com.apple.quarantine "Elli Login Callback.app" 2>/dev/null || true
fi

# Check if settings.json exists
if [ ! -f "$SETTINGS" ]; then
    echo "❌ Error: $SETTINGS not found!"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

if [[ "$OSTYPE" == "darwin"* ]] && [ -d "Elli Login Callback.app" ]; then
    LSREGISTER="/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister"
    CALLBACK_HELPER="$(pwd)/Elli Login Callback.app"
    CALLBACK_REGISTRATIONS=$(mktemp "${TMPDIR:-/tmp}/elli-callback-registrations.XXXXXX")
    trap 'rm -f "$CALLBACK_REGISTRATIONS"' EXIT HUP INT TERM

    "$LSREGISTER" -dump | awk '
        /^-{20,}$/ { path = "" }
        /^path:[[:space:]]/ {
            path = $0
            sub(/^path:[[:space:]]*/, "", path)
            sub(/[[:space:]]+\(0x[0-9a-fA-F]+\)$/, "", path)
        }
        /claimed schemes:[[:space:]]+com\.elli\.ios\.emsp:/ {
            if (path != "") print path
        }
    ' > "$CALLBACK_REGISTRATIONS"

    while IFS= read -r registered_helper; do
        if [ -n "$registered_helper" ] && [ "$registered_helper" != "$CALLBACK_HELPER" ]; then
            echo "Entferne konkurrierende Elli-Callback-Registrierung: $registered_helper"
            "$LSREGISTER" -u "$registered_helper" 2>/dev/null || true
        fi
    done < "$CALLBACK_REGISTRATIONS"

    "$LSREGISTER" -f "$CALLBACK_HELPER" || {
        echo "Der Elli-Callback-Helper konnte nicht registriert werden." >&2
        exit 1
    }
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
