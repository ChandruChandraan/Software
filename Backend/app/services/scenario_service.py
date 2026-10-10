"""Scenario Command Service for dispatching and tracking Unreal Engine scenario changes."""

import asyncio
from dataclasses import dataclass
import json
import logging
import socket
import time
from typing import Callable, Dict, List, Optional, Tuple
import uuid

from app.config import Settings
from app.schemas import (
    ScenarioAckPacket,
    ScenarioChangeResponse,
    ScenarioInfo,
    ScenarioStatusEvent,
)
from app.services.scenario_registry import ScenarioRegistry, ScenarioDefinition
from app.websocket.manager import ConnectionManager

logger = logging.getLogger("backend.scenarios.service")


class ScenarioServiceError(Exception):
    """Base exception for scenario service operations."""
    pass


class UnknownScenarioError(ScenarioServiceError):
    """Raised when an unknown scenario ID is requested."""
    pass


class UnavailableScenarioError(ScenarioServiceError):
    """Raised when a requested scenario's assets are unavailable."""
    pass


class DuplicateCommandError(ScenarioServiceError):
    """Raised when a duplicate scenario change is requested while one is active."""
    pass


class CommandSendError(ScenarioServiceError):
    """Raised when UDP transmission to Unreal fails."""
    pass


@dataclass
class ScenarioRequestRecord:
    """Internal tracking record for a scenario change command."""

    request_id: str
    scenario_id: str
    unreal_name: str
    status: str  # "pending", "sent", "accepted", "completed", "failed", "timeout"
    created_at: float
    sent_at: Optional[float] = None
    completed_at: Optional[float] = None
    message: Optional[str] = None
    error: Optional[str] = None

    def to_event(self) -> ScenarioStatusEvent:
        """Converts record to a WebSocket status event."""
        return ScenarioStatusEvent(
            request_id=self.request_id,
            scenario_id=self.scenario_id,
            scenario=self.unreal_name,
            status=self.status,
            message=self.message,
            error=self.error,
            timestamp=time.time(),
        )

    def to_response(self) -> ScenarioChangeResponse:
        """Converts record to an API response."""
        return ScenarioChangeResponse(
            request_id=self.request_id,
            scenario_id=self.scenario_id,
            scenario=self.unreal_name,
            status=self.status,
            message=self.message or f"Scenario status: {self.status}",
            timestamp=time.time(),
        )


class ScenarioService:
    """
    Coordinates scenario transitions between the REST API, Unreal Engine UDP socket,
    and connected WebSocket interfaces.
    """

    def __init__(
        self,
        settings: Settings,
        registry: ScenarioRegistry,
        ws_manager: ConnectionManager,
        unreal_service: Optional[object] = None,
        udp_sender: Optional[Callable[[bytes, Tuple[str, int]], None]] = None,
    ):
        self.settings = settings
        self.registry = registry
        self.ws_manager = ws_manager
        self.unreal_service = unreal_service
        self._udp_sender = udp_sender or self._default_udp_sender

        self._requests: Dict[str, ScenarioRequestRecord] = {}
        self._active_request_id: Optional[str] = None
        self._timeout_tasks: Dict[str, asyncio.Task] = {}
        self._lock = asyncio.Lock()

    def set_udp_sender(self, sender: Callable[[bytes, Tuple[str, int]], None]):
        """Configures the UDP transmission function (typically the bound 47001 transport)."""
        self._udp_sender = sender

    @staticmethod
    def _default_udp_sender(data: bytes, address: Tuple[str, int]):
        """Transmits raw datagram via an ephemeral UDP socket."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.sendto(data, address)
        finally:
            sock.close()

    def list_scenarios(self) -> List[ScenarioInfo]:
        """Returns the list of available scenarios from the registry."""
        return self.registry.list_scenarios()

    def get_request_status(self, request_id: str) -> Optional[ScenarioRequestRecord]:
        """Retrieves tracking record for a specific request ID."""
        return self._requests.get(request_id)

    def get_latest_status(self) -> Optional[ScenarioRequestRecord]:
        """Retrieves the latest or currently active request record."""
        if self._active_request_id and self._active_request_id in self._requests:
            return self._requests[self._active_request_id]
        if self._requests:
            # Return most recently created
            return max(self._requests.values(), key=lambda r: r.created_at)
        return None

    async def _broadcast_status(self, record: ScenarioRequestRecord):
        """Dispatches status updates to connected WebSocket clients."""
        try:
            event = record.to_event()
            # Topic: scenario_change_status
            await self.ws_manager.broadcast("scenario_change_status", event.model_dump())
        except Exception as e:
            logger.warning(f"Error broadcasting scenario status event: {e}")

    async def change_scenario(self, scenario_id: str) -> ScenarioChangeResponse:
        """
        Validates scenario ID, transmits change command to Unreal via UDP,
        and manages request lifecycle.
        """
        clean_id = scenario_id.lower().strip()
        defn: Optional[ScenarioDefinition] = self.registry.get(clean_id)
        if not defn:
            valid_ids = self.registry.get_valid_ids()
            raise UnknownScenarioError(
                f"Unknown scenario ID '{scenario_id}'. Valid scenarios: {', '.join(valid_ids)}"
            )

        if not self.registry.check_availability(defn):
            raise UnavailableScenarioError(
                f"Scenario '{scenario_id}' ({defn.display_name}) is registered but its level assets are not available."
            )

        async with self._lock:
            now = time.time()
            # Duplicate / debounce check
            if self._active_request_id and self._active_request_id in self._requests:
                active_record = self._requests[self._active_request_id]
                if active_record.status in ("pending", "sent"):
                    time_in_flight = now - active_record.created_at
                    if active_record.scenario_id == clean_id:
                        raise DuplicateCommandError(
                            f"Scenario change to '{clean_id}' is already in progress "
                            f"(Request ID: {active_record.request_id}, in-flight: {time_in_flight:.1f}s)."
                        )
                    elif time_in_flight < self.settings.SCENARIO_DEBOUNCE_SECONDS:
                        raise DuplicateCommandError(
                            f"Another scenario change command ({active_record.scenario_id}) is currently "
                            f"in progress. Please wait before issuing another change."
                        )

            # Generate unique correlation ID
            request_id = f"scenario-{uuid.uuid4().hex[:8]}"

            # Check Unreal Engine process state (non-fatal, logging only)
            if self.unreal_service:
                try:
                    is_running, pid = self.unreal_service.is_running()
                    if not is_running:
                        logger.warning(
                            f"Unreal Engine process is not detected as running. "
                            f"Dispatching scenario change UDP datagram anyway to destination."
                        )
                except Exception as e:
                    logger.debug(f"Error checking Unreal process status: {e}")

            # Build UDP message
            payload = {
                "v": 1,
                "type": "change_scenario",
                "scenario": defn.unreal_name,
                "request_id": request_id,
            }
            raw_bytes = json.dumps(payload).encode("utf-8")
            dest_host = self.settings.UNREAL_UDP_HOST
            dest_port = self.settings.UNREAL_UDP_PORT

            record = ScenarioRequestRecord(
                request_id=request_id,
                scenario_id=clean_id,
                unreal_name=defn.unreal_name,
                status="pending",
                created_at=now,
                message="Preparing to send scenario command",
            )
            self._requests[request_id] = record
            self._active_request_id = request_id

            # Transmit datagram locally
            try:
                self._udp_sender(raw_bytes, (dest_host, dest_port))
                record.status = "sent"
                record.sent_at = time.time()
                record.message = (
                    f"Scenario change command transmitted to Unreal at {dest_host}:{dest_port}; "
                    "awaiting confirmation"
                )
                logger.info(
                    f"Transmitted scenario command: request_id='{request_id}', "
                    f"scenario='{defn.unreal_name}' -> {dest_host}:{dest_port}"
                )
            except Exception as e:
                record.status = "failed"
                record.error = str(e)
                record.message = f"UDP send failure: {e}"
                logger.error(
                    f"Failed to transmit UDP scenario command to {dest_host}:{dest_port}: {e}"
                )
                await self._broadcast_status(record)
                raise CommandSendError(f"Could not send UDP command to Unreal: {e}")

            # Broadcast sent status
            await self._broadcast_status(record)

            # Schedule timeout handler
            loop = asyncio.get_running_loop()
            timeout_task = loop.create_task(
                self._watch_timeout(request_id, self.settings.SCENARIO_COMMAND_TIMEOUT)
            )
            self._timeout_tasks[request_id] = timeout_task

            return record.to_response()

    async def _watch_timeout(self, request_id: str, timeout_seconds: float):
        """Waits for Unreal acknowledgement; transitions status to 'timeout' if unconfirmed."""
        try:
            await asyncio.sleep(timeout_seconds)
            async with self._lock:
                record = self._requests.get(request_id)
                if record and record.status == "sent":
                    record.status = "timeout"
                    record.error = f"No confirmation received from Unreal within {timeout_seconds:.1f}s"
                    record.message = record.error
                    logger.warning(
                        f"Scenario change request '{request_id}' timed out waiting for Unreal ack "
                        f"after {timeout_seconds}s"
                    )
                    await self._broadcast_status(record)
        except asyncio.CancelledError:
            pass
        finally:
            self._timeout_tasks.pop(request_id, None)

    def handle_ack(self, packet: ScenarioAckPacket):
        """
        Correlates inbound acknowledgement packet from Unreal with active request.
        Called by the UDP listener on Port 47001.
        """
        request_id = packet.request_id
        record = self._requests.get(request_id)
        if not record:
            logger.warning(
                f"Received scenario ack for unknown or expired request_id: '{request_id}'"
            )
            return

        # Cancel timeout watcher task
        task = self._timeout_tasks.pop(request_id, None)
        if task and not task.done():
            task.cancel()

        # Update record state
        if packet.status in ("completed", "loaded", "ignored"):
            record.status = "completed"
            record.message = packet.message or f"Scenario '{record.unreal_name}' active in Unreal"
        elif packet.status == "rejected":
            record.status = "failed"
            record.error = packet.message or packet.error or "Rejected by Unreal Engine"
            record.message = record.error
        else:
            record.status = packet.status
            record.message = packet.message or f"Unreal reported status: {packet.status}"

        record.completed_at = time.time()
        record.error = packet.error or (packet.message if packet.status in ("failed", "rejected") else None)

        logger.info(
            f"Correlated scenario ack: request_id='{request_id}', "
            f"status='{packet.status}', error={record.error}"
        )

        # Disseminate update via WebSocket
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._broadcast_status(record))
        except RuntimeError:
            pass

    async def shutdown(self):
        """Cancels all active timeout tasks on service shutdown."""
        for task in self._timeout_tasks.values():
            if not task.done():
                task.cancel()
        self._timeout_tasks.clear()
