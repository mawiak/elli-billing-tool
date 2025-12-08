"""
Service layer for interacting with the Elli API.
"""

from datetime import datetime, timedelta
from typing import List

from elli_client import ElliAPIClient
from elli_client.models import Station, ChargingSession, RFIDCard


class ElliService:
    """
    Wrapper around ElliAPIClient to provide higher-level operations.
    """

    def __init__(self, username: str, password: str):
        """
        Initialize the Elli service.

        Args:
            username: Elli account username.
            password: Elli account password.
        """
        self.username = username
        self.password = password
        self.client: ElliAPIClient | None = None

    def __enter__(self) -> "ElliService":
        """
        Context manager entry - logs in to Elli API.
        """
        self.client = ElliAPIClient()
        self.client.login(self.username, self.password)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Context manager exit - closes the client connection.
        """
        if self.client:
            self.client.close()

    def get_stations(self) -> List[Station]:
        """
        Retrieve all charging stations.

        Returns:
            List of Station objects.
        """
        if not self.client:
            raise RuntimeError("Service not initialized. Use as context manager.")

        return self.client.get_stations()

    def get_charging_sessions(self) -> List[ChargingSession]:
        """
        Retrieve all charging sessions.

        Returns:
            List of ChargingSession objects.
        """
        if not self.client:
            raise RuntimeError("Service not initialized. Use as context manager.")

        return self.client.get_charging_sessions()

    def get_rfid_cards(self) -> List[RFIDCard]:
        """
        Retrieve all RFID cards.

        Returns:
            List of RFIDCard objects.
        """
        if not self.client:
            raise RuntimeError("Service not initialized. Use as context manager.")

        return self.client.get_rfid_cards()

    def get_charging_records_pdf(
        self,
        station_id: str,
        rfid_card_id: str,
        start_date: str,
        end_date: str,
        timezone: str = "Europe/Berlin"
    ) -> bytes:
        """
        Download charging records PDF for a specific period.

        Args:
            station_id: ID of the charging station.
            rfid_card_id: ID of the RFID card.
            start_date: Start date in ISO format (YYYY-MM-DD).
            end_date: End date in ISO format (YYYY-MM-DD).
            timezone: Timezone for the PDF (default: Europe/Berlin).

        Returns:
            PDF content as bytes.
        """
        if not self.client:
            raise RuntimeError("Service not initialized. Use as context manager.")

        # Convert dates to UTC timestamps
        # Start: YYYY-MM-DD 00:00:00 Berlin time -> subtract 1 hour for UTC (23:00 previous day)
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        created_at_after = (start_dt - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")

        # End: YYYY-MM-DD 23:59:59 Berlin time -> subtract 1 hour + 1 minute for UTC
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        created_at_before = (end_dt + timedelta(hours=22, minutes=59)).strftime("%Y-%m-%dT%H:%M:%SZ")

        return self.client.get_charging_records_pdf(
            station_id=station_id,
            rfid_card_id=rfid_card_id,
            created_at_after=created_at_after,
            created_at_before=created_at_before,
            pdf_timezone=timezone
        )
