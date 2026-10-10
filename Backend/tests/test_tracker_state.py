"""Tests for TrackerState gun tracking, shot events, and telemetry timeout transitions."""

import time
import pytest
from app.schemas import GunStatusPacket, ShotPacket
from app.services.tracker_state import TrackerState


def test_initial_state_disconnected():
    """State should report disconnected when no telemetry has ever arrived."""
    state = TrackerState(telemetry_timeout=1.0)
    assert state.get_telemetry_freshness() == "disconnected"
    assert state.last_valid_event_time is None
    assert len(state.get_all_guns()) == 0


def test_gun_status_update():
    """Verify gun status updates gun properties and connection flag."""
    state = TrackerState(telemetry_timeout=1.0)

    # Gun 1 connected
    pkt1 = GunStatusPacket(v=1, type="gun_status", gun=1, lane=1, port="COM3", connected=True, shot_count=2)
    state.handle_gun_status(pkt1)

    guns = state.get_all_guns()
    assert len(guns) == 1
    assert guns[0].gun_id == 1
    assert guns[0].port == "COM3"
    assert guns[0].connected is True
    assert guns[0].shot_count == 2

    # Gun 1 disconnected
    pkt2 = GunStatusPacket(v=1, type="gun_status", gun=1, lane=1, port="COM3", connected=False, shot_count=2)
    state.handle_gun_status(pkt2)

    # Physical only returns connected devices; physical_only=False retains complete record
    assert len(state.get_all_guns(physical_only=True)) == 0
    assert state.get_all_guns(physical_only=False)[0].connected is False


def test_shot_recording():
    """Verify shot events record coordinates, increment total shots, and update round."""
    state = TrackerState(telemetry_timeout=1.0)

    shot = ShotPacket(
        v=1,
        type="shot",
        gun=3,
        lane=3,
        x=500.0,
        y=600.0,
        round=1,
    )
    state.handle_shot(shot)

    assert state.total_shots == 1
    guns = state.get_all_guns(physical_only=False)
    assert len(guns) == 1
    assert guns[0].gun_id == 3
    assert guns[0].last_shot_coords == {"x": 500.0, "y": 600.0}
    assert guns[0].shot_count == 1
    assert len(state.recent_events) == 1


def test_telemetry_timeout_transitions():
    """Verify transition from connected -> stale -> disconnected over time."""
    timeout_s = 0.2
    state = TrackerState(telemetry_timeout=timeout_s)

    # Initially disconnected
    assert state.get_telemetry_freshness() == "disconnected"

    # Receive packet -> immediately connected
    pkt = GunStatusPacket(v=1, type="gun_status", gun=1, lane=1, connected=True)
    state.handle_gun_status(pkt)
    assert state.get_telemetry_freshness() == "connected"

    # Wait past timeout -> should become stale
    time.sleep(0.25)
    assert state.get_telemetry_freshness() == "stale"

    # Wait past timeout * 3 -> should become disconnected
    time.sleep(0.45)
    assert state.get_telemetry_freshness() == "disconnected"


def test_clear_recent_events():
    """Verify clearing recent event queue."""
    state = TrackerState(telemetry_timeout=1.0)
    shot = ShotPacket(v=1, type="shot", gun=1, lane=1, x=100.0, y=200.0, round=1)
    state.handle_shot(shot)
    assert len(state.recent_events) == 1

    state.clear_recent_events()
    assert len(state.recent_events) == 0
