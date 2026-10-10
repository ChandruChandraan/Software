"""Tests for UDP datagram protocol parsing and error handling."""

import asyncio
import json
from app.services.tracker_listener import TrackerUDPProtocol


def test_udp_protocol_valid_shot(tracker_state, ws_manager):
    """Test receiving valid shot JSON packet."""
    protocol = TrackerUDPProtocol(state=tracker_state, ws_manager=ws_manager)

    payload = {
        "v": 1,
        "type": "shot",
        "gun": 1,
        "lane": 1,
        "x": 960.0,
        "y": 540.0,
        "display_width": 1920,
        "display_height": 1080,
        "round": 1,
        "cross_lane": False,
        "time_us": 1728471234567890,
    }
    raw_data = json.dumps(payload).encode("utf-8")

    protocol.datagram_received(raw_data, ("127.0.0.1", 50000))

    assert tracker_state.packets_received == 1
    assert tracker_state.invalid_packets == 0
    assert tracker_state.total_shots == 1
    assert tracker_state.last_valid_event_time is not None

    guns = tracker_state.get_all_guns(physical_only=False)
    assert len(guns) == 1
    assert guns[0].gun_id == 1
    assert guns[0].shot_count == 1
    assert guns[0].last_shot_coords == {"x": 960.0, "y": 540.0}


def test_udp_protocol_valid_gun_status(tracker_state, ws_manager):
    """Test receiving valid gun status JSON packet."""
    protocol = TrackerUDPProtocol(state=tracker_state, ws_manager=ws_manager)

    payload = {
        "v": 1,
        "type": "gun_status",
        "gun": 2,
        "lane": 2,
        "port": "COM5",
        "connected": True,
        "shot_count": 7,
        "time_us": 1728471234567890,
    }
    raw_data = json.dumps(payload).encode("utf-8")

    protocol.datagram_received(raw_data, ("127.0.0.1", 50000))

    assert tracker_state.packets_received == 1
    assert tracker_state.invalid_packets == 0

    guns = tracker_state.get_all_guns()
    assert len(guns) == 1
    assert guns[0].gun_id == 2
    assert guns[0].port == "COM5"
    assert guns[0].connected is True
    assert guns[0].shot_count == 7


def test_udp_protocol_invalid_version(tracker_state, ws_manager):
    """Test packet with unsupported version field is rejected."""
    protocol = TrackerUDPProtocol(state=tracker_state, ws_manager=ws_manager)

    payload = {
        "v": 2,  # Invalid version
        "type": "shot",
        "gun": 1,
        "lane": 1,
        "x": 100,
        "y": 200,
    }
    protocol.datagram_received(json.dumps(payload).encode("utf-8"), ("127.0.0.1", 50000))

    assert tracker_state.packets_received == 1
    assert tracker_state.invalid_packets == 1
    assert len(tracker_state.recent_errors) == 1
    assert "Unsupported packet protocol version" in tracker_state.recent_errors[0]["error"]


def test_udp_protocol_malformed_json(tracker_state, ws_manager):
    """Test non-JSON corrupt packet is counted as invalid."""
    protocol = TrackerUDPProtocol(state=tracker_state, ws_manager=ws_manager)

    protocol.datagram_received(b"INVALID_CORRUPT_BYTES{{{{", ("127.0.0.1", 50000))

    assert tracker_state.packets_received == 1
    assert tracker_state.invalid_packets == 1


def test_udp_protocol_missing_required_fields(tracker_state, ws_manager):
    """Test JSON missing mandatory fields fails Pydantic schema validation."""
    protocol = TrackerUDPProtocol(state=tracker_state, ws_manager=ws_manager)

    payload = {"v": 1, "type": "shot"}  # Missing gun, lane, x, y
    protocol.datagram_received(json.dumps(payload).encode("utf-8"), ("127.0.0.1", 50000))

    assert tracker_state.packets_received == 1
    assert tracker_state.invalid_packets == 1


def test_udp_listener_start_stop(udp_listener):
    """Test starting and stopping UDP listener endpoint."""
    async def _run():
        started = await udp_listener.start()
        assert started is True
        assert udp_listener.is_listening is True

        status = udp_listener.get_status()
        assert status.status == "listening"
        assert status.port == udp_listener.port

        await udp_listener.stop()
        assert udp_listener.is_listening is False
        assert udp_listener.get_status().status == "stopped"

    asyncio.run(_run())
