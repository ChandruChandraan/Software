"""
Headless Tracker Daemon for Firing Simulator.
Runs without GUI/display windows, managing USB serial microcontrollers,
independent multi-gun state, and dual-destination UDP transmission:
- Unreal Engine (Port 47000): Real-time simulator shots
- Python Backend (Port 47001): Telemetry and live Console monitoring
"""

import argparse
import logging
import signal
import sys
import time
from typing import Optional, List

from PySide6.QtCore import QCoreApplication, QObject, QTimer

from core import config
from core.gun_state import MultiGunManager
from devices.serial_manager import SerialDeviceManager
from network.udp_client import UDPClient
from ui.display_manager import DisplayManager, DisplayInfo
from ui.unreal_process import UnrealManager

logger = logging.getLogger("tracker.daemon")


class HeadlessTrackerDaemon(QObject):
    """
    Headless Tracker Core Engine.
    Manages non-blocking USB serial discovery, multi-gun trigger synchronization,
    and concurrent UDP telemetry streaming.
    """

    def __init__(
        self,
        backend_host: str = config.BACKEND_IP,
        backend_port: int = config.BACKEND_PORT,
        send_to_backend: bool = getattr(config, "SEND_TO_BACKEND", True),
        unreal_host: str = config.UNREAL_IP,
        unreal_port: int = config.UNREAL_PORT,
        simulated_guns: int = getattr(config, "SIMULATED_GUN_COUNT", 4),
        auto_launch_unreal: bool = getattr(config, "AUTO_LAUNCH_UNREAL", False),
        unreal_exe_path: str = getattr(config, "UNREAL_EXE_PATH", ""),
        display_width: int = 1920,
        display_height: int = 1080,
    ):
        super().__init__()
        self.backend_host = backend_host
        self.backend_port = backend_port
        self.send_to_backend = send_to_backend
        self.unreal_host = unreal_host
        self.unreal_port = unreal_port
        self.simulated_gun_count = simulated_guns
        self.auto_launch_unreal = auto_launch_unreal
        self.unreal_exe_path = unreal_exe_path
        self._is_running = False

        logger.info("Initializing Headless Tracker Engine...")
        logger.info(f"Unreal Destination : {self.unreal_host}:{self.unreal_port} (UDP)")
        logger.info(f"Backend Destination: {self.backend_host}:{self.backend_port} (UDP)")

        # 1. Coordinate display geometry from Windows display manager (non-GUI)
        displays = DisplayManager.get_displays()
        selected_disp: Optional[DisplayInfo] = None
        if displays:
            secondary = next((d for d in displays if not d.is_primary), None)
            selected_disp = secondary or displays[0]
            w = selected_disp.width
            h = selected_disp.height
            d_idx = selected_disp.index
            logger.info(f"Detected Display {d_idx}: {w}x{h} @ ({selected_disp.x}, {selected_disp.y})")
        else:
            w = display_width
            h = display_height
            d_idx = 1
            logger.info(f"Default display bounds: {w}x{h}")

        # 2. Multi-Gun State Coordinator
        self.gun_manager = MultiGunManager(default_gun_count=max(4, self.simulated_gun_count))
        self.gun_manager.set_display_geometry(d_idx, 0, 0, w, h)

        # 3. Hardware Serial Manager
        self.serial_manager = SerialDeviceManager(self.gun_manager)

        # 4. Low-latency UDP Client
        self.udp_client = UDPClient(
            ip=self.unreal_host,
            port=self.unreal_port,
            backend_ip=self.backend_host,
            backend_port=self.backend_port,
            send_to_backend=self.send_to_backend,
        )

        # 5. Unreal Engine Process Manager
        self.unreal_manager = UnrealManager(self.unreal_exe_path) if self.unreal_exe_path else None
        self.selected_display = selected_disp

        # 6. Wire internal signals
        self._setup_connections()

        # 7. Background Heartbeat & Keepalive Watchdog
        self._watchdog_timer = QTimer(self)
        self._watchdog_timer.setInterval(2000)
        self._watchdog_timer.timeout.connect(self._on_watchdog_tick)

    def _setup_connections(self):
        # Gun state -> UDP
        self.gun_manager.gun_shot_fired.connect(self._on_gun_shot_fired)
        self.gun_manager.gun_status_changed.connect(self._on_gun_status_changed)

        # Serial logging
        self.serial_manager.log_event.connect(lambda msg: logger.info(f"[Serial] {msg}"))
        self.serial_manager.device_connected.connect(
            lambda port, gid: logger.info(f"[Device Connected] Gun {gid} on {port}")
        )
        self.serial_manager.device_disconnected.connect(
            lambda port, gid: logger.warning(f"[Device Disconnected] Gun {gid} on {port}")
        )

    def start(self):
        """Starts background workers, UDP socket, serial threads, and optional simulation."""
        if self._is_running:
            return
        self._is_running = True

        # Connect UDP client
        self.udp_client.connect_client()

        # Start serial scanning
        self.serial_manager.start()

        # Enable simulated controllers if requested
        if self.simulated_gun_count > 0:
            logger.info(f"Enabling {self.simulated_gun_count} simulated gun controllers...")
            self.serial_manager.enable_simulation(self.simulated_gun_count)

        # Launch Unreal process if requested
        if self.auto_launch_unreal and self.unreal_manager and self.selected_display:
            logger.info("Auto-launching Unreal Engine...")
            self.unreal_manager.launch(self.selected_display)

        # Start periodic keepalive watchdog
        self._watchdog_timer.start()

        # Send initial status for all registered guns to Backend
        self._broadcast_all_gun_statuses()
        logger.info("Headless Tracker Engine started successfully.")

    def stop(self):
        """Gracefully releases serial connections, timers, UDP sockets, and resources."""
        if not self._is_running:
            return
        self._is_running = False
        logger.info("Stopping Headless Tracker Engine...")

        self._watchdog_timer.stop()

        try:
            self.serial_manager.disable_simulation()
            self.serial_manager.stop()
        except Exception as e:
            logger.error(f"Error stopping Serial Manager: {e}")

        try:
            self.udp_client.disconnect_client()
        except Exception as e:
            logger.error(f"Error disconnecting UDP client: {e}")

        logger.info("Headless Tracker shutdown complete.")

    def _on_gun_shot_fired(self, gun_id: int, payload: dict):
        """Dispatches verified shot trigger to Unreal Engine and Backend."""
        logger.info(
            f"[SHOT] Gun {gun_id} Lane {payload.get('lane')} -> "
            f"Coords ({payload.get('x')}, {payload.get('y')}) Round {payload.get('round')}"
        )
        self.udp_client.send_shot(
            gun=payload["gun"],
            lane=payload["lane"],
            x=payload["x"],
            y=payload["y"],
            cross_lane=payload.get("cross_lane", False),
            round_num=payload.get("round", 1),
            display_width=payload.get("display_width", 1920),
            display_height=payload.get("display_height", 1080),
        )

    def _on_gun_status_changed(self, gun_id: int, payload: dict):
        """Dispatches gun status update to Backend."""
        status_str = "CONNECTED" if payload.get("connected") else "DISCONNECTED"
        port_str = f" on {payload.get('port')}" if payload.get("port") else ""
        logger.info(f"[STATUS] Gun {gun_id} {status_str}{port_str} (Shots: {payload.get('shot_count', 0)})")

        self.udp_client.send_gun_status(
            gun=payload["gun"],
            lane=payload["lane"],
            port=payload.get("port"),
            connected=payload.get("connected", False),
            shot_count=payload.get("shot_count", 0),
            time_us=payload.get("time_us"),
        )

    def _on_watchdog_tick(self):
        """Periodically audits heartbeat timeouts and emits keepalive to Backend."""
        self.gun_manager.check_heartbeat_timeouts(3.0)
        self._broadcast_all_gun_statuses()

    def _broadcast_all_gun_statuses(self):
        """Transmits current state of all connected guns to Backend to keep telemetry fresh."""
        if not self.send_to_backend:
            return
        for gun in self.gun_manager.get_all_guns():
            if gun.connected:
                self.udp_client.send_gun_status(
                    gun=gun.gun_id,
                    lane=gun.lane,
                    port=gun.port,
                    connected=gun.connected,
                    shot_count=gun.shot_count,
                    time_us=int(time.time() * 1_000_000),
                )


def run_daemon():
    """Main CLI entry point for headless tracker execution."""
    parser = argparse.ArgumentParser(description="Firing Simulator Headless Tracker Daemon")
    parser.add_argument("--unreal-host", default=config.UNREAL_IP, help="Unreal UDP host IP")
    parser.add_argument("--unreal-port", type=int, default=config.UNREAL_PORT, help="Unreal UDP port")
    parser.add_argument("--backend-host", default=config.BACKEND_IP, help="Backend UDP host IP")
    parser.add_argument("--backend-port", type=int, default=config.BACKEND_PORT, help="Backend UDP port")
    parser.add_argument("--no-backend", action="store_true", help="Disable telemetry to Backend")
    parser.add_argument("--no-sim", action="store_true", help="Disable simulated gun controllers")
    parser.add_argument("--sim-guns", type=int, default=config.SIMULATED_GUN_COUNT, help="Number of simulated guns")
    parser.add_argument("--launch-unreal", action="store_true", help="Auto launch Unreal Engine process")
    parser.add_argument("--display-width", type=int, default=1920, help="Fallback display width")
    parser.add_argument("--display-height", type=int, default=1080, help="Fallback display height")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])

    args = parser.parse_args()

    # Logging setup
    log_level = getattr(logging, args.log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] [TrackerDaemon] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Pure headless non-GUI Qt application
    app = QCoreApplication(sys.argv)

    sim_count = 0 if args.no_sim else args.sim_guns

    daemon = HeadlessTrackerDaemon(
        backend_host=args.backend_host,
        backend_port=args.backend_port,
        send_to_backend=not args.no_backend,
        unreal_host=args.unreal_host,
        unreal_port=args.unreal_port,
        simulated_guns=sim_count,
        auto_launch_unreal=args.launch_unreal,
        display_width=args.display_width,
        display_height=args.display_height,
    )

    # Clean OS signal handling (SIGINT, SIGTERM)
    def sig_handler(sig, frame):
        logger.info(f"Signal {sig} received, exiting...")
        daemon.stop()
        app.quit()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    daemon.start()

    # Wakeup timer to ensure Python process catches SIGINT/Ctrl+C promptly on Windows
    sig_timer = QTimer()
    sig_timer.setInterval(200)
    sig_timer.timeout.connect(lambda: None)
    sig_timer.start()

    exit_code = app.exec()
    daemon.stop()
    sys.exit(exit_code)


if __name__ == "__main__":
    run_daemon()
