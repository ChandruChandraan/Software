"""Tests for WebSocket real-time event broadcasting."""

import asyncio
import json
from starlette.testclient import TestClient
from app.websocket.manager import ConnectionManager


def test_websocket_connect_and_ping(app_with_state):
    """Verify WebSocket connection, welcome message, and ping-pong over Starlette TestClient."""
    client = TestClient(app_with_state)
    with client.websocket_connect("/ws/backend") as websocket:
        # Initial connection packet
        data = websocket.receive_json()
        assert data["topic"] == "connection_established"
        assert "backend_uptime" in data["data"]

        # Ping-pong
        websocket.send_text("ping")
        resp = websocket.receive_text()
        assert resp == "pong"


def test_websocket_broadcast_delivery():
    """Verify ConnectionManager formats envelope and broadcasts to active connections."""
    async def _run():
        mgr = ConnectionManager()

        class MockWebSocket:
            def __init__(self):
                self.messages = []
                self.accepted = False

            async def accept(self):
                self.accepted = True

            async def send_text(self, text: str):
                self.messages.append(text)

        mock_ws = MockWebSocket()
        await mgr.connect(mock_ws)
        assert len(mgr.active_connections) == 1

        # Broadcast shot event
        await mgr.broadcast("shot", {"gun": 2, "lane": 2, "round": 4})
        assert len(mock_ws.messages) == 1

        payload = json.loads(mock_ws.messages[0])
        assert payload["topic"] == "shot"
        assert payload["data"]["gun"] == 2
        assert payload["data"]["round"] == 4
        assert "timestamp" in payload

        # Clean disconnect
        await mgr.disconnect(mock_ws)
        assert len(mgr.active_connections) == 0

    asyncio.run(_run())
