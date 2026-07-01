from typing import Optional
from app.db.connection import Database
from app.utils.observability import get_logger

logger = get_logger(__name__)


class AccountRepository:
    def __init__(self, db: Database):
        self._db = db

    async def get_account(self, account_number: str) -> Optional[dict]:
        row = await self._db.fetchrow(
            """
            SELECT account_number, customer_name, status, plan,
                   balance_due, due_date, autopay_enabled
            FROM accounts
            WHERE account_number = $1
            """,
            account_number.upper(),
        )
        if row is None:
            return None
        return dict(row)

    async def get_data_usage(self, account_number: str) -> Optional[dict]:
        row = await self._db.fetchrow(
            """
            SELECT account_number, cycle_end, used_gb, plan_limit_gb,
                   priority_gb_used, priority_gb_limit,
                   hotspot_used_gb, hotspot_limit_gb
            FROM data_usage
            WHERE account_number = $1
            ORDER BY cycle_end DESC
            LIMIT 1
            """,
            account_number.upper(),
        )
        if row is None:
            return None
        return dict(row)

    async def update_balance(self, account_number: str, new_balance: float) -> bool:
        result = await self._db.execute(
            """
            UPDATE accounts
            SET balance_due = $2
            WHERE account_number = $1
            """,
            account_number.upper(),
            new_balance,
        )
        return result.endswith("1")
