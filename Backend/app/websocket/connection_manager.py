"""WebSocket connection manager for Console and Sim clients."""

import logging
from typing import List, Set, Any
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages active WebSocket connections for instructor console and unreal simulation."""

    def __init__(self) -> None:
        self.console_connections: Set[WebSocket] = set()
        self.sim_connections: Set[WebSocket] = set()

    async def connect_console(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.console_connections.add(websocket)
        logger.info(f"Console client connected. Total console clients: {len(self.console_connections)}")

    def disconnect_console(self, websocket: WebSocket) -> None:
        self.console_connections.discard(websocket)
        logger.info(f"Console client disconnected. Remaining console clients: {len(self.console_connections)}")

    async def broadcast_console(self, message: Any) -> None:
        disconnected = []
        for ws in self.console_connections:
            try:
                if isinstance(message, str):
                    await ws.send_text(message)
                else:
                    await ws.send_json(message)
            except Exception as e:
                logger.warning(f"Error sending message to console client: {e}")
                disconnected.append(ws)

        for ws in disconnected:
            self.disconnect_console(ws)

    async def connect_sim(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.sim_connections.add(websocket)
        logger.info(f"Simulation client connected. Total sim clients: {len(self.sim_connections)}")

    def disconnect_sim(self, websocket: WebSocket) -> None:
        self.sim_connections.discard(websocket)
        logger.info(f"Simulation client disconnected. Remaining sim clients: {len(self.sim_connections)}")

    async def broadcast_sim(self, message: Any) -> None:
        disconnected = []
        for ws in self.sim_connections:
            try:
                if isinstance(message, str):
                    await ws.send_text(message)
                else:
                    await ws.send_json(message)
            except Exception as e:
                logger.warning(f"Error sending message to sim client: {e}")
                disconnected.append(ws)

        for ws in disconnected:
            self.disconnect_sim(ws)


manager = ConnectionManager()
