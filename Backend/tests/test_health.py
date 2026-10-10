"""Tests for health and diagnostic REST endpoints."""


def test_get_health(client):
    """Verify basic health endpoint returns status and uptime."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "uptime_seconds" in data
    assert "version" in data
    assert "timestamp" in data


def test_get_health_details(client):
    """Verify detailed health diagnostics include listener, process, and telemetry."""
    response = client.get("/api/health/details")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "backend_host" in data
    assert "backend_port" in data

    # UDP listener status
    listener = data["udp_listener"]
    assert "status" in listener
    assert "packets_received" in listener
    assert "invalid_packets" in listener

    # Process manager status
    process = data["tracker_process"]
    assert "running" in process
    assert "mode" in process
    assert "target_path" in process

    # Telemetry status
    telemetry = data["tracker_telemetry"]
    assert "freshness" in telemetry
    assert telemetry["freshness"] in ["connected", "stale", "disconnected"]
