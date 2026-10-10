"""Asyncio UDP Datagram Listener for Tracker telemetry."""

import asyncio
import json
import logging
import socket
import time
from typing import Any, Dict, Optional, Tuple
from pydantic import ValidationError

from app.schemas import ShotPacket, GunStatusPacket, UDPListenerStatus, ScenarioAckPacket
from app.services.tracker_state import TrackerState
from app.websocket.manager import ConnectionManager

logger = logging.getLogger("backend.udp")


class TrackerUDPProtocol(asyncio.DatagramProtocol):
    """Asyncio UDP datagram protocol handling inbound Tracker and Unreal JSON packets."""

    def __init__(
        self,
        state: TrackerState,
        ws_manager: ConnectionManager,
        scenario_service: Optional[Any] = None,
    ):
        self.state = state
        self.ws_manager = ws_manager
        self.scenario_service = scenario_service
        self.transport: Optional[asyncio.DatagramTransport] = None

    def connection_made(self, transport: asyncio.DatagramTransport):
        self.transport = transport
        logger.info("UDP Datagram transport initialized.")

    def _safe_broadcast(self, topic: str, data: Any):
        """Schedules WebSocket broadcast if an event loop is running."""
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.ws_manager.broadcast(topic, data))
        except RuntimeError:
            pass

    def datagram_received(self, data: bytes, addr: Tuple[str, int]):
        raw_text = ""
        try:
            raw_text = data.decode("utf-8").strip()
            if not raw_text:
                return

            payload_dict = json.loads(raw_text)
            if not isinstance(payload_dict, dict):
                raise ValueError("JSON root must be an object")

            # Check protocol version
            version = payload_dict.get("v")
            if version != 1:
                raise ValueError(f"Unsupported packet protocol version: {version}")

            msg_type = payload_dict.get("type")

            if msg_type == "shot":
                packet = ShotPacket(**payload_dict)
                self.state.handle_shot(packet)
                # Broadcast shot event
                self._safe_broadcast("shot", packet.model_dump())
                self._safe_broadcast("tracker_event", packet.model_dump())

            elif msg_type == "gun_status":
                packet = GunStatusPacket(**payload_dict)
                self.state.handle_gun_status(packet)
                # Broadcast gun status event
                self._safe_broadcast("gun_status", packet.model_dump())
                self._safe_broadcast("tracker_event", packet.model_dump())

            elif msg_type in ("scenario_ack", "scenario_status"):
                ack_packet = ScenarioAckPacket(**payload_dict)
                self.state.packets_received += 1
                self.state.last_packet_time = time.time()
                if self.scenario_service:
                    self.scenario_service.handle_ack(ack_packet)

            else:
                raise ValueError(f"Unknown message type: '{msg_type}'")

        except (UnicodeDecodeError, json.JSONDecodeError, ValidationError, ValueError) as err:
            err_msg = str(err)
            self.state.record_invalid_packet(raw_text or str(data[:60]), err_msg)
            self._safe_broadcast(
                "udp_error",
                {"error": err_msg, "raw": (raw_text[:100] if raw_text else str(data[:40]))},
            )
        except Exception as e:
            logger.exception(f"Unexpected error processing datagram from {addr}: {e}")
            self.state.record_invalid_packet(raw_text or "binary", str(e))

    def error_received(self, exc: Exception):
        logger.error(f"UDP datagram transport error: {exc}")
        self._safe_broadcast("udp_error", {"error": str(exc)})

    def connection_lost(self, exc: Optional[Exception]):
        if exc:
            logger.warning(f"UDP datagram transport closed with error: {exc}")
        else:
            logger.info("UDP datagram transport closed cleanly.")


class TrackerUDPListener:
    """Manages the lifecycle of the asyncio UDP server endpoint."""

    def __init__(
        self,
        host: str,
        port: int,
        state: TrackerState,
        ws_manager: ConnectionManager,
        scenario_service: Optional[Any] = None,
    ):
        self.host = host
        self.port = port
        self.state = state
        self.ws_manager = ws_manager
        self.scenario_service = scenario_service
        self.transport: Optional[asyncio.DatagramTransport] = None
        self.protocol: Optional[TrackerUDPProtocol] = None
        self.is_listening: bool = False
        self._last_error: Optional[str] = None

    async def start(self) -> bool:
        """Start listening on the configured host and port."""
        if self.is_listening:
            return True

        loop = asyncio.get_running_loop()
        try:
            # Bind endpoint
            transport, protocol = await loop.create_datagram_endpoint(
                lambda: TrackerUDPProtocol(self.state, self.ws_manager, self.scenario_service),
                local_addr=(self.host, self.port),
            )
            self.transport = transport
            self.protocol = protocol
            self.is_listening = True
            self._last_error = None
            logger.info(f"Tracker UDP listener started on {self.host}:{self.port}")
            return True
        except Exception as e:
            self._last_error = str(e)
            self.is_listening = False
            logger.error(f"Failed to start UDP listener on {self.host}:{self.port}: {e}")
            return False

    def send_to(self, data: bytes, address: Tuple[str, int]) -> bool:
        """Sends a UDP datagram from the bound 47001 transport so Unreal routes return ACKs back here."""
        if self.transport and not self.transport.is_closing():
            try:
                self.transport.sendto(data, address)
                return True
            except Exception as e:
                logger.error(f"Failed to send UDP datagram via listener transport: {e}")
        return False

    async def stop(self):
        """Cleanly close the UDP listener transport."""
        if self.transport:
            try:
                self.transport.close()
            except Exception as e:
                logger.debug(f"Error closing UDP transport: {e}")
            self.transport = None
            self.protocol = None
        self.is_listening = False
        logger.info("Tracker UDP listener stopped.")

    def get_status(self) -> UDPListenerStatus:
        """Returns structured status information for health checks and dashboard."""
        status_str = "listening" if self.is_listening else ("error" if self._last_error else "stopped")
        return UDPListenerStatus(
            status=status_str,
            host=self.host,
            port=self.port,
            packets_received=self.state.packets_received,
            invalid_packets=self.state.invalid_packets,
            last_packet_time=self.state.last_packet_time,
        )
