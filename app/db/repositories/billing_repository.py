from typing import Optional
from app.db.connection import Database
from app.utils.observability import get_logger

logger = get_logger(__name__)


class BillingRepository:
    def __init__(self, db: Database):
        self._db = db

    async def get_billing_cycle(self, account_number: str, cycle_label: str = "current") -> Optional[dict]:
        cycle_row = await self._db.fetchrow(
            """
            SELECT id, account_number, cycle_label, plan_charge, taxes_and_fees,
                   add_ons, overages, credits, total, created_at
            FROM billing_cycles
            WHERE account_number = $1 AND cycle_label = $2
            """,
            account_number.upper(),
            cycle_label,
        )
        if cycle_row is None:
            return None

        line_items = await self._db.fetch(
            """
            SELECT description, amount
            FROM billing_line_items
            WHERE billing_cycle_id = $1
            ORDER BY line_order
            """,
            cycle_row["id"],
        )

        result = dict(cycle_row)
        result["line_items"] = [dict(item) for item in line_items]
        return result

    async def get_payment_history(self, account_number: str, limit: int = 3) -> list[dict]:
        rows = await self._db.fetch(
            """
            SELECT payment_date, amount, method, status
            FROM payments
            WHERE account_number = $1
            ORDER BY payment_date DESC
            LIMIT $2
            """,
            account_number.upper(),
            limit,
        )
        return [dict(row) for row in rows]

    async def apply_credit(self, account_number: str, credit_amount: float, reason: str) -> dict:
        async with self._db.acquire() as conn:
            async with conn.transaction():
                current = await conn.fetchval(
                    "SELECT balance_due FROM accounts WHERE account_number = $1 FOR UPDATE",
                    account_number.upper(),
                )
                if current is None:
                    return {"success": False, "message": "Account not found."}

                new_balance = max(float(current) - credit_amount, 0)
                await conn.execute(
                    "UPDATE accounts SET balance_due = $2 WHERE account_number = $1",
                    account_number.upper(),
                    new_balance,
                )
                logger.info(
                    "billing_credit_applied",
                    account_number=account_number.upper(),
                    credit_amount=credit_amount,
                    reason=reason,
                    new_balance=new_balance,
                )
                return {
                    "success": True,
                    "account_number": account_number.upper(),
                    "credit_amount": credit_amount,
                    "new_balance": new_balance,
                }
