"""Comprehensive test suite for FiringSim scenario management and Unreal UDP command integration."""

import asyncio
import json
from pathlib import Path
import time
from typing import List, Tuple
from unittest.mock import MagicMock, patch

import pytest
from starlette.testclient import TestClient

from app.config import Settings
from app.main import app
from app.schemas import ScenarioAckPacket
from app.services.scenario_registry import ScenarioDefinition, ScenarioRegistry
from app.services.scenario_service import (
    CommandSendError,
    DuplicateCommandError,
    ScenarioService,
    UnavailableScenarioError,
    UnknownScenarioError,
)
from app.services.tracker_listener import TrackerUDPProtocol
from app.services.tracker_state import TrackerState
from app.websocket.manager import ConnectionManager


@pytest.fixture
def test_settings():
    """Isolated settings fixture."""
    return Settings(
        UNREAL_UDP_HOST="127.0.0.1",
        UNREAL_UDP_PORT=47000,
        SCENARIO_COMMAND_TIMEOUT=0.2,  # Fast timeout for test speed
        SCENARIO_DEBOUNCE_SECONDS=1.0,
        LOCAL_ONLY_MANAGEMENT=False,
        TRACKER_AUTOSTART=False,
        UNREAL_AUTOSTART=False,
    )


@pytest.fixture
def mock_ws_manager():
    """Mock WebSocket ConnectionManager capturing broadcasts."""
    mgr = ConnectionManager()
    mgr.broadcast = MagicMock(return_value=asyncio.sleep(0))
    return mgr


@pytest.fixture
def captured_udp():
    """Captures sent UDP datagrams."""
    sent: List[Tuple[bytes, Tuple[str, int]]] = []

    def sender(data: bytes, addr: Tuple[str, int]):
        sent.append((data, addr))

    sender.sent = sent
    return sender


@pytest.fixture
def scenario_service(test_settings, mock_ws_manager, captured_udp, tmp_path):
    """Instantiates ScenarioService with mocked UDP socket and registry."""
    # Create temporary maps to test availability checks
    maps_dir = tmp_path / "Maps"
    maps_dir.mkdir(parents=True)
    (maps_dir / "IndoorRange.umap").write_text("map data")
    (maps_dir / "Range_Basic.umap").write_text("map data")

    registry = ScenarioRegistry(content_dir=tmp_path)
    # Register an intentionally unavailable scenario
    registry.register(
        ScenarioDefinition(
            scenario_id="desert_storm_01",
            display_name="Desert Storm Range",
            unreal_name="DesertStorm_01",
            relative_map_path="Maps/DesertStorm_NonExistent.umap",
            description="Desert environment",
            default_available=False,
        )
    )

    unreal_service = MagicMock()
    unreal_service.is_running.return_value = (True, 1234)

    service = ScenarioService(
        settings=test_settings,
        registry=registry,
        ws_manager=mock_ws_manager,
        unreal_service=unreal_service,
        udp_sender=captured_udp,
    )
    return service


@pytest.fixture
def test_client(scenario_service, mock_ws_manager, test_settings):
    """TestClient wired with the mock scenario_service in app.state."""
    app.state.settings = test_settings
    app.state.scenario_registry = scenario_service.registry
    app.state.scenario_service = scenario_service
    app.state.ws_manager = mock_ws_manager
    with TestClient(app) as client:
        yield client


# ==============================================================================
# 1. Scenario List Retrieval Tests
# ==============================================================================


def test_get_scenarios_list(test_client):
    """Verifies GET /api/scenarios returns valid scenarios and no internal paths."""
    response = test_client.get("/api/scenarios")
    assert response.status_code == 200
    scenarios = response.json()
    assert isinstance(scenarios, list)
    assert len(scenarios) >= 4

    ids = [s["scenario_id"] for s in scenarios]
    assert "indoor_range" in ids
    assert "training_range_01" in ids
    assert "range_basic" in ids
    assert "tactical_shooting_range" in ids

    # Ensure no internal server paths or .umap extensions are exposed
    for s in scenarios:
        assert "scenario_id" in s
        assert "display_name" in s
        assert "available" in s
        assert "unreal_name" not in s
        assert "relative_map_path" not in s
        assert ".umap" not in s.get("display_name", "")


def test_scenario_availability_verification(tmp_path):
    """Verifies ScenarioRegistry accurately checks actual .umap existence."""
    content_dir = tmp_path / "Content"
    maps_dir = content_dir / "Maps"
    maps_dir.mkdir(parents=True)
    (maps_dir / "Installed.umap").write_text("ok")

    registry = ScenarioRegistry(content_dir=content_dir)
    installed_def = ScenarioDefinition(
        scenario_id="installed_map",
        display_name="Installed Map",
        unreal_name="Installed",
        relative_map_path="Maps/Installed.umap",
    )
    missing_def = ScenarioDefinition(
        scenario_id="missing_map",
        display_name="Missing Map",
        unreal_name="Missing",
        relative_map_path="Maps/Missing.umap",
    )
    registry.register(installed_def)
    registry.register(missing_def)

    assert registry.check_availability(installed_def) is True
    assert registry.check_availability(missing_def) is False


# ==============================================================================
# 2. Valid and Unknown Scenario ID Tests
# ==============================================================================


def test_post_scenario_change_valid(test_client, captured_udp):
    """Verifies valid scenario change transmits UDP command to Unreal and returns 'sent'."""
    payload = {"scenario_id": "indoor_range"}
    response = test_client.post("/api/scenarios/change", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["scenario_id"] == "indoor_range"
    assert data["scenario"] == "IndoorRange"
    assert data["status"] == "sent"
    assert "request_id" in data
    assert data["request_id"].startswith("scenario-")
    assert "awaiting confirmation" in data["message"].lower()

    # Verify UDP packet was delivered to 127.0.0.1:47000
    assert len(captured_udp.sent) == 1
    raw_bytes, addr = captured_udp.sent[0]
    assert addr == ("127.0.0.1", 47000)

    udp_packet = json.loads(raw_bytes.decode("utf-8"))
    assert udp_packet["v"] == 1
    assert udp_packet["type"] == "change_scenario"
    assert udp_packet["scenario"] == "IndoorRange"
    assert udp_packet["request_id"] == data["request_id"]


def test_post_scenario_change_training_range_01(test_client, captured_udp):
    """Verifies training_range_01 maps to Training_Range_01 in Unreal UDP packet."""
    response = test_client.post("/api/scenarios/change", json={"scenario_id": "training_range_01"})
    assert response.status_code == 200
    data = response.json()
    assert data["scenario_id"] == "training_range_01"
    assert data["scenario"] == "Training_Range_01"
    assert data["status"] == "sent"

    raw_bytes, addr = captured_udp.sent[0]
    packet = json.loads(raw_bytes.decode("utf-8"))
    assert packet["scenario"] == "Training_Range_01"


def test_post_scenario_change_unknown_id(test_client):
    """Verifies unknown scenario ID returns 400 Bad Request."""
    response = test_client.post(
        "/api/scenarios/change", json={"scenario_id": "nonexistent_scenario_123"}
    )
    assert response.status_code == 400
    assert "Unknown scenario ID" in response.json()["detail"]


def test_post_scenario_change_unavailable_scenario(test_client):
    """Verifies request for registered but unavailable scenario returns 400 Bad Request."""
    response = test_client.post(
        "/api/scenarios/change", json={"scenario_id": "desert_storm_01"}
    )
    assert response.status_code == 400
    assert "not available" in response.json()["detail"]


# ==============================================================================
# 3. Missing or Malformed Request Data Tests
# ==============================================================================


@pytest.mark.parametrize(
    "malformed_payload",
    [
        {},
        {"scenario_id": ""},
        {"scenario_id": None},
        {"wrong_field": "indoor_range"},
    ],
)
def test_post_scenario_change_malformed(test_client, malformed_payload):
    """Verifies malformed or empty payloads are rejected with 422 Unprocessable Entity."""
    response = test_client.post("/api/scenarios/change", json=malformed_payload)
    assert response.status_code == 422


# ==============================================================================
# 4. UDP Send Failures
# ==============================================================================


def test_udp_send_failure(test_client, scenario_service, mock_ws_manager):
    """Verifies socket OSError results in 'failed' status, 502 status code, and WS event."""

    def failing_sender(data: bytes, addr: Tuple[str, int]):
        raise OSError("Host network unreachable (Simulated UDP failure)")

    scenario_service._udp_sender = failing_sender

    response = test_client.post("/api/scenarios/change", json={"scenario_id": "indoor_range"})
    assert response.status_code == 502
    assert "Failed to transmit scenario command over UDP" in response.json()["detail"]

    # Verify latest record in service is marked 'failed'
    latest = scenario_service.get_latest_status()
    assert latest is not None
    assert latest.status == "failed"
    assert "Simulated UDP failure" in (latest.error or "")

    # Verify WebSocket broadcast was called with status 'failed'
    mock_ws_manager.broadcast.assert_called()
    call_args = mock_ws_manager.broadcast.call_args[0]
    assert call_args[0] == "scenario_change_status"
    assert call_args[1]["status"] == "failed"


# ==============================================================================
# 5. Duplicate Submission Prevention
# ==============================================================================


def test_duplicate_submission_throttle(test_client):
    """Verifies duplicate submission for same scenario while in flight raises 409 Conflict."""
    resp1 = test_client.post("/api/scenarios/change", json={"scenario_id": "indoor_range"})
    assert resp1.status_code == 200
    assert resp1.json()["status"] == "sent"

    # Immediately submit the same scenario while state is 'sent'
    resp2 = test_client.post("/api/scenarios/change", json={"scenario_id": "indoor_range"})
    assert resp2.status_code == 409
    assert "already in progress" in resp2.json()["detail"]


# ==============================================================================
# 6. Request ID Correlation & Inbound Acknowledgement
# ==============================================================================


def test_unreal_acknowledgement_correlation(test_client, scenario_service, mock_ws_manager):
    """Verifies Unreal acknowledgement updates status to 'completed' and correlates request ID."""
    resp = test_client.post("/api/scenarios/change", json={"scenario_id": "indoor_range"})
    assert resp.status_code == 200
    req_id = resp.json()["request_id"]

    # Simulate Unreal returning completion ack packet on port 47001
    ack = ScenarioAckPacket(
        v=1,
        type="scenario_ack",
        request_id=req_id,
        status="completed",
        scenario="IndoorRange",
    )
    scenario_service.handle_ack(ack)

    # Poll status endpoint
    poll_resp = test_client.get(f"/api/scenarios/status/{req_id}")
    assert poll_resp.status_code == 200
    poll_data = poll_resp.json()
    assert poll_data["status"] == "completed"
    assert poll_data["request_id"] == req_id


def test_tracker_udp_listener_handles_scenario_ack(scenario_service):
    """Verifies TrackerUDPProtocol processes inbound scenario_ack JSON datagram."""
    tracker_state = TrackerState()
    mock_ws = ConnectionManager()
    protocol = TrackerUDPProtocol(
        state=tracker_state,
        ws_manager=mock_ws,
        scenario_service=scenario_service,
    )

    # First submit request to have an active request ID
    asyncio.run(scenario_service.change_scenario("indoor_range"))
    req_id = scenario_service.get_latest_status().request_id

    # Inbound UDP packet
    ack_json = json.dumps(
        {
            "v": 1,
            "type": "scenario_ack",
            "request_id": req_id,
            "status": "accepted",
            "scenario": "IndoorRange",
        }
    ).encode("utf-8")

    protocol.datagram_received(ack_json, ("127.0.0.1", 47000))

    record = scenario_service.get_request_status(req_id)
    assert record is not None
    assert record.status == "accepted"


# ==============================================================================
# 7. Missing Acknowledgement and Timeout Handling
# ==============================================================================


def test_command_timeout(scenario_service, mock_ws_manager):
    """Verifies request transitions to 'timeout' when no ack is received before timeout."""
    async def _test():
        scenario_service.settings.SCENARIO_COMMAND_TIMEOUT = 0.05
        response = await scenario_service.change_scenario("indoor_range")
        req_id = response.request_id

        # Allow timeout task to expire
        await asyncio.sleep(0.1)

        record = scenario_service.get_request_status(req_id)
        assert record is not None
        assert record.status == "timeout"
        assert "No confirmation received" in (record.error or "")

        # Verify WebSocket broadcast called with timeout
        mock_ws_manager.broadcast.assert_called()
        timeout_calls = [
            call for call in mock_ws_manager.broadcast.call_args_list
            if call[0][1].get("status") == "timeout"
        ]
        assert len(timeout_calls) >= 1
        assert timeout_calls[0][0][1]["request_id"] == req_id

    asyncio.run(_test())


# ==============================================================================
# 8. Unreal Engine Process State Resilience
# ==============================================================================


def test_backend_resilient_when_unreal_stopped(test_client, scenario_service, captured_udp):
    """Verifies Backend remains responsive and sends command even if Unreal is not running."""
    # Simulate Unreal service reporting stopped
    mock_unreal = MagicMock()
    mock_unreal.is_running.return_value = (False, None)
    scenario_service.unreal_service = mock_unreal

    response = test_client.post("/api/scenarios/change", json={"scenario_id": "indoor_range"})
    assert response.status_code == 200
    assert response.json()["status"] == "sent"
    # Command was still delivered to socket
    assert len(captured_udp.sent) == 1
    # Unreal service stop/start was NOT invoked
    mock_unreal.start.assert_not_called()
    mock_unreal.stop.assert_not_called()


# ==============================================================================
# 9. Scenario JSON Configuration & Updates
# ==============================================================================


def test_scenario_registry_loads_from_json(tmp_path):
    """Verifies ScenarioRegistry loads and updates scenarios from a custom JSON file."""
    json_file = tmp_path / "custom_scenarios.json"
    custom_data = [
        {
            "scenario_id": "custom_cqb",
            "display_name": "Custom CQB House",
            "unreal_name": "CQB_House",
            "relative_map_path": "Maps/IndoorRange.umap",
            "description": "Custom Close Quarters Battle training",
            "default_available": True,
        },
        {
            "scenario_id": "indoor_range",
            "display_name": "Updated Indoor Range",
            "description": "Overridden description from JSON",
        },
    ]
    json_file.write_text(json.dumps(custom_data), encoding="utf-8")

    registry = ScenarioRegistry(content_dir=tmp_path, json_path=json_file)

    # Verifies newly added scenario exists
    custom = registry.get("custom_cqb")
    assert custom is not None
    assert custom.display_name == "Custom CQB House"
    assert custom.unreal_name == "CQB_House"

    # Verifies override of default scenario
    indoor = registry.get("indoor_range")
    assert indoor is not None
    assert indoor.display_name == "Updated Indoor Range"
    assert indoor.description == "Overridden description from JSON"


def test_scenario_registry_save_to_json(tmp_path):
    """Verifies ScenarioRegistry can save registered scenarios to JSON."""
    registry = ScenarioRegistry()
    export_file = tmp_path / "exported_scenarios.json"
    success = registry.save_to_json(export_file)
    assert success is True
    assert export_file.exists()

    data = json.loads(export_file.read_text(encoding="utf-8"))
    assert isinstance(data, list)
    ids = [d["scenario_id"] for d in data]
    assert "indoor_range" in ids
    assert "training_range_01" in ids

