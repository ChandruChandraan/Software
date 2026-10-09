"""Tracker telemetry REST endpoints."""

from typing import Dict, Any
from fastapi import APIRouter
from ..services.tracker_listener import tracker_listener

router = APIRouter(tags=["Tracker"])


@router.get("/status")
def get_tracker_status() -> Dict[str, Any]:
    """Retrieve operational status and telemetry counters of UDP tracker listener."""
    return tracker_listener.get_status()


@router.get("/guns")
def get_tracker_guns() -> Dict[str, Any]:
    """Retrieve runtime state and telemetry for all active and registered simulator guns."""
    return {
        "guns": tracker_listener.get_gun_states()
    }
