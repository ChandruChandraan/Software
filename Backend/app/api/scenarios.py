"""REST API endpoints for simulation scenario queries and Unreal level transitions."""

import logging
from typing import List
from fastapi import APIRouter, HTTPException, Request, status

from app.schemas import (
    ScenarioChangeRequest,
    ScenarioChangeResponse,
    ScenarioInfo,
)
from app.services.scenario_service import (
    CommandSendError,
    DuplicateCommandError,
    UnavailableScenarioError,
    UnknownScenarioError,
)

logger = logging.getLogger("backend.api.scenarios")

router = APIRouter(prefix="/api/scenarios", tags=["Scenarios"])


@router.get("", response_model=List[ScenarioInfo])
async def list_scenarios(request: Request):
    """
    Returns the list of valid selectable simulator scenarios with availability status.
    Excludes internal server filesystem paths to protect backend integrity.
    """
    scenario_service = getattr(request.app.state, "scenario_service", None)
    if not scenario_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Scenario service is not initialized.",
        )
    return scenario_service.list_scenarios()


@router.post("/change", response_model=ScenarioChangeResponse)
async def change_scenario(request: Request, payload: ScenarioChangeRequest):
    """
    Initiates a scenario change request in Unreal Engine 5.8:
    1. Validates the scenario ID against the registered scenario catalog.
    2. Verifies availability and command destination configuration.
    3. Prevents duplicate in-flight requests.
    4. Constructs and transmits the UDP datagram to Unreal Engine on Port 47000.
    5. Returns an immediate acknowledgement with request ID and status 'sent'.
    6. Broadcasts real-time lifecycle events over WebSocket /ws/backend.
    """
    scenario_service = getattr(request.app.state, "scenario_service", None)
    if not scenario_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Scenario service is not initialized.",
        )

    try:
        response = await scenario_service.change_scenario(payload.scenario_id)
        return response
    except UnknownScenarioError as err:
        logger.warning(f"Scenario change rejected: {err}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        )
    except UnavailableScenarioError as err:
        logger.warning(f"Scenario unavailable: {err}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        )
    except DuplicateCommandError as err:
        logger.info(f"Duplicate scenario request throttled: {err}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(err),
        )
    except CommandSendError as err:
        logger.error(f"UDP transmission failure for scenario change: {err}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to transmit scenario command over UDP to Unreal: {err}",
        )
    except Exception as err:
        logger.exception(f"Unexpected error handling scenario change: {err}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error processing scenario change: {err}",
        )


@router.get("/status/{request_id}", response_model=ScenarioChangeResponse)
async def get_scenario_request_status(request: Request, request_id: str):
    """
    Polls the current status of a specific scenario change request ID.
    Enables HTTP clients to track transition outcomes (sent, accepted, completed, timeout, failed).
    """
    scenario_service = getattr(request.app.state, "scenario_service", None)
    if not scenario_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Scenario service is not initialized.",
        )

    record = scenario_service.get_request_status(request_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scenario request ID '{request_id}' not found.",
        )
    return record.to_response()


@router.get("/active", response_model=ScenarioChangeResponse)
async def get_active_scenario_status(request: Request):
    """Returns the most recent or currently active scenario change status."""
    scenario_service = getattr(request.app.state, "scenario_service", None)
    if not scenario_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Scenario service is not initialized.",
        )

    record = scenario_service.get_latest_status()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No scenario change commands have been issued in this session.",
        )
    return record.to_response()
