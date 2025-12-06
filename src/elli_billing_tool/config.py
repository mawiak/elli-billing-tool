"""
Configuration management for the Elli Billing Tool.
"""

import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv


@dataclass
class Config:
    """
    Application configuration loaded from environment variables.
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
    def load_from_env(cls, env_file: Optional[str] = None) -> "Config":
        """
        Load configuration from .env file or environment variables.

        Args:
            env_file: Optional path to .env file. Defaults to .env in current directory.

        Returns:
            Config instance with loaded values.

        Raises:
            ValueError: If required environment variables are missing.
        """
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()

        username = os.getenv("ELLI_EMAIL")
        password = os.getenv("ELLI_PASSWORD")
        station_id = os.getenv("ELLI_STATION_ID")
        rfid_card_id = os.getenv("ELLI_RFID_CARD_ID")
        kwh_price_cents = os.getenv("ELLI_KWH_PRICE_CENTS")
        location = os.getenv("ELLI_LOCATION")

        # Email configuration
        email_subject = os.getenv("EMAIL_SUBJECT")
        email_recipients = os.getenv("EMAIL_RECIPIENTS", "").split(",")
        email_cc = os.getenv("EMAIL_CC", "").split(",") if os.getenv("EMAIL_CC") else []
        email_name = os.getenv("EMAIL_NAME")

        if not all([username, password, station_id, rfid_card_id, kwh_price_cents, location, email_subject, email_recipients, email_name]):
            missing = []
            if not username:
                missing.append("ELLI_EMAIL")
            if not password:
                missing.append("ELLI_PASSWORD")
            if not station_id:
                missing.append("ELLI_STATION_ID")
            if not rfid_card_id:
                missing.append("ELLI_RFID_CARD_ID")
            if not kwh_price_cents:
                missing.append("ELLI_KWH_PRICE_CENTS")
            if not location:
                missing.append("ELLI_LOCATION")
            if not email_subject:
                missing.append("EMAIL_SUBJECT")
            if not email_recipients or not email_recipients[0]:
                missing.append("EMAIL_RECIPIENTS")
            if not email_name:
                missing.append("EMAIL_NAME")

            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}"
            )

        try:
            kwh_price = float(kwh_price_cents)
        except ValueError as e:
            raise ValueError(
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
