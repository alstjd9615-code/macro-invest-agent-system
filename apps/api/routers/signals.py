"""Signal read routes for the analyst-facing product API.

Routes
------
``GET /api/signals/latest``
    Run the signal engine against the current macro snapshot and return the
    evaluated signal summaries with trust metadata.

Design constraints
------------------
* All routes are **read-only**.
* Deterministic signal engine outputs are the authoritative source.
* Trust metadata is always included in the response.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query

from apps.api.dependencies import get_macro_service, get_signal_service
from apps.api.dto.builders import build_trust_from_signal_result, signal_output_to_dto
from apps.api.dto.signals import SignalsLatestResponse
from domain.signals.registry import default_registry
from services.interfaces import MacroServiceInterface, SignalServiceInterface

router = APIRouter(prefix="/api/signals", tags=["signals"])


@router.get(
    "/latest",
    response_model=SignalsLatestResponse,
    summary="Get latest signal evaluations",
    description=(
        "Run the signal engine against the current macro snapshot and return all "
        "evaluated signal summaries. The response includes per-signal type, strength, "
        "score, trend, rationale, rule-level results, and trust metadata. "
        "Use the 'signal_ids' query parameter to filter to specific signals."
    ),
)
async def get_latest_signals(
    country: str = Query(default="US", description="ISO 3166-1 alpha-2 country code"),
    signal_ids: list[str] | None = Query(
        default=None,
        description=(
            "Optional filter: comma-separated list of signal IDs to evaluate. "
            "When omitted, all registered signals are evaluated."
        ),
    ),
    macro_service: MacroServiceInterface = Depends(get_macro_service),
    signal_service: SignalServiceInterface = Depends(get_signal_service),
) -> SignalsLatestResponse:
    """Evaluate and return the latest signals for *country*.

    Returns HTTP 200 with :class:`~apps.api.dto.signals.SignalsLatestResponse`
    on success.  Returns HTTP 502 if the macro service cannot be reached.
    Returns HTTP 422 if the requested signal IDs are not found in the registry.
    """
    # Resolve signal definitions from the registry
    registry = default_registry
    if signal_ids:
        definitions = []
        missing = []
        for sid in signal_ids:
            try:
                defn = registry.get(sid)
                definitions.append(defn)
            except KeyError:
                missing.append(sid)
        if missing:
            raise HTTPException(
                status_code=422,
                detail=f"Unknown signal IDs: {missing}. "
                f"Available: {registry.list_ids()}",
            )
    else:
        definitions = [registry.get(sid) for sid in registry.list_ids()]

    if not definitions:
        # Registry is empty — return empty response rather than erroring
        from apps.api.dto.trust import DataAvailability, FreshnessStatus, TrustMetadata

        return SignalsLatestResponse(
            country=country,
            run_id="",
            signals=[],
            signals_count=0,
            buy_count=0,
            sell_count=0,
            hold_count=0,
            strongest_signal_id=None,
            trust=TrustMetadata(
                freshness_status=FreshnessStatus.UNKNOWN,
                availability=DataAvailability.UNAVAILABLE,
            ),
        )

    # Fetch snapshot
    try:
        snapshot = await macro_service.get_snapshot(country=country)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=502,
            detail=f"Macro data service unavailable: {exc}",
        ) from exc

    # Run engine
    try:
        result = await signal_service.run_engine(
            signal_definitions=definitions,
            snapshot=snapshot,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=502,
            detail=f"Signal engine error: {exc}",
        ) from exc

    signals_dtos = [signal_output_to_dto(s) for s in result.signals]
    trust = build_trust_from_signal_result(result)

    strongest = result.strongest_signal()
    strongest_id = strongest.signal_id if strongest else None

    buy_count = sum(1 for s in result.signals if str(s.signal_type) == "buy")
    sell_count = sum(1 for s in result.signals if str(s.signal_type) == "sell")
    hold_count = sum(1 for s in result.signals if str(s.signal_type) == "hold")

    return SignalsLatestResponse(
        country=country,
        run_id=result.run_id,
        signals=signals_dtos,
        signals_count=len(signals_dtos),
        buy_count=buy_count,
        sell_count=sell_count,
        hold_count=hold_count,
        strongest_signal_id=strongest_id,
        trust=trust,
    )


_ = uuid  # suppress unused import
