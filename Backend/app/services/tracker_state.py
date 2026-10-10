"""In-memory state management for gun telemetry and system health."""

from collections import deque
import logging
import time
from typing import Dict, List, Optional, Any, Literal
from app.schemas import GunStateModel, ShotPacket, GunStatusPacket, TrackerTelemetryStatus

logger = logging.getLogger("backend.state")


class TrackerState:
    """Maintains runtime state of guns, received UDP packets, and freshness."""

    def __init__(self, telemetry_timeout: float = 5.0):
        self.telemetry_timeout = telemetry_timeout
        self.backend_start_time = time.time()

        # Packet counters
        self.packets_received: int = 0
        self.invalid_packets: int = 0
        self.last_packet_time: Optional[float] = None
        self.last_valid_event_time: Optional[float] = None
        self.last_valid_payload: Optional[Dict[str, Any]] = None

        # Gun states keyed by gun_id
        self._guns: Dict[int, GunStateModel] = {}
        self.total_shots: int = 0

        # Ring buffers for live UI feed & diagnostics
        self.recent_events: deque = deque(maxlen=100)
        self.recent_errors: deque = deque(maxlen=50)

    def get_telemetry_freshness(self) -> Literal["connected", "stale", "disconnected"]:
        """
        Determines current telemetry freshness based on last received valid event:
        - disconnected: No valid telemetry ever received, or elapsed > timeout * 3
        - stale: Valid telemetry received, but elapsed > timeout and <= timeout * 3
        - connected: Valid telemetry received within timeout
        """
        if self.last_valid_event_time is None:
            return "disconnected"

        elapsed = time.time() - self.last_valid_event_time
        if elapsed <= self.telemetry_timeout:
            return "connected"
        elif elapsed <= (self.telemetry_timeout * 3):
            return "stale"
        else:
            return "disconnected"

    def get_telemetry_status(self) -> TrackerTelemetryStatus:
        """Returns structured telemetry freshness metadata."""
        freshness = self.get_telemetry_freshness()
        now = time.time()
        elapsed = (now - self.last_valid_event_time) if self.last_valid_event_time else None
        physical_guns = self.get_all_guns(physical_only=True)
        connected_count = sum(1 for g in physical_guns if g.connected)

        return TrackerTelemetryStatus(
            freshness=freshness,
            last_valid_event_time=self.last_valid_event_time,
            seconds_since_last_event=round(elapsed, 2) if elapsed is not None else None,
            connected_guns=connected_count,
            total_guns=len(physical_guns),
            total_shots=self.total_shots,
        )

    def handle_gun_status(self, packet: GunStatusPacket) -> GunStateModel:
        """Updates gun state from validated gun_status UDP packet."""
        now = time.time()
        self.packets_received += 1
        self.last_packet_time = now
        self.last_valid_event_time = now
        self.last_valid_payload = packet.model_dump()

        gun = self._guns.get(packet.gun)
        if gun is None:
            gun = GunStateModel(
                gun_id=packet.gun,
                lane=packet.lane,
                port=packet.port,
                connected=packet.connected,
                shot_count=packet.shot_count,
                last_seen=now,
            )
            self._guns[packet.gun] = gun
        else:
            gun.lane = packet.lane
            if packet.port is not None:
                gun.port = packet.port
            gun.connected = packet.connected
            gun.shot_count = max(gun.shot_count, packet.shot_count)
            gun.last_seen = now

        # Gun state updated from packet; keepalives do not flood recent_events
        return gun

    def handle_shot(self, packet: ShotPacket) -> GunStateModel:
        """Updates gun state and registers shot event from validated shot UDP packet."""
        now = time.time()
        self.packets_received += 1
        self.last_packet_time = now
        self.last_valid_event_time = now
        self.last_valid_payload = packet.model_dump()
        self.total_shots += 1

        gun = self._guns.get(packet.gun)
        if gun is None:
            gun = GunStateModel(
                gun_id=packet.gun,
                lane=packet.lane,
                connected=True,
                shot_count=packet.round,
                last_seen=now,
                last_shot_time=now,
                last_shot_coords={"x": packet.x, "y": packet.y},
            )
            self._guns[packet.gun] = gun
        else:
            gun.lane = packet.lane
            gun.connected = True
            gun.shot_count = max(gun.shot_count, packet.round)
            gun.last_seen = now
            gun.last_shot_time = now
            gun.last_shot_coords = {"x": packet.x, "y": packet.y}

        # Add to recent events
        event_entry = {
            "type": "shot",
            "gun": packet.gun,
            "lane": packet.lane,
            "x": packet.x,
            "y": packet.y,
            "round": packet.round,
            "cross_lane": packet.cross_lane,
            "display_width": packet.display_width,
            "display_height": packet.display_height,
            "timestamp": now,
        }
        self.recent_events.appendleft(event_entry)
        return gun

    def record_invalid_packet(self, raw_str: str, error_detail: str):
        """Records a malformed or invalid UDP packet."""
        now = time.time()
        self.packets_received += 1
        self.invalid_packets += 1
        self.last_packet_time = now

        error_entry = {
            "timestamp": now,
            "error": error_detail,
            "raw_snippet": (raw_str[:120] + "...") if len(raw_str) > 120 else raw_str,
        }
        self.recent_errors.appendleft(error_entry)
        logger.warning(f"Invalid UDP packet received: {error_detail} (raw: {error_entry['raw_snippet']})")

    def get_all_guns(self, physical_only: bool = True) -> List[GunStateModel]:
        """Returns sorted list of guns by Gun ID, filtering strictly to physical hardware by default."""
        guns = [self._guns[gid] for gid in sorted(self._guns.keys())]
        if physical_only:
            return [g for g in guns if g.connected and g.port and not g.port.startswith("SIM-")]
        return guns

    def clear_recent_events(self):
        """Clears recent events feed."""
        self.recent_events.clear()

    def get_uptime_seconds(self) -> float:
        """Returns backend server uptime in seconds."""
        return round(time.time() - self.backend_start_time, 2)
