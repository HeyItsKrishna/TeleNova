import asyncio
import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

from app.api.models import (
    ChatRequest,
    ChatResponse,
    WebhookRequest,
    WebhookResponse,
    HealthResponse,
)
from app.agents.orchestrator import route_and_respond
from app.utils.session import session_store
from app.utils.observability import configure_logging, get_logger, RequestMetrics
from app.rag.vector_store import knowledge_base
from app.db.connection import database
from app.config import get_settings

settings = get_settings()
logger = get_logger(__name__)

_kb_loaded = False
_db_connected = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _kb_loaded, _db_connected

    configure_logging()
    logger.info("startup_begin")

    # Database startup
    try:
        await database.connect()
        _db_connected = await database.health_check()
    except Exception:
        traceback.print_exc()
        _db_connected = False

    # Knowledge base startup
    try:
        chunk_count = knowledge_base.load_knowledge_base(force_reload=True)
        _kb_loaded = chunk_count > 0

    except Exception as e:
        traceback.print_exc()

        logger.error(
            "knowledge_base_load_failed",
            error=str(e),
        )

        _kb_loaded = False

    async def cleanup_sessions():
        while True:
            await asyncio.sleep(300)
            session_store.cleanup_expired()

    task = asyncio.create_task(cleanup_sessions())

    yield

    task.cancel()
    await database.disconnect()
    logger.info("shutdown_complete")


from fastapi.openapi.utils import get_openapi

app = FastAPI(
    title="TeleNova AI Support API",
    description="Conversational AI customer support system powered by Gemini and Google ADK",
    version="1.0.0",
    lifespan=lifespan,
)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # Force OpenAPI 3.0.3 for Dialogflow CX / Conversational Agents
    schema["openapi"] = "3.0.3"

    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    return HealthResponse(
        status="healthy" if _db_connected else "degraded",
        version="1.0.0",
        environment=settings.app_env,
        knowledge_base_loaded=_kb_loaded,
        active_sessions=session_store.active_count,
        database_connected=_db_connected,
    )


@app.post("/chat", response_model=ChatResponse, tags=["Conversation"])
async def chat(request: ChatRequest, background_tasks: BackgroundTasks):
    session = session_store.get_or_create(
        session_id=request.session_id,
        user_id=request.user_id,
    )

    if request.account_number and not session.account_number:
        session.account_number = request.account_number

    metrics = RequestMetrics(session_id=session.session_id)

    session.add_turn(
        role="user",
        content=request.message,
        intent=session.active_intent,
    )

    try:
        result = await route_and_respond(
            user_message=request.message,
            session=session,
            metrics=metrics,
        )

    except Exception as e:
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=f"{type(e).__name__}: {e}",
        )

    session.add_turn(
        role="assistant",
        content=result["response"],
        intent=result["intent"],
        metadata={"sources": result.get("sources", [])},
    )

    observability_data = metrics.finalize()

    logger.info(
        "chat_complete",
        **observability_data,
    )

    return ChatResponse(
        response=result["response"],
        session_id=session.session_id,
        intent=result["intent"],
        agent_type=result["agent_type"],
        suggested_actions=result.get("suggested_actions", []),
        requires_human=result.get("requires_human", False),
        sources=result.get("sources", []),
        observability=observability_data,
    )


@app.post("/webhook", tags=["Dialogflow CX"])
async def dialogflow_webhook(request: WebhookRequest):
    session_id = request.get_session_id()
    tag = request.get_tag()
    intent_name = request.get_intent_display_name()
    parameters = request.get_parameters()
    query_text = request.get_query_text()

    logger.info(
        "webhook_received",
        session_id=session_id,
        tag=tag,
        intent=intent_name,
    )

    session = session_store.get_or_create(session_id=session_id)

    if parameters.get("account_number"):
        session.account_number = parameters["account_number"]

    metrics = RequestMetrics(
        session_id=session_id,
        intent=intent_name,
    )

    if not query_text:
        query_text = (
            f"Help me with {intent_name.replace('_', ' ')}"
            if intent_name
            else "I need help"
        )

    try:
        result = await route_and_respond(
            user_message=query_text,
            session=session,
            metrics=metrics,
        )

        response_text = result["response"]

    except Exception as e:
        traceback.print_exc()

        logger.error(
            "webhook_error",
            error=str(e),
            session_id=session_id,
        )

        response_text = (
            "I'm sorry, I encountered an issue processing your request. "
            "Let me connect you with a specialist."
        )

    session.add_turn(
        role="user",
        content=query_text,
        intent=intent_name or "unknown",
    )

    session.add_turn(
        role="assistant",
        content=response_text,
        intent=intent_name or "unknown",
    )

    observability_data = metrics.finalize()

    logger.info(
        "webhook_complete",
        **observability_data,
    )

    webhook_response = WebhookResponse.from_text(
        text=response_text,
        session_params={
            "last_intent": intent_name,
            "response_generated": True,
        },
    )

    return webhook_response.model_dump(exclude_none=True)