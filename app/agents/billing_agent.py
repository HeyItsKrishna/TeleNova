from google.adk.agents import Agent
from google.adk.tools import tool
from app.config import get_settings
from app.utils.observability import get_logger
from app.db.container import repositories

settings = get_settings()
logger = get_logger(__name__)


@tool
async def get_billing_details(account_number: str, billing_cycle: str = "current") -> dict:
    """Fetch detailed billing information for a customer account.

    Args:
        account_number: Customer's TeleNova account number.
        billing_cycle: 'current' or 'previous' billing cycle.

    Returns:
        Itemized billing breakdown.
    """
    cycle = await repositories.billing.get_billing_cycle(account_number, billing_cycle)
    if cycle is None:
        return {"error": f"Billing information not found for account {account_number}."}

    return {
        "account_number": cycle["account_number"],
        "billing_cycle": cycle["cycle_label"],
        "plan_charge": float(cycle["plan_charge"]),
        "taxes_and_fees": float(cycle["taxes_and_fees"]),
        "add_ons": float(cycle["add_ons"]),
        "overages": float(cycle["overages"]),
        "credits": float(cycle["credits"]),
        "total": float(cycle["total"]),
        "line_items": [
            {"description": item["description"], "amount": float(item["amount"])}
            for item in cycle["line_items"]
        ],
    }


@tool
async def apply_billing_credit(account_number: str, credit_amount: float, reason: str) -> dict:
    """Apply a goodwill or error credit to a customer's account.

    Args:
        account_number: Customer's account number.
        credit_amount: Amount to credit in USD (max $50 without supervisor approval).
        reason: Reason for the credit.

    Returns:
        Confirmation of credit application.
    """
    if credit_amount > 50:
        return {
            "success": False,
            "message": f"Credit of ${credit_amount:.2f} exceeds agent authorization limit of $50.00. Escalating to supervisor for approval.",
            "escalation_required": True,
        }

    result = await repositories.billing.apply_credit(account_number, credit_amount, reason)
    if not result.get("success"):
        return result

    return {
        "success": True,
        "account_number": result["account_number"],
        "credit_amount": result["credit_amount"],
        "reason": reason,
        "message": f"Credit of ${credit_amount:.2f} applied to account {result['account_number']}. It will reflect on your next billing statement.",
        "new_balance": result["new_balance"],
    }


@tool
async def check_payment_history(account_number: str) -> dict:
    """Check recent payment history for a customer account.

    Args:
        account_number: Customer's account number.

    Returns:
        Last 3 payment records.
    """
    payments = await repositories.billing.get_payment_history(account_number, limit=3)
    if not payments:
        return {"error": f"Payment history not found for account {account_number}."}

    return {
        "account_number": account_number.upper(),
        "payment_history": [
            {
                "date": p["payment_date"].isoformat(),
                "amount": float(p["amount"]),
                "method": p["method"],
                "status": p["status"],
            }
            for p in payments
        ],
    }


billing_agent = Agent(
    name="TeleNova Billing Agent",
    model=settings.gemini_model,
    description="Specialized agent for billing disputes, charges, credits, and payment inquiries.",
    instruction="""You are TeleNova's billing specialist agent. Your responsibilities:
1. Retrieve and explain billing details clearly using line items
2. Investigate disputed charges by comparing with plan details
3. Apply appropriate credits for legitimate billing errors (up to $50)
4. Explain overage charges and how to avoid them
5. Suggest AutoPay enrollment for the $5/month discount
6. Escalate to supervisor for credits over $50 or complex disputes

Always be empathetic when customers are concerned about unexpected charges.
Verify account identity before discussing billing details.""",
    tools=[get_billing_details, apply_billing_credit, check_payment_history],
)
