"""Base MCP request/response schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class MCPRequest(BaseModel):
    """Base class for all MCP requests.

    MCP (Model Context Protocol) requests contain the input parameters
    and metadata for operations on macro data and signals.
    """

    request_id: str = Field(..., description="Unique request identifier for tracing")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Request creation timestamp",
    )

    class Config:
        """Pydantic config for base request."""

        json_schema_extra = {
            "example": {
                "request_id": "req-12345",
                "timestamp": "2026-04-11T12:00:00Z",
            }
        }


class MCPResponse(BaseModel, extra="forbid"):
    """Base class for all MCP responses.

    MCP responses contain the result data and metadata for completed operations.
    """

    request_id: str = Field(..., description="Echo of the request ID that triggered this response")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Response creation timestamp",
    )
    success: bool = Field(default=True, description="Whether the operation succeeded")
    error_message: str | None = Field(
        default=None,
        description="Error message if success is False",
    )

    class Config:
        """Pydantic config for base response."""

        json_schema_extra = {
            "example": {
                "request_id": "req-12345",
                "timestamp": "2026-04-11T12:00:00Z",
                "success": True,
                "error_message": None,
            }
        }
