"""Structured logger factory for the macro-invest-agent-platform.

Provides a single :func:`get_logger` factory that returns a
:mod:`structlog` logger pre-configured for the current environment:

- **Local / pretty mode**: human-readable, colourised console output.
- **JSON mode**: one-line JSON records suitable for log aggregators.

Every log record includes a ``trace_id`` field so that requests can be
correlated across the domain, MCP, and agent layers.

Usage::

    from core.logging.logger import get_logger

    log = get_logger(__name__)
    log.info("signal_computed", strategy="base-macro-v1", direction="BULLISH")
"""

import logging
import sys
import uuid
from contextvars import ContextVar
from typing import Any

import structlog
from structlog.types import FilteringBoundLogger

from core.config.settings import get_settings

# ---------------------------------------------------------------------------
# Trace-ID context variable
# ---------------------------------------------------------------------------

#: Thread/async-safe storage for the current request's trace identifier.
_trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")


def set_trace_id(trace_id: str | None = None) -> str:
    """Set the trace ID for the current execution context.

    If *trace_id* is ``None`` or empty a new UUID4 is generated.
    Returns the trace ID that was set.
    """
    tid = trace_id or str(uuid.uuid4())
    _trace_id_var.set(tid)
    return tid


def get_trace_id() -> str:
    """Return the trace ID for the current execution context, or an empty string."""
    return _trace_id_var.get()


# ---------------------------------------------------------------------------
# Structlog processor that injects the trace_id into every log record
# ---------------------------------------------------------------------------


def _inject_trace_id(
    logger: Any,  # noqa: ANN401
    method: str,
    event_dict: structlog.types.EventDict,
) -> structlog.types.EventDict:
    """Structlog processor: add ``trace_id`` from the current context var."""
    tid = get_trace_id()
    if tid:
        event_dict["trace_id"] = tid
    return event_dict


# ---------------------------------------------------------------------------
# One-time configuration (idempotent)
# ---------------------------------------------------------------------------

_configured = False


def _configure_structlog() -> None:
    """Configure structlog processors and output format.

    Called once per process.  Subsequent calls are no-ops.
    """
    global _configured  # noqa: PLW0603
    if _configured:
        return

    settings = get_settings()
    log_level = getattr(logging, settings.log_level.value, logging.INFO)

    # Configure stdlib logging as the backend
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        _inject_trace_id,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
    ]

    if settings.log_pretty:
        # Human-readable output for local development
        processors: list[Any] = [
            *shared_processors,
            structlog.dev.ConsoleRenderer(colors=True),
        ]
    else:
        # JSON output for production / log aggregators
        processors = [
            *shared_processors,
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    _configured = True


# ---------------------------------------------------------------------------
# Public factory
# ---------------------------------------------------------------------------


def get_logger(name: str) -> FilteringBoundLogger:
    """Return a configured structlog logger bound to *name*.

    Call once per module::

        log = get_logger(__name__)

    Args:
        name: Typically ``__name__`` of the calling module.

    Returns:
        A structlog ``BoundLogger`` ready to use.
    """
    _configure_structlog()
    return structlog.get_logger(name)  # type: ignore[no-any-return]
