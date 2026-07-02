from typing import Optional

from app.db.connection import Database
from app.utils.observability import get_logger

logger = get_logger(__name__)


class NetworkRepository:

    def __init__(self, db: Database):
        self._db = db

    async def get_device(self, account_number: str) -> Optional[dict]:

        row = await self._db.fetchrow(
            """
            SELECT
                c.account_number,
                d.device_name,
                d.network_type,
                d.esim,
                d.imei,
                d.registered_at
            FROM customers c
            JOIN devices d
                ON d.customer_id = c.id
            WHERE c.account_number = $1
            LIMIT 1
            """,
            account_number.upper(),
        )

        return dict(row) if row else None

    async def get_latest_diagnostic(
        self,
        account_number: str,
    ) -> Optional[dict]:

        device = await self.get_device(account_number)

        if device is None:
            return None

        #
        # Temporary diagnostic generated from device data.
        #
        return {
            "account_number": device["account_number"],
            "sim_status": "ACTIVE",
            "network_registration": "REGISTERED",
            "signal_strength": "-82 dBm",
            "technology": device["network_type"],
            "last_data_session": device["registered_at"],
            "volte_enabled": True,
            "issues_detected": [],
        }

    async def get_outage_by_zip(
        self,
        zip_code: str,
    ) -> Optional[dict]:
        #
        # Temporary stub.
        # Replace later with a real outages table/service.
        #
        return None

    async def record_diagnostic(
        self,
        account_number: str,
        diagnostic: dict,
    ) -> str:
        #
        # No diagnostics table yet.
        # Stub to preserve the interface.
        #
        return "diagnostic-recorded"