from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_system_health():
    response = client.get("/system/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "backend"
    assert data["database"] == "ok"


def test_system_licence():
    response = client.get("/system/licence")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "active"


def test_system_settings():
    response = client.get("/system/settings")
    assert response.status_code == 200
    data = response.json()
    assert data["udp_listen_port"] == 47001


def test_system_health_details():
    response = client.get("/system/health/details")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "ok"
    assert "udp_listener" in data
    assert data["udp_listener"]["port"] == 47001
