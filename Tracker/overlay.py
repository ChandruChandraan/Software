"""
Standalone Projector Overlay Application for Firing Simulator.
Runs an independent, transparent, fullscreen projector reticle overlay window
on the designated secondary or projector display.
"""

import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication

from core import config
from core.gun_state import MultiGunManager
from network.udp_client import UDPClient
from ui.display_manager import DisplayManager
from ui.overlay_window import ProjectorOverlay


def run_overlay():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    displays = DisplayManager.get_displays()
    if not displays:
        print("[OVERLAY] No displays detected. Exiting.")
        return

    # Select secondary display / projector by default
    default_to_primary = getattr(config, "DEFAULT_TO_PRIMARY_DISPLAY", False)
    target_display = displays[0]
    if not default_to_primary:
        secondary = next((d for d in displays if not d.is_primary), None)
        if secondary:
            target_display = secondary

    print(f"[OVERLAY] Launching overlay on Display {target_display.index} ({target_display.width}x{target_display.height})...")

    gun_manager = MultiGunManager(default_gun_count=getattr(config, "SIMULATED_GUN_COUNT", 4))
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
    overlay.show_fullscreen_overlay()

    sys.exit(app.exec())


if __name__ == "__main__":
    run_overlay()
