import json
import sys
import time
from pathlib import Path

from PySide6.QtCore import QObject, QTimer, QUrl
from PySide6.QtWidgets import QApplication
from PySide6.QtWebSockets import QWebSocket

from core import config
from core.gun_state import MultiGunManager
from network.udp_client import UDPClient
from ui.display_manager import DisplayManager
from ui.overlay_window import ProjectorOverlay


class OverlayTelemetryBridge(QObject):
    """
    Connects to the backend WebSocket stream (ws://127.0.0.1:8000/ws/backend)
    and synchronizes live shots, coordinates, lanes, and gun status into MultiGunManager.
    """

    def __init__(self, gun_manager: MultiGunManager, overlay: ProjectorOverlay):
        super().__init__()
        self.gun_manager = gun_manager
        self.overlay = overlay

        self.ws = QWebSocket()
        self.ws.textMessageReceived.connect(self._on_message)
        self.ws.connected.connect(lambda: print("[OVERLAY] Connected to live backend telemetry feed."))
        self.ws.disconnected.connect(self._on_disconnected)

        self._reconnect_timer = QTimer(self)
        self._reconnect_timer.setInterval(2000)
        self._reconnect_timer.timeout.connect(self._connect_ws)

        self._connect_ws()

    def _connect_ws(self):
        http_port = getattr(config, "BACKEND_HTTP_PORT", 8080)
        backend_url = f"ws://{config.BACKEND_IP}:{http_port}/ws/backend"
        self.ws.open(QUrl(backend_url))

    def _on_disconnected(self):
        if not self._reconnect_timer.isActive():
            self._reconnect_timer.start()

    def _on_message(self, text: str):
        try:
            msg = json.loads(text)
            topic = msg.get("topic")
            data = msg.get("data", {})

            if topic == "gun_status":
                gid = data.get("gun")
                if gid:
                    gun = self.gun_manager.get_or_create_gun(gid)
                    gun.port = data.get("port")
                    gun.connected = bool(data.get("connected"))
                    gun.lane = data.get("lane", gid)
                    gun.shot_count = data.get("shot_count", 0)
                    gun.last_heartbeat = time.time()
                    if gun.connected:
                        self.overlay.set_active_gun(gid)
                    self.overlay.update()

            elif topic == "shot":
                gid = data.get("gun")
                if gid:
                    gun = self.gun_manager.get_or_create_gun(gid)
                    gun.connected = True
                    gun.lane = data.get("lane", gid)
                    gun.cross_lane = bool(data.get("cross_lane", False))
                    x = data.get("x")
                    y = data.get("y")
                    if x is not None and y is not None:
                        gun.update_aim(
                            int(x), int(y),
                            self.gun_manager.display_width,
                            self.gun_manager.display_height,
                        )
                    gun.record_shot()
                    self.overlay.set_active_gun(gid)
                    self.overlay.update()
        except Exception as e:
            print(f"[OVERLAY] Telemetry parse error: {e}")


def run_overlay():
    import argparse
    parser = argparse.ArgumentParser(description="FiringSim Projector Overlay")
    parser.add_argument("--display", type=int, default=None, help="1-based Display index")
    parser.add_argument("--x", type=int, default=None, help="Target screen X coordinate")
    parser.add_argument("--y", type=int, default=None, help="Target screen Y coordinate")
    parser.add_argument("--w", type=int, default=None, help="Target screen width")
    parser.add_argument("--h", type=int, default=None, help="Target screen height")
    cli_args, _ = parser.parse_known_args()

    app = QApplication(sys.argv)
    app.setApplicationName("FiringSim Projector Overlay")
    app.setQuitOnLastWindowClosed(True)

    displays = DisplayManager.get_displays()
    if not displays:
        print("[OVERLAY] No displays detected. Exiting.")
        return

    # Select target secondary projector display
    target_display = None
    if cli_args.display is not None:
        target_display = next((d for d in displays if d.index == cli_args.display), None)

    if target_display is None:
        # Secondary display / projector by default
        default_to_primary = getattr(config, "DEFAULT_TO_PRIMARY_DISPLAY", False)
        if default_to_primary:
            target_display = displays[0]
        else:
            secondary = next((d for d in displays if not d.is_primary), None)
            target_display = secondary if secondary else displays[0]

    # Override geometry with CLI values if specified
    if cli_args.x is not None:
        target_display.x = cli_args.x
    if cli_args.y is not None:
        target_display.y = cli_args.y
    if cli_args.w is not None:
        target_display.width = cli_args.w
    if cli_args.h is not None:
        target_display.height = cli_args.h

    print(f"[OVERLAY] Launching overlay on Display {target_display.index} ({target_display.width}x{target_display.height}) at pos ({target_display.x}, {target_display.y})...")

    gun_manager = MultiGunManager(default_gun_count=0)
    gun_manager.set_display_geometry(
        target_display.index, target_display.x, target_display.y, target_display.width, target_display.height
    )

    udp_client = UDPClient(
        ip=config.UNREAL_IP,
        port=config.UNREAL_PORT,
        backend_ip=config.BACKEND_IP,
        backend_port=config.BACKEND_PORT,
    )
    udp_client.connect_client()

    overlay = ProjectorOverlay(
        display_info=target_display,
        gun_manager=gun_manager,
        udp_client=udp_client,
        active_gun_id=1,
        transparent=getattr(config, "OVERLAY_TRANSPARENT", True),
    )
    overlay.setWindowTitle("FiringSim Projector Overlay")
    overlay.show_fullscreen_overlay()

    # Synchronize live telemetry from backend
    telemetry_bridge = OverlayTelemetryBridge(gun_manager, overlay)

    sys.exit(app.exec())


if __name__ == "__main__":
    run_overlay()

