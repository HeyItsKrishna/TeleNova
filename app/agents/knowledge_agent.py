from google.adk.agents import Agent
from google.adk.tools import tool
from app.config import get_settings
from app.utils.observability import get_logger

settings = get_settings()
logger = get_logger(__name__)


@tool
def search_knowledge_base(query: str, category: str = "") -> dict:
    """Search the TeleNova knowledge base for relevant support information.

    Args:
        query: The customer's question or search term.
        category: Optional category filter — one of: billing, network, plan, account, escalation.

    Returns:
        Relevant knowledge base excerpts with source attribution.
    """
    from app.rag.vector_store import knowledge_base as kb

    intent_filter = category if category in {"billing", "network", "plan", "account", "escalation"} else None
    results = kb.retrieve(query=query, n_results=3, intent_filter=intent_filter)

    if not results:
        return {
            "found": False,
            "message": "No relevant information found in the knowledge base for this query.",
            "suggestion": "Escalate to a human specialist.",
        }

    formatted = []
    for doc in results:
        formatted.append({
            "source": doc["source"],
            "relevance": doc["relevance_score"],
            "excerpt": doc["content"][:500],
        })

    return {
        "found": True,
        "result_count": len(formatted),
        "results": formatted,
    }


@tool
def get_policy_answer(topic: str) -> dict:
    """Retrieve a specific policy or FAQ answer from TeleNova's knowledge base.

    Args:
        topic: The policy topic to look up, e.g. 'late payment fee', 'data overage policy',
               'plan downgrade timing', 'device unlock requirements'.

    Returns:
        Policy details with source document reference.
    """
    policy_index = {
        "late payment fee": ("billing_faq", "A $10 late fee is applied on Day 6 past the due date. Service may suspend on Day 15 if unpaid."),
        "data overage": ("billing_faq", "Data overage is $10 per GB beyond plan limit, capped at $50/month maximum overage charge."),
        "autopay discount": ("billing_faq", "AutoPay saves $5/month. Processes 1 day before the due date. Accepted: Visa, Mastercard, Amex, Discover, Debit, ACH, UPI."),
        "plan downgrade timing": ("plan_comparison", "Downgrades take effect at the next billing cycle start. Upgrades are immediate with pro-rated charges."),
        "plan upgrade timing": ("plan_comparison", "Upgrades are effective immediately. A pro-rated charge applies for the remainder of the current billing cycle."),
        "device unlock": ("customer_support_handbook", "Paid-in-full devices: instant unlock. Installment devices: must complete or pay off remaining balance; 2-business-day processing."),
        "voluntary suspension": ("customer_support_handbook", "Account can be suspended voluntarily for 30–90 days at $10/month to hold the number. AutoPay pauses during suspension."),
        "outage credit": ("network_troubleshooting", "Outages exceeding 4 continuous hours qualify for a bill credit automatically. No claim needed."),
        "escalation tiers": ("escalation_sop", "T1: AI. T2: Live Agent (<5 min wait). T3: Specialist (24-hr callback). T4: Executive (same-day ack)."),
        "number porting": ("customer_support_handbook", "Porting in: provide previous carrier account + PIN; 2–4 hours. TeleNova cannot block port-out requests."),
        "roaming activation": ("network_troubleshooting", "International roaming must be enabled on the account; activation takes up to 2 hours."),
        "senior discount": ("customer_support_handbook", "$10 off per line per month on Starter or Connect plans for customers 65+ (government ID required)."),
        "military discount": ("customer_support_handbook", "15% off total monthly bill for military/veterans verified via ID.me."),
    }

    topic_lower = topic.lower()
    for key, (source, answer) in policy_index.items():
        if key in topic_lower or topic_lower in key:
            return {
                "found": True,
                "topic": key,
                "answer": answer,
                "source": source,
            }

    return {
        "found": False,
        "message": f"No indexed policy found for '{topic}'. Try search_knowledge_base for a broader search.",
    }


knowledge_agent = Agent(
    name="TeleNova Knowledge Agent",
    model=settings.gemini_model,
    description="Retrieves accurate information from TeleNova's knowledge base for policy, FAQ, and procedural questions.",
    instruction="""You are TeleNova's knowledge specialist. Your role:
1. Search the knowledge base for accurate answers to customer policy and FAQ questions
2. Use get_policy_answer for specific policy topics (fees, discounts, timing rules)
3. Use search_knowledge_base for broader or more nuanced questions
4. Always attribute answers to their source document
5. If the knowledge base does not contain sufficient information, say so clearly
   and recommend escalation to a human specialist

Never fabricate policy details. Accuracy is critical in a billing/support context.""",
    tools=[search_knowledge_base, get_policy_answer],
)
