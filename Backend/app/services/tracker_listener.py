"""Async UDP listener service on Port 47001 to ingest Tracker events."""

import asyncio
import json
import logging
import time
from typing import Optional, Dict, Any, List

from ..config import get_config
from ..websocket.connection_manager import manager

logger = logging.getLogger("backend.udp_listener")


class TrackerDatagramProtocol(asyncio.DatagramProtocol):
    """Protocol handler for incoming UDP telemetry packets from Tracker."""

    def __init__(self, listener: "TrackerUdpListener") -> None:
        self.listener = listener

    def connection_made(self, transport: asyncio.DatagramTransport) -> None:
        self.listener.transport = transport
        self.listener.is_active = True
        logger.info(f"Tracker UDP listener socket bound on {self.listener.host}:{self.listener.port}")

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        payload = self.listener.validate_and_process_datagram(data, addr)
        if payload is not None:
            # Broadcast to connected console clients
            try:
                asyncio.create_task(
                    manager.broadcast_console({
                        "topic": "tracker_event",
                        "payload": payload,
                    })
                )
            except Exception as e:
                logger.debug(f"Failed to schedule WebSocket broadcast: {e}")

    def error_received(self, exc: Exception) -> None:
        logger.error(f"Tracker UDP listener error: {exc}")

    def connection_lost(self, exc: Optional[Exception]) -> None:
        self.listener.is_active = False
        logger.info("Tracker UDP listener transport closed.")


class TrackerUdpListener:
    """Service lifecycle wrapper for Tracker UDP ingestion on Port 47001."""

    def __init__(self, host: Optional[str] = None, port: Optional[int] = None) -> None:
        self._custom_host = host
        self._custom_port = port
        self.host: str = host or "127.0.0.1"
        self.port: int = port or 47001
        self.transport: Optional[asyncio.DatagramTransport] = None
        self.is_active: bool = False

        # Vitality counters & telemetry state
        self.total_packets: int = 0
        self.accepted_packets: int = 0
        self.rejected_packets: int = 0
        self.last_packet_time: Optional[float] = None
        self.last_event: Optional[Dict[str, Any]] = None

        # Authoritative per-gun runtime states: gun_id -> dict
        self.guns: Dict[int, Dict[str, Any]] = {}
        self.stale_threshold: float = 5.0

    @property
    def packet_count(self) -> int:
        """Backward-compatibility alias for total_packets."""
        return self.total_packets

    @packet_count.setter
    def packet_count(self, val: int) -> None:
        self.total_packets = val

    def reset(self) -> None:
        """Reset internal telemetry counters and gun states (used in tests)."""
        self.total_packets = 0
        self.accepted_packets = 0
        self.rejected_packets = 0
        self.last_packet_time = None
        self.last_event = None
        self.guns.clear()

    async def start(self) -> None:
        """Start listening on the configured UDP port."""
        cfg = get_config()
        self.host = self._custom_host if self._custom_host is not None else cfg.udp_listen_host
        self.port = self._custom_port if self._custom_port is not None else cfg.udp_listen_port
        self.stale_threshold = getattr(cfg, "tracker_stale_threshold_seconds", 5.0)

        loop = asyncio.get_running_loop()
        try:
            await loop.create_datagram_endpoint(
                lambda: TrackerDatagramProtocol(self),
                local_addr=(self.host, self.port),
            )
            logger.info(f"Started Tracker UDP listener on {self.host}:{self.port}")
        except Exception as e:
            logger.warning(f"Could not bind Tracker UDP listener on {self.host}:{self.port}: {e}")

    def stop(self) -> None:
        """Stop UDP listener."""
        if self.transport:
            self.transport.close()
            self.transport = None
            self.is_active = False
            logger.info("Tracker UDP listener stopped.")

    def validate_and_process_datagram(self, data: bytes, addr: tuple[str, int]) -> Optional[Dict[str, Any]]:
        """
        Validates incoming JSON datagrams and updates authoritative gun telemetry state.
        Supports 'shot' and 'gun_status' message types.
        Rejects malformed, incomplete, or unsupported packets.
        """
        self.total_packets += 1

        try:
            text = data.decode("utf-8")
            payload = json.loads(text)
        except Exception as e:
            self.rejected_packets += 1
            logger.debug(f"Rejected unparseable UDP datagram from {addr}: {e}")
            return None

        if not isinstance(payload, dict):
            self.rejected_packets += 1
            logger.debug(f"Rejected non-dictionary datagram from {addr}")
            return None

        msg_type = payload.get("type")
        if not msg_type or not isinstance(msg_type, str):
            self.rejected_packets += 1
            logger.debug(f"Rejected datagram with missing or invalid 'type' from {addr}")
            return None

        now = time.time()

        if msg_type == "shot":
            # Validation for shot event
            gun_id = payload.get("gun")
            lane = payload.get("lane")
            x = payload.get("x")
            y = payload.get("y")

            if (
                gun_id is None or not isinstance(gun_id, int) or gun_id < 1 or
                lane is None or not isinstance(lane, int) or lane < 1 or
                x is None or not isinstance(x, (int, float)) or x < 0 or
                y is None or not isinstance(y, (int, float)) or y < 0
            ):
                self.rejected_packets += 1
                logger.debug(f"Rejected invalid shot payload: {payload}")
                return None

            round_num = int(payload.get("round", 1))

            # Update authoritative gun telemetry
            if gun_id not in self.guns:
                self.guns[gun_id] = {
                    "gun_id": gun_id,
                    "lane": lane,
                    "port": None,
                    "connected": True,
                    "shot_count": round_num,
                    "last_update": now,
                }
            else:
                gun_ref = self.guns[gun_id]
                gun_ref["lane"] = lane
                gun_ref["connected"] = True
                gun_ref["shot_count"] = max(gun_ref.get("shot_count", 0), round_num)
                gun_ref["last_update"] = now

        elif msg_type == "gun_status":
            # Validation for gun_status event
            gun_id = payload.get("gun")
            lane = payload.get("lane")
            connected = payload.get("connected")

            if (
                gun_id is None or not isinstance(gun_id, int) or gun_id < 1 or
                lane is None or not isinstance(lane, int) or lane < 1 or
                connected is None or not isinstance(connected, bool)
            ):
                self.rejected_packets += 1
                logger.debug(f"Rejected invalid gun_status payload: {payload}")
                return None

            shot_count = payload.get("shot_count")
            if shot_count is not None and (not isinstance(shot_count, int) or shot_count < 0):
                self.rejected_packets += 1
                return None
            shot_count = int(shot_count or 0)

            port = payload.get("port")
            if port is not None and not isinstance(port, str):
                self.rejected_packets += 1
                return None

            # Update authoritative gun telemetry
            if gun_id not in self.guns:
                self.guns[gun_id] = {
                    "gun_id": gun_id,
                    "lane": lane,
                    "port": port,
                    "connected": connected,
                    "shot_count": shot_count,
                    "last_update": now,
                }
            else:
                gun_ref = self.guns[gun_id]
                gun_ref["lane"] = lane
                gun_ref["port"] = port
                gun_ref["connected"] = connected
                if shot_count > 0:
                    gun_ref["shot_count"] = max(gun_ref.get("shot_count", 0), shot_count)
                gun_ref["last_update"] = now

        else:
            # Unsupported message type
            self.rejected_packets += 1
            logger.debug(f"Rejected unsupported packet type '{msg_type}' from {addr}")
            return None

        # Accepted packet
        self.accepted_packets += 1
        self.last_packet_time = now
        self.last_event = payload
        return payload

    def get_status(self) -> Dict[str, Any]:
        """Return listener telemetry and vitality metrics."""
        now = time.time()
        stale_threshold = self.stale_threshold

        active_guns = 0
        for g in self.guns.values():
            if g.get("connected") and (now - g.get("last_update", 0) <= stale_threshold):
                active_guns += 1

        is_online = (
            self.is_active
            and self.last_packet_time is not None
            and (now - self.last_packet_time <= stale_threshold)
        )
        status_str = "online" if is_online else ("waiting" if self.is_active else "offline")

        total_shots = sum(g.get("shot_count", 0) for g in self.guns.values())

        return {
            "status": status_str,
            "is_active": self.is_active,
            "host": self.host,
            "port": self.port,
            "total_packets": self.total_packets,
            "accepted_packets": self.accepted_packets,
            "rejected_packets": self.rejected_packets,
            "last_packet_time": self.last_packet_time,
            "has_received_event": self.last_event is not None,
            "connected_guns": active_guns,
            "total_guns": len(self.guns),
            "total_shots": total_shots,
            "unreal_forwarding": False,
            "stale_threshold_seconds": stale_threshold,
        }

    def get_gun_states(self) -> List[Dict[str, Any]]:
        """Return list of authoritative gun telemetry states with dynamic stale detection."""
        now = time.time()
        stale_threshold = self.stale_threshold
        result = []

        for gid in sorted(self.guns.keys()):
            g = self.guns[gid]
            last_up = g.get("last_update", 0.0)
            is_stale = g.get("connected", False) and ((now - last_up) > stale_threshold)
            result.append({
                "gun_id": g.get("gun_id", gid),
                "lane": g.get("lane", gid),
                "port": g.get("port"),
                "connected": g.get("connected", False) and not is_stale,
                "raw_connected": g.get("connected", False),
                "shot_count": g.get("shot_count", 0),
                "last_update": last_up,
                "is_stale": is_stale,
            })

        return result


tracker_listener = TrackerUdpListener()
