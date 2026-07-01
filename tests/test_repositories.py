import pytest
import asyncpg
from app.config import get_settings
from app.db.connection import Database
from app.db.repositories.account_repository import AccountRepository
from app.db.repositories.billing_repository import BillingRepository
from app.db.repositories.network_repository import NetworkRepository
from app.db.repositories.ticket_repository import TicketRepository

settings = get_settings()

pytestmark = pytest.mark.skipif(
    "localhost" not in settings.database_url and "127.0.0.1" not in settings.database_url,
    reason="Integration tests only run against local Postgres",
)


@pytest.fixture
async def db():
    database = Database()
    try:
        await database.connect()
    except Exception:
        pytest.skip("Local Postgres not reachable — run: docker compose up -d postgres")
    yield database
    await database.disconnect()


class TestAccountRepository:

    @pytest.mark.asyncio
    async def test_get_existing_account(self, db):
        repo = AccountRepository(db)
        account = await repo.get_account("TN-100001")
        assert account is not None
        assert account["account_number"] == "TN-100001"
        assert account["plan"] == "unlimited_pro"

    @pytest.mark.asyncio
    async def test_get_nonexistent_account(self, db):
        repo = AccountRepository(db)
        account = await repo.get_account("TN-999999")
        assert account is None

    @pytest.mark.asyncio
    async def test_case_insensitive_lookup(self, db):
        repo = AccountRepository(db)
        account = await repo.get_account("tn-100001")
        assert account is not None

    @pytest.mark.asyncio
    async def test_suspended_account_status(self, db):
        repo = AccountRepository(db)
        account = await repo.get_account("TN-100002")
        assert account is not None
        assert account["status"] == "suspended_nonpayment"
        assert float(account["balance_due"]) == 135.50

    @pytest.mark.asyncio
    async def test_get_data_usage_unlimited_plan(self, db):
        repo = AccountRepository(db)
        usage = await repo.get_data_usage("TN-100001")
        assert usage is not None
        assert usage["plan_limit_gb"] is None

    @pytest.mark.asyncio
    async def test_get_data_usage_capped_plan(self, db):
        repo = AccountRepository(db)
        usage = await repo.get_data_usage("TN-100002")
        assert usage is not None
        assert float(usage["plan_limit_gb"]) == 25.0
        assert float(usage["used_gb"]) == 22.80

    @pytest.mark.asyncio
    async def test_get_data_usage_nonexistent(self, db):
        repo = AccountRepository(db)
        usage = await repo.get_data_usage("TN-999999")
        assert usage is None


class TestBillingRepository:

    @pytest.mark.asyncio
    async def test_get_billing_cycle_with_line_items(self, db):
        repo = BillingRepository(db)
        cycle = await repo.get_billing_cycle("TN-100001", "current")
        assert cycle is not None
        assert len(cycle["line_items"]) == 5
        assert float(cycle["total"]) == 81.75

    @pytest.mark.asyncio
    async def test_billing_cycle_line_item_values(self, db):
        repo = BillingRepository(db)
        cycle = await repo.get_billing_cycle("TN-100001", "current")
        descriptions = [item["description"] for item in cycle["line_items"]]
        assert "Unlimited Pro Plan" in descriptions
        assert "AutoPay Discount" in descriptions

    @pytest.mark.asyncio
    async def test_get_billing_cycle_nonexistent(self, db):
        repo = BillingRepository(db)
        cycle = await repo.get_billing_cycle("TN-100001", "nonexistent")
        assert cycle is None

    @pytest.mark.asyncio
    async def test_get_payment_history_limit(self, db):
        repo = BillingRepository(db)
        payments = await repo.get_payment_history("TN-100001", limit=2)
        assert len(payments) == 2

    @pytest.mark.asyncio
    async def test_payment_history_most_recent_first(self, db):
        repo = BillingRepository(db)
        payments = await repo.get_payment_history("TN-100001", limit=3)
        dates = [p["payment_date"] for p in payments]
        assert dates == sorted(dates, reverse=True)

    @pytest.mark.asyncio
    async def test_missed_payment_in_history(self, db):
        repo = BillingRepository(db)
        payments = await repo.get_payment_history("TN-100002", limit=3)
        statuses = [p["status"] for p in payments]
        assert "Missed" in statuses

    @pytest.mark.asyncio
    async def test_apply_credit_reduces_balance(self, db):
        repo = BillingRepository(db)
        before = await db.fetchval(
            "SELECT balance_due FROM accounts WHERE account_number = $1", "TN-100003"
        )
        result = await repo.apply_credit("TN-100003", 10.00, "Test credit")
        assert result["success"] is True
        assert result["new_balance"] == max(float(before) - 10.00, 0)
        await db.execute(
            "UPDATE accounts SET balance_due = $1 WHERE account_number = $2",
            before, "TN-100003",
        )

    @pytest.mark.asyncio
    async def test_apply_credit_nonexistent_account(self, db):
        repo = BillingRepository(db)
        result = await repo.apply_credit("TN-999999", 10.00, "Test")
        assert result["success"] is False


class TestNetworkRepository:

    @pytest.mark.asyncio
    async def test_get_active_outage(self, db):
        repo = NetworkRepository(db)
        outage = await repo.get_outage_by_zip("90210")
        assert outage is not None
        assert outage["status"] == "Outage Active"
        assert "Data" in outage["affected_services"]

    @pytest.mark.asyncio
    async def test_degraded_performance_outage(self, db):
        repo = NetworkRepository(db)
        outage = await repo.get_outage_by_zip("94102")
        assert outage is not None
        assert outage["status"] == "Degraded Performance"

    @pytest.mark.asyncio
    async def test_get_outage_clear_area(self, db):
        repo = NetworkRepository(db)
        outage = await repo.get_outage_by_zip("00000")
        assert outage is None

    @pytest.mark.asyncio
    async def test_get_latest_diagnostic_with_issues(self, db):
        repo = NetworkRepository(db)
        diagnostic = await repo.get_latest_diagnostic("TN-100002")
        assert diagnostic is not None
        assert diagnostic["volte_enabled"] is False
        assert len(diagnostic["issues_detected"]) == 2

    @pytest.mark.asyncio
    async def test_get_latest_diagnostic_no_issues(self, db):
        repo = NetworkRepository(db)
        diagnostic = await repo.get_latest_diagnostic("TN-100001")
        assert diagnostic is not None
        assert diagnostic["volte_enabled"] is True
        assert diagnostic["issues_detected"] == []

    @pytest.mark.asyncio
    async def test_get_latest_diagnostic_not_registered(self, db):
        repo = NetworkRepository(db)
        diagnostic = await repo.get_latest_diagnostic("TN-100003")
        assert diagnostic is not None
        assert "Not Registered" in diagnostic["network_registration"]


class TestTicketRepository:

    @pytest.mark.asyncio
    async def test_get_existing_ticket(self, db):
        repo = TicketRepository(db)
        ticket = await repo.get_ticket("BIL-78231")
        assert ticket is not None
        assert ticket["status"] == "in_progress"
        assert ticket["category"] == "billing"

    @pytest.mark.asyncio
    async def test_get_resolved_ticket_has_notes(self, db):
        repo = TicketRepository(db)
        ticket = await repo.get_ticket("NET-45901")
        assert ticket is not None
        assert ticket["status"] == "resolved"
        assert ticket["resolution_notes"] is not None

    @pytest.mark.asyncio
    async def test_get_nonexistent_ticket(self, db):
        repo = TicketRepository(db)
        ticket = await repo.get_ticket("XXX-00000")
        assert ticket is None

    @pytest.mark.asyncio
    async def test_list_tickets_for_account(self, db):
        repo = TicketRepository(db)
        tickets = await repo.list_tickets_for_account("TN-100001")
        assert len(tickets) >= 2
        ticket_ids = [t["ticket_id"] for t in tickets]
        assert "BIL-78231" in ticket_ids

    @pytest.mark.asyncio
    async def test_create_ticket_correct_billing_prefix(self, db):
        repo = TicketRepository(db)
        result = await repo.create_ticket("TN-100001", "billing", "Test billing ticket")
        assert result["ticket_id"].startswith("BIL-")
        assert result["status"] == "open"
        assert "estimated_resolution" in result
        await db.execute("DELETE FROM tickets WHERE ticket_id = $1", result["ticket_id"])

    @pytest.mark.asyncio
    async def test_create_ticket_unknown_category_defaults_general(self, db):
        repo = TicketRepository(db)
        result = await repo.create_ticket("TN-100001", "unknown_category", "Edge case")
        assert result["ticket_id"].startswith("GEN-")
        await db.execute("DELETE FROM tickets WHERE ticket_id = $1", result["ticket_id"])

    @pytest.mark.asyncio
    async def test_ticket_eta_varies_by_category(self, db):
        repo = TicketRepository(db)
        billing = await repo.create_ticket("TN-100001", "billing", "Billing test")
        network = await repo.create_ticket("TN-100001", "network", "Network test")
        assert billing["estimated_resolution"] != network["estimated_resolution"]
        await db.execute("DELETE FROM tickets WHERE ticket_id = ANY($1)", [billing["ticket_id"], network["ticket_id"]])
