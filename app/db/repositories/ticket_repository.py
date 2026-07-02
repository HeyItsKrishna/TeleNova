from app.db.connection import Database


class TicketRepository:

    def __init__(self, db: Database):
        self._db = db

    async def get_by_customer_id(self, customer_id):

        return await self._db.fetch(
            """
            SELECT *
            FROM support_tickets
            WHERE customer_id = $1
            ORDER BY created_at DESC
            """,
            customer_id,
        )

    async def get_open_tickets(self, customer_id):

        return await self._db.fetch(
            """
            SELECT *
            FROM support_tickets
            WHERE customer_id = $1
              AND status IN ('OPEN','IN_PROGRESS')
            ORDER BY created_at DESC
            """,
            customer_id,
        )

    async def get_by_ticket_number(
        self,
        ticket_number: str,
    ):

        row = await self._db.fetchrow(
            """
            SELECT
                t.*,
                c.account_number,
                c.first_name,
                c.last_name
            FROM support_tickets t
            JOIN customers c
                ON c.id = t.customer_id
            WHERE t.ticket_number = $1
            """,
            ticket_number,
        )

        return dict(row) if row else None

    async def get_by_account_number(
        self,
        account_number: str,
    ):

        rows = await self._db.fetch(
            """
            SELECT
                t.*
            FROM support_tickets t
            JOIN customers c
                ON c.id = t.customer_id
            WHERE c.account_number = $1
            ORDER BY t.created_at DESC
            """,
            account_number.upper(),
        )

        return [dict(r) for r in rows]

    async def create_ticket(
        self,
        ticket_number,
        customer_id,
        category,
        priority,
        summary,
    ):

        await self._db.execute(
            """
            INSERT INTO support_tickets(
                ticket_number,
                customer_id,
                category,
                priority,
                status,
                summary
            )
            VALUES(
                $1,$2,$3,$4,'OPEN',$5
            )
            """,
            ticket_number,
            customer_id,
            category,
            priority,
            summary,
        )

    async def update_status(
        self,
        ticket_number,
        status,
    ):

        await self._db.execute(
            """
            UPDATE support_tickets
            SET
                status=$2,
                updated_at=NOW()
            WHERE ticket_number=$1
            """,
            ticket_number,
            status,
        )

    async def resolve_ticket(
        self,
        ticket_number,
        resolution,
    ):

        await self._db.execute(
            """
            UPDATE support_tickets
            SET
                status='RESOLVED',
                resolution=$2,
                updated_at=NOW()
            WHERE ticket_number=$1
            """,
            ticket_number,
            resolution,
        )