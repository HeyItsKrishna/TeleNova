import structlog
import time
import uuid
import logging
from contextlib import contextmanager
from typing import Any, Generator
from app.config import get_settings

settings = get_settings()



def configure_logging() -> None:
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    return structlog.get_logger(name)


class RequestMetrics:
    def __init__(self, session_id: str, intent: str = "unknown"):
        self.request_id = str(uuid.uuid4())
        self.session_id = session_id
        self.intent = intent
        self.start_time = time.monotonic()
        self.token_count_input = 0
        self.token_count_output = 0
        self.latency_ms = 0.0

    def record_tokens(self, input_tokens: int, output_tokens: int) -> None:
        self.token_count_input = input_tokens
        self.token_count_output = output_tokens

    def finalize(self) -> dict[str, Any]:
        self.latency_ms = round((time.monotonic() - self.start_time) * 1000, 2)
        total_tokens = self.token_count_input + self.token_count_output
        estimated_cost = round(
            (self.token_count_input * 0.000000075) + (self.token_count_output * 0.0000003), 6
        )
        return {
            "request_id": self.request_id,
            "session_id": self.session_id,
            "intent": self.intent,
            "latency_ms": self.latency_ms,
            "token_count_input": self.token_count_input,
            "token_count_output": self.token_count_output,
            "total_tokens": total_tokens,
            "estimated_cost_usd": estimated_cost,
        }


@contextmanager
def timed_operation(logger: structlog.BoundLogger, operation: str) -> Generator:
    start = time.monotonic()
    try:
        yield
    finally:
        elapsed = round((time.monotonic() - start) * 1000, 2)
        logger.info("operation_complete", operation=operation, latency_ms=elapsed)
