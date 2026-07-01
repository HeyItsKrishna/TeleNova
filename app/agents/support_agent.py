from google.adk.agents import Agent
from google.adk.tools import tool
from app.config import get_settings
from app.utils.observability import get_logger
from app.db.container import repositories

settings = get_settings()
logger = get_logger(__name__)


@tool
async def check_account_status(account_number: str) -> dict:
    """Check the status of a customer account by account number.

    Args:
        account_number: The customer's TeleNova account number.

    Returns:
        Account status, plan type, and balance information.
    """
    account = await repositories.accounts.get_account(account_number)
    if account is None:
        return {"error": f"Account {account_number} not found. Please verify the account number."}
    return {
        "account_number": account["account_number"],
        "status": account["status"],
        "plan": account["plan"],
        "balance_due": float(account["balance_due"]),
        "due_date": account["due_date"].isoformat() if account["due_date"] else None,
    }


@tool
async def get_ticket_status(ticket_id: str) -> dict:
    """Retrieve the status of a support ticket.

    Args:
        ticket_id: The ticket ID in format BIL-XXXXX, NET-XXXXX, ACC-XXXXX, etc.

    Returns:
        Ticket status, assignee team, and last update.
    """
    ticket = await repositories.tickets.get_ticket(ticket_id)
    if ticket is None:
        return {"error": f"Ticket {ticket_id} not found. Please verify the ticket number."}

    result = {
        "ticket_id": ticket["ticket_id"],
        "status": ticket["status"],
        "category": ticket["category"],
        "assigned_team": ticket["assigned_team"],
        "created_date": ticket["created_at"].isoformat(),
        "last_updated": ticket["updated_at"].isoformat(),
        "estimated_resolution": ticket["estimated_resolution"],
    }
    if ticket.get("resolution_notes"):
        result["resolution_notes"] = ticket["resolution_notes"]
    return result


@tool
async def get_data_usage(account_number: str) -> dict:
    """Get current data usage for the billing cycle.

    Args:
        account_number: The customer's TeleNova account number.

    Returns:
        Data usage statistics for current billing cycle.
    """
    usage = await repositories.accounts.get_data_usage(account_number)
    if usage is None:
        return {"error": "Usage data not available for this account."}

    result = {
        "account_number": usage["account_number"],
        "used_gb": float(usage["used_gb"]),
        "hotspot_used_gb": float(usage["hotspot_used_gb"]),
        "hotspot_limit_gb": float(usage["hotspot_limit_gb"]),
        "cycle_end": usage["cycle_end"].isoformat(),
    }
    if usage["plan_limit_gb"] is not None:
        result["plan_limit_gb"] = float(usage["plan_limit_gb"])
        result["remaining_gb"] = round(float(usage["plan_limit_gb"]) - float(usage["used_gb"]), 2)
    else:
        result["plan_limit_gb"] = "Unlimited"
    if usage["priority_gb_used"] is not None:
        result["priority_gb_used"] = float(usage["priority_gb_used"])
        result["priority_gb_limit"] = float(usage["priority_gb_limit"])
    return result


@tool
async def create_support_ticket(account_number: str, category: str, description: str) -> dict:
    """Create a new support ticket for a customer issue.

    Args:
        account_number: Customer's account number.
        category: Issue category (billing, network, account, device, general).
        description: Brief description of the issue.

    Returns:
        New ticket ID and estimated resolution time.
    """
    result = await repositories.tickets.create_ticket(account_number, category, description)
    result["message"] = f"Ticket {result['ticket_id']} created successfully. You'll receive updates via SMS and email."
    return result


support_agent = Agent(
    name="TeleNova Support Agent",
    model=settings.gemini_model,
    description="Primary customer support agent that handles general inquiries and coordinates specialized agents.",
    instruction="""You are Nova, TeleNova's primary AI support agent. Your role is to:
1. Understand the customer's issue and categorize it correctly
2. Use available tools to fetch account and ticket information
3. Provide accurate, empathetic responses
4. Create tickets when an issue cannot be resolved in the current session
5. Escalate to human agents when the situation requires it

Always verify account information before making changes. Be concise but thorough.""",
    tools=[check_account_status, get_ticket_status, get_data_usage, create_support_ticket],
)
