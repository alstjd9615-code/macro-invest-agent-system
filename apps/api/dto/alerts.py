"""Alert DTOs for the analyst-facing read API (Chapter 6)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class AlertEventDTO(BaseModel, extra="forbid"):
    """Read model for a single alert event.

    Attributes:
        alert_id: Unique identifier.
        triggered_at: UTC datetime when the alert fired.
        trigger_type: Category of the triggering condition.
        severity: Analyst-facing importance level (info/warning/critical).
        source_regime: Regime label before transition (if applicable).
        target_regime: Regime label after transition (if applicable).
        indicator_type: Macro indicator involved (threshold_breach alerts).
        context_snapshot_id: Supporting snapshot ID for explanation pre-fetch.
        country: Country code (ISO 3166-1 alpha-2), if applicable.
        rule_id: ID of the rule that triggered this event.
        rule_name: Human-readable rule name.
        message: Short analyst-facing description of the trigger.
        acknowledgement_state: Current analyst acknowledgement state.
        acknowledged_at: UTC datetime of acknowledgement, if any.
        snoozed_until: UTC datetime until which the alert is snoozed, if any.
        metadata: Supplemental key/value pairs attached at rule evaluation.
    """

    alert_id: str
    triggered_at: datetime
    trigger_type: str
    severity: str
    source_regime: str | None = None
    target_regime: str | None = None
    indicator_type: str | None = None
    context_snapshot_id: str | None = None
    country: str | None = None
    rule_id: str
    rule_name: str
    message: str
    acknowledgement_state: str = Field(default="active")
    acknowledged_at: datetime | None = None
    snoozed_until: datetime | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class AlertsRecentResponse(BaseModel, extra="forbid"):
    """Response model for ``GET /api/alerts/recent``."""

    alerts: list[AlertEventDTO] = Field(default_factory=list)
    total: int = Field(description="Number of alerts in this response")
    limit_applied: int = Field(description="The limit that was applied")


class AlertAcknowledgeRequest(BaseModel, extra="forbid"):
    """Request body for acknowledging an alert (``PATCH /api/alerts/{id}/acknowledge``)."""


class AlertSnoozeRequest(BaseModel, extra="forbid"):
    """Request body for snoozing an alert (``PATCH /api/alerts/{id}/snooze``)."""

    snoozed_until: datetime = Field(
        description="UTC datetime until which the alert should be snoozed"
    )
