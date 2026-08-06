#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
OUTPUT_DIR=${1:-"$SCRIPT_DIR/../../dist/package"}
APP_DIR="$OUTPUT_DIR/Elli Login Callback.app"
CACHE_DIR=$(mktemp -d "${TMPDIR:-/tmp}/elli-billing-helper.XXXXXX")
trap 'rm -r "$CACHE_DIR"' EXIT HUP INT TERM

mkdir -p "$APP_DIR/Contents/MacOS"
cp "$SCRIPT_DIR/Info.plist" "$APP_DIR/Contents/Info.plist"
swiftc "$SCRIPT_DIR/ElliLoginCallback.swift" -o "$APP_DIR/Contents/MacOS/ElliLoginCallback" -framework AppKit -module-cache-path "$CACHE_DIR"

# swiftc signs the Mach-O executable on modern macOS runners, but that alone can
# leave the surrounding .app bundle in an invalid state (missing CodeResources).
# Seal the complete helper bundle reproducibly for unsigned/test distributions.
# This ad-hoc signature is intentionally not a replacement for Developer ID.
codesign --force --deep --sign - "$APP_DIR"
