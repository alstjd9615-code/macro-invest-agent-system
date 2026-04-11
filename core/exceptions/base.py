"""Typed application exception hierarchy for macro-invest-agent-platform.

All custom exceptions inherit from :class:`AppError`, which carries a machine-
readable ``error_code`` and a ``detail`` payload so that callers can handle
errors programmatically rather than parsing message strings.

Exception design rules:
- Every public exception class has an explicit ``error_code`` default.
- Subclasses refine the ``error_code`` to a specific domain prefix.
- HTTP status semantics (4xx / 5xx) are encoded in subclass names, not here.
- Secrets and PII must never appear in ``detail`` or ``message``.

Usage::

    from core.exceptions.base import NotFoundError, ValidationError

    raise NotFoundError(
        message="Signal result not found.",
        error_code="SIGNAL_NOT_FOUND",
        detail={"strategy_id": strategy_id},
    )
"""

from __future__ import annotations

from typing import Any


class AppError(Exception):
    """Base class for all application-level exceptions.

    Args:
        message: Human-readable error summary (safe to surface to callers).
        error_code: Machine-readable identifier, e.g. ``"SIGNAL_NOT_FOUND"``.
        detail: Optional structured context for debugging.  Must not contain
            secrets or PII.
    """

    error_code: str = "APP_ERROR"

    def __init__(
        self,
        message: str,
        *,
        error_code: str | None = None,
        detail: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        if error_code is not None:
            self.error_code = error_code
        self.detail: dict[str, Any] = detail or {}

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"{self.__class__.__name__}("
            f"error_code={self.error_code!r}, "
            f"message={self.message!r}, "
            f"detail={self.detail!r})"
        )


# ---------------------------------------------------------------------------
# 4xx — client / input errors
# ---------------------------------------------------------------------------


class ValidationError(AppError):
    """Raised when input data fails schema or business-rule validation.

    Maps to HTTP 422 Unprocessable Entity.
    """

    error_code = "VALIDATION_ERROR"


class NotFoundError(AppError):
    """Raised when a requested resource does not exist.

    Maps to HTTP 404 Not Found.
    """

    error_code = "NOT_FOUND"


class ConflictError(AppError):
    """Raised when an operation would create a conflicting state.

    Maps to HTTP 409 Conflict.
    """

    error_code = "CONFLICT"


# ---------------------------------------------------------------------------
# 5xx — server / infrastructure errors
# ---------------------------------------------------------------------------


class InternalError(AppError):
    """Raised for unexpected server-side errors that should not be retried.

    Maps to HTTP 500 Internal Server Error.
    """

    error_code = "INTERNAL_ERROR"


class StorageError(AppError):
    """Raised when a database or object-store operation fails.

    Maps to HTTP 503 Service Unavailable.
    """

    error_code = "STORAGE_ERROR"


class ConfigurationError(AppError):
    """Raised when the application is mis-configured at startup.

    Typically indicates a missing or invalid environment variable.
    This exception is fatal — the application should not continue.
    """

    error_code = "CONFIGURATION_ERROR"


# ---------------------------------------------------------------------------
# Domain-specific errors
# ---------------------------------------------------------------------------


class DomainError(AppError):
    """Base class for domain-logic violations (signal engine, feature compute).

    Raised when inputs are structurally valid but violate a business rule.
    """

    error_code = "DOMAIN_ERROR"


class MCPToolError(AppError):
    """Raised by MCP tool implementations on execution failure.

    Agents should treat this as a non-retryable tool call failure unless
    the subclass indicates otherwise.
    """

    error_code = "MCP_TOOL_ERROR"
