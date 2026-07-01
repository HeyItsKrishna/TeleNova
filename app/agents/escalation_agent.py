from google.adk.agents import Agent
from google.adk.tools import tool
from app.config import get_settings
from app.utils.observability import get_logger
from app.db.container import repositories

settings = get_settings()
logger = get_logger(__name__)


@tool
async def assess_escalation_priority(
    account_number: str,
    issue_category: str,
    issue_description: str,
    previous_contacts: int = 0,
) -> dict:
    """Assess the priority and appropriate tier for an escalation.
    
    Args:
        account_number: Customer's account number.
        issue_category: Category of the issue (billing, network, account, device).
        issue_description: Description of the unresolved issue.
        previous_contacts: Number of prior contacts about this issue.
    
    Returns:
        Escalation tier, priority, and recommended action.
    """
    account = await repositories.accounts.get_account(account_number)

    is_high_value = False
    if account:
       plan = account["plan"]
       is_high_value = plan in ("business_pro", "unlimited_pro")
       
    priority_score = 0

    if previous_contacts >= 3:
        priority_score += 2
    elif previous_contacts >= 1:
        priority_score += 1

    if is_high_value:
        priority_score += 2

    billing_keywords = ["fraud", "legal", "lawsuit", "dispute", "unauthorized"]
    if any(kw in issue_description.lower() for kw in billing_keywords):
        priority_score += 3

    if priority_score >= 5:
        tier = "T4 - Executive Resolution"
        sla = "Same-day acknowledgment; 5 business day resolution"
    elif priority_score >= 3:
        tier = "T3 - Specialist Team"
        sla = "24-hour callback; 3 business day resolution"
    else:
        tier = "T2 - Live Agent"
        sla = "< 5 minute wait; same session or 24-hour resolution"

    return {
        "account_number": account_number.upper(),
        "issue_category": issue_category,
        "priority_score": priority_score,
        "recommended_tier": tier,
        "sla_commitment": sla,
        "is_high_value_account": is_high_value,
        "previous_contacts": previous_contacts,
    }


@tool
def initiate_human_handoff(
    account_number: str,
    session_summary: str,
    escalation_tier: str,
    customer_callback: str = "",
) -> dict:
    """Initiate transfer to a human agent with full context handoff.
    
    Args:
        account_number: Customer's account number.
        session_summary: Summary of the AI conversation and steps already taken.
        escalation_tier: The tier to escalate to (T2, T3, T4).
        customer_callback: Customer's preferred callback number.
    
    Returns:
        Escalation confirmation and estimated wait time.
    """
    import random
    case_id = f"CASE-{random.randint(100000, 999999)}"
    wait_times = {"T2 - Live Agent": "3–8 minutes", "T3 - Specialist Team": "24-hour callback", "T4 - Executive Resolution": "Same-day acknowledgment"}
    wait = wait_times.get(escalation_tier, "10–15 minutes")
    return {
        "case_id": case_id,
        "account_number": account_number.upper(),
        "escalation_tier": escalation_tier,
        "estimated_wait": wait,
        "callback_number": customer_callback or "Number on file",
        "context_transferred": True,
        "session_summary_logged": True,
        "message": f"Your case {case_id} has been escalated to a TeleNova specialist. Context from our conversation has been passed along — you won't need to repeat yourself. {f'Expected wait: {wait}.' if 'callback' not in wait.lower() else f'You will receive a callback within {wait}.'}",
    }


@tool
def apply_goodwill_gesture(account_number: str, gesture_type: str) -> dict:
    """Apply a goodwill gesture for a customer experiencing significant inconvenience.
    
    Args:
        account_number: Customer's account number.
        gesture_type: Type of gesture ('bill_credit_20', 'bill_credit_50', 'data_bonus_5gb', 'free_month').
    
    Returns:
        Confirmation of goodwill gesture applied.
    """
    gestures = {
        "bill_credit_20": {"description": "$20 bill credit", "value": 20.00, "requires_supervisor": False},
        "bill_credit_50": {"description": "$50 bill credit", "value": 50.00, "requires_supervisor": True},
        "data_bonus_5gb": {"description": "5 GB data bonus for current cycle", "value": 0, "requires_supervisor": False},
        "free_month": {"description": "One free month of service", "value": None, "requires_supervisor": True},
    }
    gesture = gestures.get(gesture_type)
    if not gesture:
        return {"error": f"Unknown gesture type: {gesture_type}. Valid types: {list(gestures.keys())}"}
    if gesture["requires_supervisor"]:
        return {
            "applied": False,
            "message": f"The {gesture['description']} requires supervisor approval. Escalating your request.",
            "requires_supervisor": True,
        }
    import random
    return {
        "applied": True,
        "confirmation_id": f"GWG-{random.randint(10000, 99999)}",
        "account_number": account_number.upper(),
        "gesture": gesture["description"],
        "message": f"We've applied a {gesture['description']} to your account as an apology for the inconvenience. It will reflect on your next statement.",
    }


escalation_agent = Agent(
    name="TeleNova Escalation Agent",
    model=settings.gemini_model,
    description="Handles escalation assessment, human handoff coordination, and goodwill gestures for frustrated customers.",
    instruction="""You are TeleNova's escalation specialist agent. Your responsibilities:
1. Assess the appropriate escalation tier based on issue severity and customer history
2. Apply goodwill gestures for customers who have experienced significant inconvenience
3. Coordinate warm handoffs to human agents with full context
4. Never leave a customer without a clear next step and case reference number
5. Acknowledge frustration genuinely before explaining escalation steps

Your primary goal is to restore customer confidence in TeleNova even when the issue cannot be resolved immediately.
Always provide a case number and SLA commitment before ending the escalation interaction.""",
    tools=[assess_escalation_priority, initiate_human_handoff, apply_goodwill_gesture],
)
