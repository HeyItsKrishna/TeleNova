from app.db.connection import Database


class BillingRepository:

    def __init__(self, db: Database):
        self._db = db

    async def get_by_customer_id(self, customer_id):

        return await self._db.fetchrow(
            """
            SELECT
                b.*,
                c.account_number,
                c.first_name,
                c.last_name
            FROM billing_accounts b
            JOIN customers c
                ON b.customer_id = c.id
            WHERE b.customer_id = $1
            """,
            customer_id,
        )

    async def get_by_account_number(self, account_number: str):

        return await self._db.fetchrow(
            """
            SELECT
                b.*,
                c.account_number,
                c.first_name,
                c.last_name
            FROM billing_accounts b
            JOIN customers c
                ON b.customer_id = c.id
            WHERE c.account_number = $1
            """,
            account_number.upper(),
        )

    # ------------------------------------------------------------------
    # Billing Agent API
    # ------------------------------------------------------------------

    async def get_billing_cycle(
        self,
        account_number: str,
        billing_cycle: str = "current",
    ):

        row = await self._db.fetchrow(
            """
            SELECT
                c.account_number,
                p.monthly_price,
                b.current_balance,
                b.autopay_enabled
            FROM customers c
            JOIN billing_accounts b
                ON b.customer_id = c.id
            LEFT JOIN plans p
                ON p.id = c.plan_id
            WHERE c.account_number = $1
            """,
            account_number.upper(),
        )

        if row is None:
            return None

        plan_charge = float(row["monthly_price"] or 0)
        taxes = round(plan_charge * 0.18, 2)
        total = float(row["current_balance"])

        return {
            "account_number": row["account_number"],
            "cycle_label": billing_cycle.title(),
            "plan_charge": plan_charge,
            "taxes_and_fees": taxes,
            "add_ons": 0.0,
            "overages": 0.0,
            "credits": 0.0,
            "total": total,
            "line_items": [
                {
                    "description": "Monthly Plan",
                    "amount": plan_charge,
                },
                {
                    "description": "Taxes",
                    "amount": taxes,
                },
            ],
        }

    async def apply_credit(
        self,
        account_number: str,
        credit_amount: float,
        reason: str,
    ):

        row = await self._db.fetchrow(
            """
            UPDATE billing_accounts
            SET current_balance = GREATEST(
                current_balance - $2,
                0
            )
            WHERE customer_id = (
                SELECT id
                FROM customers
                WHERE account_number = $1
            )
            RETURNING current_balance
            """,
            account_number.upper(),
            credit_amount,
        )

        if row is None:
            return {
                "success": False,
                "message": "Account not found.",
            }

        return {
            "success": True,
            "account_number": account_number.upper(),
            "credit_amount": credit_amount,
            "new_balance": float(row["current_balance"]),
        }

    async def get_payment_history(
        self,
        account_number: str,
        limit: int = 3,
    ):
        #
        # Temporary implementation
        #
        # Replace with a payment_history table later.
        #

        row = await self.get_by_account_number(account_number)

        if row is None:
            return []

        return [
            {
                "payment_date": row["created_at"],
                "amount": row["current_balance"],
                "method": row["preferred_payment_method"],
                "status": "Completed",
            }
        ]