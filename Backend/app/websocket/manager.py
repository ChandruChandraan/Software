"""WebSocket connection manager for real-time dashboard events."""

import asyncio
import json
import logging
import time
from typing import Any, Dict, Set
from fastapi import WebSocket

logger = logging.getLogger("backend.websocket")


class ConnectionManager:
    """Tracks active client WebSockets and broadcasts live events."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        """Accept and register an active WebSocket connection."""
        await websocket.accept()
        async with self._lock:
            self.active_connections.add(websocket)
        logger.debug(f"Client connected. Active clients: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket):
        """Unregister a disconnected WebSocket."""
        async with self._lock:
            self.active_connections.discard(websocket)
        logger.debug(f"Client disconnected. Active clients: {len(self.active_connections)}")

    async def broadcast(self, topic: str, data: Any):
        """
        Broadcast message to all connected clients using the standard envelope:
        {"topic": topic, "data": data, "timestamp": time.time()}
        """
        if not self.active_connections:
            return

        payload = {
            "topic": topic,
            "data": data,
            "timestamp": time.time(),
        }
        message_text = json.dumps(payload)

        # Snapshot active connections safely
        async with self._lock:
            clients = list(self.active_connections)

        dead_clients = []
        for client in clients:
            try:
                await client.send_text(message_text)
            except Exception as e:
                logger.debug(f"Failed to send to client ({e}), marking dead")
                dead_clients.append(client)

        if dead_clients:
            async with self._lock:
                for dead in dead_clients:
                    self.active_connections.discard(dead)


# Global connection manager instance
ws_manager = ConnectionManager()
