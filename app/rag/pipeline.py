import google.generativeai as genai
import os
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

IMPORTANT: You are NOT a human. If asked, acknowledge you are an AI assistant."""

GROUNDED_PROMPT_TEMPLATE = """KNOWLEDGE BASE CONTEXT:
{context}

CONVERSATION HISTORY:
{history}

CUSTOMER MESSAGE: {user_message}

Using the knowledge base context provided above, give a helpful, accurate response to the customer. If the context doesn't contain enough information, say so and offer escalation to a human agent.

INTENT DETECTED: {intent}
"""


class RAGPipeline:
    def __init__(self):
        genai.configure(
            api_key=os.environ["GOOGLE_API_KEY"]
        )
        self._model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            system_instruction=SYSTEM_PROMPT,
            generation_config=genai.GenerationConfig(
                temperature=settings.gemini_temperature,
                max_output_tokens=settings.gemini_max_output_tokens,
                top_p=0.95,
            ),
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
        parts = []
        for i, doc in enumerate(retrieved_docs, 1):
            parts.append(f"[Source {i}: {doc['source']} | Relevance: {doc['relevance_score']}]\n{doc['content']}")
        return "\n\n---\n\n".join(parts)

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

        context_text = self._format_context(retrieved_docs)
        history_text = self._format_history(history)

        prompt = GROUNDED_PROMPT_TEMPLATE.format(
            context=context_text,
            history=history_text,
            user_message=user_message,
            intent=intent,
        )

        response = self._model.generate_content(prompt)

        if response.usage_metadata:
            metrics.record_tokens(
                input_tokens=response.usage_metadata.prompt_token_count or 0,
                output_tokens=response.usage_metadata.candidates_token_count or 0,
            )

        answer = response.text.strip()
        sources = list({doc["source"] for doc in retrieved_docs})

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

    def _map_intent_to_category(self, intent: str) -> str:
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
