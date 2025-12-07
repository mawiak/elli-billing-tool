"""
Configuration management for the Elli Billing Tool.
"""

import json
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

    username: str
    password: str
    station_id: str
    rfid_card_id: str
    kwh_price_cents: float
    location: str

    # Email configuration
    email_subject: str
    email_recipients: list[str]
    email_cc: list[str]
    email_name: str

    @classmethod
    def load_from_file(cls, settings_file: Path = None) -> "Config":
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

        # Filter out comment fields
        settings = {k: v for k, v in settings.items() if not k.startswith("_")}

        username = settings.get("ELLI_EMAIL")
        password = settings.get("ELLI_PASSWORD")
        station_id = settings.get("ELLI_STATION_ID")
        rfid_card_id = settings.get("ELLI_RFID_CARD_ID")
        kwh_price_cents = settings.get("ELLI_KWH_PRICE_CENTS")
        location = settings.get("ELLI_LOCATION")

        # Email configuration
        email_subject = settings.get("EMAIL_SUBJECT")
        email_recipients_str = settings.get("EMAIL_RECIPIENTS", "")
        email_recipients = [r.strip() for r in email_recipients_str.split(",") if r.strip()]
        email_cc_str = settings.get("EMAIL_CC", "")
        email_cc = [c.strip() for c in email_cc_str.split(",") if c.strip()]
        email_name = settings.get("EMAIL_NAME")

        # Check for missing required fields
        missing = []
        if not username or username == "your.email@example.com":
            missing.append("ELLI_EMAIL")
        if not password or password == "your_password":
            missing.append("ELLI_PASSWORD")
        if not station_id:
            missing.append("ELLI_STATION_ID (run 'list' command to find it)")
        if not rfid_card_id:
            missing.append("ELLI_RFID_CARD_ID (run 'list' command to find it)")
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

        try:
            kwh_price = float(kwh_price_cents)
        except (ValueError, TypeError) as e:
            raise ConfigError(
                f"ELLI_KWH_PRICE_CENTS must be a valid number, got: {kwh_price_cents}"
            ) from e

        return cls(
            username=username,
            password=password,
            station_id=station_id,
            rfid_card_id=rfid_card_id,
            kwh_price_cents=kwh_price,
            location=location,
            email_subject=email_subject,
            email_recipients=email_recipients,
            email_cc=email_cc,
            email_name=email_name
        )
