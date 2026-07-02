from google import genai

from app.config import get_settings
from app.rag.vector_store import knowledge_base
from app.utils.observability import get_logger, RequestMetrics

settings = get_settings()
logger = get_logger(__name__)

SYSTEM_PROMPT = """You are Nova, TeleNova's intelligent customer support assistant. You are helpful, empathetic, and concise.

GUIDELINES:
- Always address the customer's actual concern directly
- Use information from the provided knowledge base context when available
- If you cannot find information in the context, say so clearly and offer to connect them with a human agent
- Keep responses focused and under 150 words unless a detailed explanation is genuinely needed
- Use bullet points for multi-step instructions
- Never make up billing amounts, ticket numbers, or account-specific data
- Maintain a warm, professional tone
- If a customer seems frustrated, acknowledge their frustration before providing information

IMPORTANT: You are NOT a human. If asked, acknowledge you are an AI assistant.
"""

GROUNDED_PROMPT_TEMPLATE = """KNOWLEDGE BASE CONTEXT:
{context}

CONVERSATION HISTORY:
{history}

CUSTOMER MESSAGE:
{user_message}

INTENT DETECTED:
{intent}

Respond using ONLY the provided knowledge base when possible.
If the knowledge base does not contain enough information,
say so clearly and offer escalation to a human agent.
"""


class RAGPipeline:
    def __init__(self):
        self._client = genai.Client(
            vertexai=True,
            project=settings.google_cloud_project,
            location=settings.google_cloud_location,
        )

    def _format_history(self, history: list[dict]) -> str:
        if not history:
            return "No prior conversation."

        formatted = []

        for turn in history[-6:]:
            role = "Customer" if turn["role"] == "user" else "Nova"
            formatted.append(f"{role}: {turn['content']}")

        return "\n".join(formatted)

    def _format_context(self, retrieved_docs: list[dict]) -> str:
        if not retrieved_docs:
            return "No relevant knowledge base content found."

        context = []

        for i, doc in enumerate(retrieved_docs, start=1):
            context.append(
                f"""[Source {i}]
Source: {doc["source"]}
Relevance: {doc["relevance_score"]}

{doc["content"]}
"""
            )

        return "\n\n----------------------\n\n".join(context)

    async def generate(
        self,
        user_message: str,
        intent: str,
        history: list[dict],
        metrics: RequestMetrics,
    ) -> dict:

        intent_category = self._map_intent_to_category(intent)

        retrieved_docs = knowledge_base.retrieve(
            query=user_message,
            n_results=4,
            intent_filter=intent_category,
        )

        prompt = GROUNDED_PROMPT_TEMPLATE.format(
            context=self._format_context(retrieved_docs),
            history=self._format_history(history),
            user_message=user_message,
            intent=intent,
        )

        full_prompt = f"{SYSTEM_PROMPT}\n\n{prompt}"

        response = self._client.models.generate_content(
            model=settings.gemini_model,
            contents=full_prompt,
        )

        answer = response.text.strip()

        try:
            usage = response.usage_metadata

            metrics.record_tokens(
                input_tokens=getattr(usage, "prompt_token_count", 0) or 0,
                output_tokens=getattr(usage, "candidates_token_count", 0) or 0,
            )

        except Exception:
            pass

        sources = list(
            {
                doc["source"]
                for doc in retrieved_docs
            }
        )

        logger.info(
            "rag_generation_complete",
            intent=intent,
            context_sources=sources,
            response_length=len(answer),
        )

        return {
            "answer": answer,
            "sources": sources,
            "retrieved_count": len(retrieved_docs),
        }

    def _map_intent_to_category(self, intent: str) -> str | None:
        mapping = {
            "billing_inquiry": "billing",
            "billing_dispute": "billing",
            "payment_issue": "billing",
            "plan_upgrade": "plan",
            "plan_inquiry": "plan",
            "plan_downgrade": "plan",
            "network_issue": "network",
            "signal_problem": "network",
            "slow_data": "network",
            "escalation_request": "escalation",
            "ticket_status": "account",
            "account_information": "account",
            "general_support": None,
        }

        return mapping.get(intent)


rag_pipeline = RAGPipeline()