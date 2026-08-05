"""
Configuration management for the Elli Billing Tool.
"""

import json
import os
from dataclasses import dataclass
from pathlib import Path


class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass


@dataclass
class Config:
    """
    Application configuration loaded from settings.json.
    """

    station_id: str
    rfid_card_id: str | None  # Optional: None = all sessions (RFID + App)
    kwh_price_cents: float
    location: str
    current_month: bool  # True = current month, False = last completed month

    # Email configuration
    email_subject: str
    email_recipients: list[str]
    email_cc: list[str]
    email_name: str

    @classmethod
    def load_from_file(cls, settings_file: Path = None, require_all: bool = True) -> "Config":
        """
        Load configuration from settings.json file.

        Args:
            settings_file: Optional path to settings.json file. Defaults to settings.json in current directory.

        Returns:
            Config instance with loaded values.

        Raises:
            ConfigError: If settings file is missing or has invalid values.
        """
        if settings_file is None:
            settings_file = Path("settings.json")

        if not settings_file.exists():
            raise ConfigError(
                f"Settings file not found: {settings_file}\n"
                "Please copy settings.json.example to settings.json and fill in your details."
            )

        try:
            with open(settings_file, "r", encoding="utf-8") as f:
                settings = json.load(f)
        except json.JSONDecodeError as e:
            raise ConfigError(f"Invalid JSON in settings file: {e}")

        # Remove obsolete password-login fields when the file can safely be replaced.
        obsolete = {"ELLI_EMAIL", "ELLI_PASSWORD"}.intersection(settings)
        if obsolete:
            migrated = {k: v for k, v in settings.items() if k not in obsolete}
            try:
                temporary = settings_file.with_name(f".{settings_file.name}.{os.getpid()}.tmp")
                temporary.write_text(json.dumps(migrated, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                os.replace(temporary, settings_file)
                settings = migrated
                print("Hinweis: Veraltete Elli-E-Mail-/Passwortfelder wurden aus settings.json entfernt.")
            except OSError:
                temporary.unlink(missing_ok=True)
                print("Hinweis: Veraltete Elli-E-Mail-/Passwortfelder werden ignoriert.")

        # Filter out documentation-only fields after migration so they are preserved on disk.
        settings = {k: v for k, v in settings.items() if not k.startswith("_")}

        station_id = settings.get("ELLI_STATION_ID")
        rfid_card_id = settings.get("ELLI_RFID_CARD_ID") or None  # Empty string -> None
        kwh_price_cents = settings.get("ELLI_KWH_PRICE_CENTS")
        location = settings.get("ELLI_LOCATION")
        current_month = settings.get("ELLI_CURRENT_MONTH", False)

        # Email configuration
        email_subject = settings.get("EMAIL_SUBJECT")
        email_recipients_str = settings.get("EMAIL_RECIPIENTS", "")
        email_recipients = [r.strip() for r in email_recipients_str.split(",") if r.strip()]
        email_cc_str = settings.get("EMAIL_CC", "")
        email_cc = [c.strip() for c in email_cc_str.split(",") if c.strip()]
        email_name = settings.get("EMAIL_NAME")

        # Check for missing required fields
        missing = []

        # Only check other fields if require_all is True
        if require_all:
            if not station_id:
                missing.append("ELLI_STATION_ID (run 'list' command to find it)")
            # RFID_CARD_ID is now optional - if empty/None, all sessions (RFID + App) will be included
            if not kwh_price_cents:
                missing.append("ELLI_KWH_PRICE_CENTS")
            if not location:
                missing.append("ELLI_LOCATION")
            if not email_subject:
                missing.append("EMAIL_SUBJECT")
            if not email_recipients:
                missing.append("EMAIL_RECIPIENTS")
            if not email_name or email_name == "Your Name":
                missing.append("EMAIL_NAME")

        if missing:
            raise ConfigError(
                f"Missing or invalid configuration in settings.json:\n  - " + "\n  - ".join(missing)
            )

        # Validate kwh_price only if require_all
        kwh_price = 0.0
        if require_all:
            try:
                kwh_price = float(kwh_price_cents)
            except (ValueError, TypeError) as e:
                raise ConfigError(
                    f"ELLI_KWH_PRICE_CENTS must be a valid number, got: {kwh_price_cents}"
                ) from e

        return cls(
            station_id=station_id or "",
            rfid_card_id=rfid_card_id,  # Can be None
            kwh_price_cents=kwh_price,
            location=location or "",
            current_month=current_month,
            email_subject=email_subject or "",
            email_recipients=email_recipients,
            email_cc=email_cc,
            email_name=email_name or ""
        )
