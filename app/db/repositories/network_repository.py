from typing import Optional
from app.db.connection import Database
from app.utils.observability import get_logger

logger = get_logger(__name__)


class NetworkRepository:
    def __init__(self, db: Database):
        self._db = db

    async def get_outage_by_zip(self, zip_code: str) -> Optional[dict]:
        row = await self._db.fetchrow(
            """
            SELECT zip_code, incident_id, status, network_type,
                   started_at, estimated_resolution, affected_services
            FROM network_outages
            WHERE zip_code = $1
            ORDER BY started_at DESC
            LIMIT 1
            """,
            zip_code,
        )
        if row is None:
            return None
        return dict(row)

    async def get_latest_diagnostic(self, account_number: str) -> Optional[dict]:
        row = await self._db.fetchrow(
            """
            SELECT account_number, sim_status, network_registration,
                   signal_strength, technology, last_data_session,
                   volte_enabled, issues_detected, recorded_at
            FROM network_diagnostics
            WHERE account_number = $1
            ORDER BY recorded_at DESC
            LIMIT 1
            """,
            account_number.upper(),
        )
        if row is None:
            return None
        return dict(row)

    async def record_diagnostic(self, account_number: str, diagnostic: dict) -> str:
        row = await self._db.fetchrow(
            """
            INSERT INTO network_diagnostics
                (account_number, sim_status, network_registration, signal_strength,
                 technology, volte_enabled, issues_detected)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id
            """,
            account_number.upper(),
            diagnostic["sim_status"],
            diagnostic["network_registration"],
            diagnostic.get("signal_strength"),
            diagnostic.get("technology"),
            diagnostic.get("volte_enabled", False),
            diagnostic.get("issues_detected", []),
        )
        return str(row["id"])
