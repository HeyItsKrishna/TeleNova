from typing import Optional
from app.utils.observability import get_logger, RequestMetrics
from app.utils.session import UserSession
from app.rag.pipeline import rag_pipeline

logger = get_logger(__name__)

INTENT_TO_AGENT = {
    "billing_inquiry": "billing",
    "billing_dispute": "billing",
    "payment_issue": "billing",
    "plan_upgrade": "support",
    "plan_inquiry": "support",
    "plan_downgrade": "support",
    "network_issue": "network",
    "signal_problem": "network",
    "slow_data": "network",
    "escalation_request": "escalation",
    "ticket_status": "support",
    "account_information": "support",
    "general_support": "support",
    "troubleshooting": "network",
}

INTENT_KEYWORDS = {
    "billing_inquiry": ["bill", "billing", "charge", "payment", "invoice", "autopay", "statement"],
    "billing_dispute": ["overcharged", "wrong charge", "dispute", "incorrect", "refund", "credit"],
    "payment_issue": ["payment", "pay", "due", "missed", "late fee", "extension"],
    "plan_upgrade": ["upgrade", "switch plan", "better plan", "more data", "unlimited"],
    "plan_inquiry": ["plan", "plans", "pricing", "cost", "features", "compare"],
    "plan_downgrade": ["downgrade", "cheaper", "lower plan", "reduce"],
    "network_issue": ["no signal", "no service", "outage", "network down", "can't connect"],
    "signal_problem": ["signal", "weak signal", "one bar", "drops", "call dropping"],
    "slow_data": ["slow", "slow data", "speed", "buffering", "loading slowly"],
    "escalation_request": ["speak to human", "talk to agent", "transfer", "supervisor", "manager", "escalate"],
    "ticket_status": ["ticket", "case", "complaint", "status", "reference", "BIL-", "NET-", "ACC-", "GEN-"],
    "account_information": ["account", "my account", "profile", "number", "settings"],
    "troubleshooting": ["fix", "troubleshoot", "help me", "problem", "issue", "not working"],
}


def classify_intent(message: str, session: UserSession) -> str:
    message_lower = message.lower()
    scores: dict[str, int] = {}
    for intent, keywords in INTENT_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in message_lower)
        if score > 0:
            scores[intent] = score

    if scores:
        return max(scores, key=scores.get)

    return session.active_intent or "general_support"


async def route_and_respond(
    user_message: str,
    session: UserSession,
    metrics: RequestMetrics,
) -> dict:
    intent = classify_intent(user_message, session)
    metrics.intent = intent
    agent_type = INTENT_TO_AGENT.get(intent, "support")

    logger.info("intent_classified", intent=intent, agent_type=agent_type, session_id=session.session_id)

    rag_result = await rag_pipeline.generate(
        user_message=user_message,
        intent=intent,
        history=session.get_history_for_prompt(),
        metrics=metrics,
    )

    response_text = rag_result["answer"]
    suggested_actions = _get_suggested_actions(intent)

    return {
        "response": response_text,
        "intent": intent,
        "agent_type": agent_type,
        "sources": rag_result.get("sources", []),
        "suggested_actions": suggested_actions,
        "requires_human": intent == "escalation_request",
    }


def _get_suggested_actions(intent: str) -> list[str]:
    action_map = {
        "billing_inquiry": ["View my bill", "Set up AutoPay", "Dispute a charge"],
        "billing_dispute": ["Review line items", "Apply for credit", "Speak to billing specialist"],
        "plan_upgrade": ["Compare plans", "Upgrade to Unlimited Pro", "Get family plan discount"],
        "plan_inquiry": ["Compare all plans", "Check my current plan", "See add-ons"],
        "network_issue": ["Check outage map", "Run diagnostics", "Report an outage"],
        "signal_problem": ["Run speed test", "Enable Wi-Fi Calling", "Check coverage map"],
        "slow_data": ["Check data usage", "Run speed test", "Upgrade data plan"],
        "escalation_request": ["Connect to live agent", "Request callback", "Schedule a call"],
        "ticket_status": ["View all my tickets", "Create new ticket"],
        "account_information": ["View account details", "Update payment method", "Add a line"],
        "general_support": ["Browse FAQs", "View account", "Contact us"],
        "troubleshooting": ["Step-by-step guide", "Run diagnostics", "Create a ticket"],
    }
    return action_map.get(intent, ["View account", "Contact us"])
