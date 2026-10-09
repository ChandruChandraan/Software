from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_console_websocket():
    with client.websocket_connect("/ws/console") as websocket:
        websocket.send_text("ping")
        data = websocket.receive_json()
        assert data["type"] == "ack"
        assert data["received"] == "ping"


def test_sim_websocket():
    with client.websocket_connect("/ws/sim") as websocket:
        websocket.send_text("sim_status")
        data = websocket.receive_json()
        assert data["type"] == "ack"
        assert data["received"] == "sim_status"
