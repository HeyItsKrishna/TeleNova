from typing import Optional
import random
from app.db.connection import Database
from app.utils.observability import get_logger

logger = get_logger(__name__)

CATEGORY_PREFIX_MAP = {
    "billing": "BIL",
    "network": "NET",
    "account": "ACC",
    "device": "DEV",
    "general": "GEN",
}

CATEGORY_ETA_MAP = {
    "billing": "3–5 business days",
    "network": "24–72 hours",
    "account": "1 business day",
    "device": "1–3 business days",
    "general": "24 hours",
}


class TicketRepository:
    def __init__(self, db: Database):
        self._db = db

    async def get_ticket(self, ticket_id: str) -> Optional[dict]:
        row = await self._db.fetchrow(
            """
            SELECT ticket_id, account_number, category, status, description,
                   assigned_team, resolution_notes, created_at, updated_at
            FROM tickets
            WHERE ticket_id = $1
            """,
            ticket_id.upper(),
        )
        if row is None:
            return None
        result = dict(row)
        result["estimated_resolution"] = CATEGORY_ETA_MAP.get(result["category"], "24 hours")
        return result

    async def list_tickets_for_account(self, account_number: str) -> list[dict]:
        rows = await self._db.fetch(
            """
            SELECT ticket_id, category, status, description, created_at, updated_at
            FROM tickets
            WHERE account_number = $1
            ORDER BY created_at DESC
            """,
            account_number.upper(),
        )
        return [dict(row) for row in rows]

    async def create_ticket(self, account_number: str, category: str, description: str) -> dict:
        category_normalized = category.lower()
        prefix = CATEGORY_PREFIX_MAP.get(category_normalized, "GEN")
        ticket_id = f"{prefix}-{random.randint(10000, 99999)}"
        team_map = {
            "billing": "Billing Specialist",
            "network": "Network Ops",
            "account": "Account Specialist",
            "device": "Device Support",
            "general": "Support Queue",
        }

        await self._db.execute(
            """
            INSERT INTO tickets (ticket_id, account_number, category, status, description, assigned_team)
            VALUES ($1, $2, $3, 'open', $4, $5)
            """,
            ticket_id,
            account_number.upper(),
            category_normalized,
            description,
            team_map.get(category_normalized, "Support Queue"),
        )
        logger.info("ticket_created", ticket_id=ticket_id, account_number=account_number.upper())
        return {
            "ticket_id": ticket_id,
            "account_number": account_number.upper(),
            "category": category_normalized,
            "status": "open",
            "estimated_resolution": CATEGORY_ETA_MAP.get(category_normalized, "24 hours"),
        }
