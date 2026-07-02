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
            SELECT
                c.id,
                c.account_number,
                c.first_name,
                c.last_name,
                c.email,
                c.phone_number,
                c.account_status,

                p.plan_code,
                p.plan_name,
                p.monthly_price,
                p.data_limit_gb,
                p.voice_minutes,
                p.sms_limit,
                p.features,

                b.current_balance,
                b.autopay_enabled,
                b.preferred_payment_method

            FROM customers c

            LEFT JOIN plans p
                ON c.plan_id = p.id

            LEFT JOIN billing_accounts b
                ON b.customer_id = c.id

            WHERE c.account_number = $1
            """,
            account_number.upper(),
        )

        if row is None:
            return None

        return dict(row)

    async def get_customer(self, account_number: str) -> Optional[dict]:

        row = await self._db.fetchrow(
            """
            SELECT *
            FROM customers
            WHERE account_number = $1
            """,
            account_number.upper(),
        )

        return dict(row) if row else None

    async def get_plan(self, account_number: str) -> Optional[dict]:

        row = await self._db.fetchrow(
            """
            SELECT
                p.*
            FROM customers c
            JOIN plans p
                ON c.plan_id = p.id
            WHERE c.account_number = $1
            """,
            account_number.upper(),
        )

        return dict(row) if row else None

    async def update_balance(
        self,
        account_number: str,
        new_balance: float,
    ) -> bool:

        result = await self._db.execute(
            """
            UPDATE billing_accounts
            SET current_balance = $2
            WHERE customer_id = (
                SELECT id
                FROM customers
                WHERE account_number = $1
            )
            """,
            account_number.upper(),
            new_balance,
        )

        return result.endswith("1")