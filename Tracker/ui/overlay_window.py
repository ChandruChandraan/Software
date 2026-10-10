"""
Multi-Gun Projector Overlay Host Window.
Renders independent configurable overlay layers for each Gun ID on the same selected projector.
Supports Individual Tracking Mode and Diagnostic Mode with distinct visual styling per gun.
"""

import time
from typing import List, Optional

from PySide6.QtCore import Qt, QRect, QTimer, Signal
from PySide6.QtGui import QKeyEvent, QMouseEvent, QPainter, QPen, QColor, QFont, QBrush
from PySide6.QtWidgets import QWidget

from core import config
from core.gun_state import MultiGunManager, GunState
from network.udp_client import UDPClient
from .display_manager import DisplayInfo


class ProjectorOverlay(QWidget):
    """
    Dedicated borderless fullscreen overlay host for the selected secondary display / projector.
    Renders simultaneous, independent visual layers for all registered Gun IDs.
    All layers share the exact same viewport coordinate space.
    """

    closed = Signal()
    active_gun_changed = Signal(int)

    def __init__(
        self,
        display_info: DisplayInfo,
        gun_manager: MultiGunManager,
        udp_client: Optional[UDPClient] = None,
        active_gun_id: int = 1,
        transparent: bool = True,
        parent=None,
    ):
        super().__init__(parent)
        self.display_info: DisplayInfo = display_info
        self.gun_manager: MultiGunManager = gun_manager
        self.udp_client: Optional[UDPClient] = udp_client
        self.active_gun_id: int = active_gun_id
        self.full_transparent: bool = transparent

        # Overlay Modes: False = Individual Tracking Mode (Mode A), True = Diagnostic Mode (Mode B)
        self.diagnostic_mode: bool = False
        self.show_hud: bool = True
        self.show_border: bool = True
        self.backdrop_mode: bool = False

        # True only after the user explicitly selects a gun from the dashboard table.
        # Until then, mouse movement does NOT move any crosshair.
        self.gun_selected: bool = False

        self.last_frame_time: float = time.time()
        self.current_fps: float = float(config.OVERLAY_FPS)

        self._configure_window()
        self._setup_connections()

        # 60 FPS render & polling loop
        self.render_timer = QTimer(self)
        self.render_timer.setInterval(int(1000 / config.OVERLAY_FPS))
        self.render_timer.timeout.connect(self._on_frame_tick)
        self.render_timer.start()

    def _configure_window(self):
        """Sets window properties for borderless fullscreen transparent overlay on target display."""
        if self.display_info.screen_obj is not None:
            self.setScreen(self.display_info.screen_obj)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setWindowTitle("FiringSim Projector Overlay")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setStyleSheet("background: transparent;")
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.CrossCursor)

        if self.display_info.screen_obj is not None:
            self.setGeometry(self.display_info.screen_obj.geometry())
        else:
            self.setGeometry(
                self.display_info.x,
                self.display_info.y,
                self.display_info.width,
                self.display_info.height,
            )

    def _setup_connections(self):
        # Repaint whenever any gun state, aim, or shot changes
        self.gun_manager.all_guns_changed.connect(self._safe_update)
        self.gun_manager.gun_state_changed.connect(self._on_gun_state_changed)
        self.gun_manager.gun_shot_fired.connect(self._on_gun_shot_fired)

    def _safe_update(self):
        try:
            if self.isVisible():
                self.update()
        except (RuntimeError, Exception):
            pass

    def _on_gun_state_changed(self, gun_id: int):
        # Auto-switch to newly connected gun if current active gun is disconnected
        active = self.gun_manager.get_gun(self.active_gun_id)
        gun = self.gun_manager.get_gun(gun_id)
        if gun and gun.connected and (not active or not active.connected):
            self.active_gun_id = gun_id
            self.gun_selected = True
        self._safe_update()

    def _on_gun_shot_fired(self, gun_id: int, payload: dict):
        # Always focus on whichever gun fired the trigger
        self.active_gun_id = gun_id
        self.gun_selected = True
        self._safe_update()

    def closeEvent(self, event):
        try:
            self.gun_manager.all_guns_changed.disconnect(self._safe_update)
            self.gun_manager.gun_state_changed.disconnect(self._on_gun_state_changed)
            self.gun_manager.gun_shot_fired.disconnect(self._on_gun_shot_fired)
        except Exception:
            pass
        if hasattr(self, "render_timer") and self.render_timer.isActive():
            self.render_timer.stop()
        self.closed.emit()
        super().closeEvent(event)

    def _enforce_topmost_on_secondary(self):
        """Ensures the border and HUD float directly over Unreal Engine on the secondary screen."""
        try:
            import ctypes
            user32 = ctypes.windll.user32
            hwnd = int(self.winId())
            HWND_TOPMOST = -1
            SWP_NOACTIVATE = 0x0010
            SWP_SHOWWINDOW = 0x0040
            user32.SetWindowPos(
                hwnd,
                HWND_TOPMOST,
                self.display_info.x,
                self.display_info.y,
                self.display_info.width,
                self.display_info.height,
                SWP_SHOWWINDOW | SWP_NOACTIVATE,
            )
        except Exception:
            pass

    def show_fullscreen_overlay(self):
        """Positions and raises the borderless window on the target screen over Unreal."""
        self.setGeometry(
            self.display_info.x,
            self.display_info.y,
            self.display_info.width,
            self.display_info.height,
        )
        self.show()
        win = self.windowHandle()
        if win is not None:
            if self.display_info.screen_obj is not None:
                win.setScreen(self.display_info.screen_obj)
            win.setGeometry(
                self.display_info.x,
                self.display_info.y,
                self.display_info.width,
                self.display_info.height,
            )
        self._enforce_topmost_on_secondary()
        self.raise_()

    def set_active_gun(self, gun_id: int):
        """Sets which Gun ID is actively focused. Called when hardware connects or fires."""
        self.active_gun_id = gun_id
        self.gun_selected = True
        self.update()

    def toggle_diagnostic_mode(self):
        """Toggles between Individual Tracking Mode and Diagnostic Mode."""
        self.diagnostic_mode = not self.diagnostic_mode
        self.update()

    def _on_frame_tick(self):
        now = time.time()
        dt = now - self.last_frame_time
        self.last_frame_time = now
        if dt > 0:
            fps_instant = 1.0 / dt
            self.current_fps = 0.9 * self.current_fps + 0.1 * fps_instant

        # Periodically re-assert topmost priority over Unreal on the secondary monitor (every ~1s)
        if not hasattr(self, "_tick_count"):
            self._tick_count = 0
        self._tick_count += 1
        if self._tick_count % 60 == 0:
            self._enforce_topmost_on_secondary()

        self.update()

    def mouseMoveEvent(self, event: QMouseEvent):
        """Move the selected gun's crosshair on hover — only after a gun is selected from the table."""
        if not self.gun_selected:
            super().mouseMoveEvent(event)
            return
        pos = event.position() if hasattr(event, "position") else event.pos()
        x, y = round(pos.x()), round(pos.y())
        if 0 <= x < self.width() and 0 <= y < self.height():
            active_gun = self.gun_manager.get_gun(self.active_gun_id)
            if active_gun is not None and active_gun.connected and (x != active_gun.latest_x or y != active_gun.latest_y):
                active_gun.update_aim(x, y, self.width(), self.height())
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        """Right-Click: Toggles CrossLane for Gun 1. Left-Click: Cycles active gun."""
        if event.button() == Qt.MouseButton.RightButton:
            active_gun = self.gun_manager.get_gun(self.active_gun_id)
            if active_gun is not None and active_gun.gun_id == 1:
                self.gun_manager.set_gun_cross_lane(1, not active_gun.cross_lane)
        elif event.button() == Qt.MouseButton.LeftButton:
            connected = self.gun_manager.get_connected_guns()
            if len(connected) > 1:
                curr_idx = next((i for i, g in enumerate(connected) if g.gun_id == self.active_gun_id), -1)
                next_gun = connected[(curr_idx + 1) % len(connected)]
                self.active_gun_id = next_gun.gun_id
                self.update()
        super().mousePressEvent(event)

    def keyPressEvent(self, event: QKeyEvent):
        """Key 1-8: Focus Gun ID. Key D: Toggle Diagnostic. Key B: Toggle Border. Key H: Toggle HUD. Key T: Backdrop. Key Esc: Close."""
        key = event.key()
        if key == Qt.Key.Key_Escape:
            self.close()
            event.accept()
            return
        elif Qt.Key.Key_1 <= key <= Qt.Key.Key_8:
            gid = key - Qt.Key.Key_0
            if self.gun_manager.get_gun(gid):
                self.active_gun_id = gid
                self.update()
        elif key == Qt.Key.Key_D:
            self.toggle_diagnostic_mode()
        elif key == Qt.Key.Key_B:
            self.show_border = not self.show_border
            self.update()
        elif key == Qt.Key.Key_H:
            self.show_hud = not self.show_hud
            self.update()
        elif key == Qt.Key.Key_T:
            self.backdrop_mode = not self.backdrop_mode
            self.update()
        elif key == Qt.Key.Key_Tab:
            connected = self.gun_manager.get_connected_guns()
            if connected:
                curr_idx = next((i for i, g in enumerate(connected) if g.gun_id == self.active_gun_id), -1)
                next_gun = connected[(curr_idx + 1) % len(connected)]
                self.active_gun_id = next_gun.gun_id
                self.update()
        super().keyPressEvent(event)


    def paintEvent(self, event):
        w = self.width()
        h = self.height()

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # 1. Background (drawn if full_transparent is False or backdrop_mode is True)
        if not self.full_transparent or self.backdrop_mode:
            painter.fillRect(0, 0, w, h, QColor(8, 12, 18, 225))

        # 2. Tactical Calibration Border Lines, Corner Brackets & Info Banners
        if self.show_border or self.show_hud:
            self._draw_overlay_borders_and_info(painter, w, h)

        # 3. Hardware Optical Center Crosshair
        cx, cy = w // 2, h // 2
        pen_center = QPen(QColor(100, 110, 125, 140))
        pen_center.setStyle(Qt.PenStyle.DashLine)
        pen_center.setWidth(1)
        painter.setPen(pen_center)
        painter.drawLine(0, cy, w, cy)
        painter.drawLine(cx, 0, cx, h)

        # Center coordinate tag
        if self.show_hud:
            painter.setFont(QFont("Consolas", 8, QFont.Weight.Bold))
            painter.setPen(QColor(100, 110, 125, 200))
            painter.drawText(cx + 8, cy - 8, f"CENTER ({cx}, {cy})")

        # 4. Render Individual Gun Layers (Connected Guns Only)
        guns = self.gun_manager.get_connected_guns()
        banner_y_offset = 54

        for gun in guns:
            if not gun.overlay_visible:
                continue

            # Draw aim reticle if coordinates are valid
            if gun.has_valid_aim and gun.latest_x is not None and gun.latest_y is not None:
                self._draw_gun_marker(painter, gun)

            # Draw Shot Feedback Banner if fired recently (< 2.0s)
            now = time.time()
            if now - gun.last_shot_time < 2.0 and gun.last_shot_text:
                self._draw_shot_banner(painter, gun, banner_y_offset)
                banner_y_offset += 48

        # 5. Diagnostic Mode or Individual Tracking Mode HUD
        if self.show_hud:
            if self.diagnostic_mode:
                self._draw_diagnostic_hud(painter, guns)
            else:
                self._draw_tracking_hud(painter)

        painter.end()

    def _draw_overlay_borders_and_info(self, painter: QPainter, w: int, h: int):
        """Renders high-tech tactical projector border lines, corner alignment brackets, and system info HUD."""
        # 1. Main Calibration Perimeter Border Line (Glowing Multi-Layer Green)
        if self.show_border:
            # Outer ambient glow border
            glow_pen = QPen(QColor(0, 230, 118, 60), 6)
            painter.setPen(glow_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(3, 3, w - 6, h - 6)

            # Crisp primary perimeter border
            border_pen = QPen(QColor("#00e676"), 2)
            painter.setPen(border_pen)
            painter.drawRect(2, 2, w - 4, h - 4)

            # Inset dashed framing line (16px inset)
            inner_pen = QPen(QColor(0, 230, 118, 90), 1, Qt.PenStyle.DashLine)
            painter.setPen(inner_pen)
            painter.drawRect(16, 16, w - 32, h - 32)

            # 2. Four Heavy Corner Alignment Brackets (Length: 50px, Thickness: 4px)
            corner_pen = QPen(QColor("#00e676"), 4)
            painter.setPen(corner_pen)
            cl = 50
            pad = 2

            # Top-Left Bracket
            painter.drawLine(pad, pad, pad + cl, pad)
            painter.drawLine(pad, pad, pad, pad + cl)

            # Top-Right Bracket
            painter.drawLine(w - pad, pad, w - pad - cl, pad)
            painter.drawLine(w - pad, pad, w - pad, pad + cl)

            # Bottom-Left Bracket
            painter.drawLine(pad, h - pad, pad + cl, h - pad)
            painter.drawLine(pad, h - pad, pad, h - pad - cl)

            # Bottom-Right Bracket
            painter.drawLine(w - pad, h - pad, w - pad - cl, h - pad)
            painter.drawLine(w - pad, h - pad, w - pad, h - pad - cl)

            # 3. Corner Coordinate Badges
            painter.setFont(QFont("Consolas", 8, QFont.Weight.Bold))
            painter.setPen(QPen(QColor(0, 230, 118, 200), 1))
            painter.setBrush(QBrush(QColor(10, 16, 24, 210)))

            # TL (0, 0)
            painter.drawRoundedRect(6, 6, 54, 18, 3, 3)
            painter.drawText(12, 19, "(0, 0)")

            # TR (W, 0)
            tr_w = 72
            painter.drawRoundedRect(w - tr_w - 6, 6, tr_w, 18, 3, 3)
            painter.drawText(w - tr_w, 19, f"({w}, 0)")

            # BL (0, H)
            painter.drawRoundedRect(6, h - 48, 64, 18, 3, 3)
            painter.drawText(12, h - 35, f"(0, {h})")

            # BR (W, H)
            br_w = 84
            painter.drawRoundedRect(w - br_w - 6, h - 48, br_w, 18, 3, 3)
            painter.drawText(w - br_w, h - 35, f"({w}, {h})")

            # 4. Alignment Ticks (at 25%, 50%, 75% margins)
            tick_pen = QPen(QColor(0, 230, 118, 160), 1)
            painter.setPen(tick_pen)
            for pct in (0.25, 0.5, 0.75):
                tx = int(w * pct)
                ty = int(h * pct)
                painter.drawLine(tx, 2, tx, 12)
                painter.drawLine(tx, h - 12, tx, h - 2)
                painter.drawLine(2, ty, 12, ty)
                painter.drawLine(w - 12, ty, w - 2, ty)

        # 5. Top Header Information Banner
        if self.show_hud:
            connected_guns = self.gun_manager.get_connected_guns()
            gun_count = len(connected_guns)
            active_gun = self.gun_manager.get_gun(self.active_gun_id)
            active_port = active_gun.port if active_gun and active_gun.port else "NO-PORT"
            active_lane = active_gun.lane if active_gun else self.active_gun_id

            # Top-Center HUD Info Pill
            top_info_w = 700
            top_info_h = 32
            top_rect = QRect((w - top_info_w) // 2, 8, top_info_w, top_info_h)

            painter.setPen(QPen(QColor(0, 230, 118, 180), 1))
            painter.setBrush(QBrush(QColor(8, 14, 22, 240)))
            painter.drawRoundedRect(top_rect, 6, 6)

            painter.setFont(QFont("Consolas", 9, QFont.Weight.Bold))
            painter.setPen(QColor("#00e676"))
            disp_txt = f"DISPLAY {self.display_info.index} ({self.display_info.width}x{self.display_info.height})"
            hud_info_str = f"⌖ FIRINGSIM TARGET SCREEN  |  {disp_txt}  |  FPS: {self.current_fps:.0f}  |  GUNS: {gun_count} ACTIVE"
            painter.drawText(top_rect, Qt.AlignmentFlag.AlignCenter, hud_info_str)

            # Top-Left Tag
            painter.setFont(QFont("Consolas", 8, QFont.Weight.Bold))
            painter.setPen(QColor(0, 230, 118, 180))
            painter.drawText(66, 20, "SCREEN BOUNDS: 1:1 RATIO")

            # Top-Right Tag
            painter.drawText(w - 360, 20, "ALIGNMENT • READY")

            # 6. Bottom Navigation & Status Info Bar
            bot_h = 30
            bot_rect = QRect(14, h - bot_h - 6, w - 28, bot_h)

            painter.setPen(QPen(QColor(40, 52, 72, 220), 1))
            painter.setBrush(QBrush(QColor(8, 12, 18, 240)))
            painter.drawRoundedRect(bot_rect, 6, 6)

            painter.setFont(QFont("Consolas", 8, QFont.Weight.Bold))

            # Bottom Left: Hardware Telemetry Info
            painter.setPen(QColor("#38bdf8"))
            total_shots = sum(g.shot_count for g in connected_guns) if connected_guns else 0
            left_str = f"ACTIVE: GUN {self.active_gun_id}  |  PORT: {active_port}  |  LANE: {active_lane}  |  TOTAL SHOTS: {total_shots}"
            painter.drawText(bot_rect.x() + 14, bot_rect.y() + 19, left_str)

            # Bottom Center: Hotkey Controls Info
            mode_str = "TEST MODE" if self.diagnostic_mode else "NORMAL MODE"
            mode_col = QColor("#f59e0b") if self.diagnostic_mode else QColor("#00e676")
            painter.setPen(mode_col)
            center_str = f"[MODE: {mode_str}]  [TAB/1-8: GUN]  [D: TEST]  [B: BORDER]  [H: INFO]  [T: BACKDROP]  [ESC: CLOSE]"
            painter.drawText(bot_rect, Qt.AlignmentFlag.AlignCenter, center_str)

            # Bottom Right: Telemetry Link State
            painter.setPen(QColor("#00e676"))
            painter.drawText(bot_rect.right() - 210, bot_rect.y() + 19, "CONNECTION: ONLINE ✓")

    def _draw_gun_marker(self, painter: QPainter, gun: GunState):
        """Draws an individual reticle layer tailored specifically for this Gun ID."""
        if gun.latest_x is None or gun.latest_y is None:
            return

        px: int = gun.latest_x
        py: int = gun.latest_y
        color = QColor(gun.color)
        is_active = (gun.gun_id == self.active_gun_id)

        # Outer Reticle Ring
        ring_pen = QPen(color, 3 if is_active else 2)
        painter.setPen(ring_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(px - 20, py - 20, 40, 40)

        # Active Gun Double Ring Glow
        if is_active:
            painter.setPen(QPen(QColor(color.red(), color.green(), color.blue(), 100), 1, Qt.PenStyle.DashLine))
            painter.drawEllipse(px - 28, py - 28, 56, 56)

        # Center Dot
        painter.setPen(Qt.PenStyle.NoPen)
        center_dot_color = QColor("#ffffff") if is_active else color
        painter.setBrush(QBrush(center_dot_color))
        painter.drawEllipse(px - 3, py - 3, 6, 6)

        # Crosshair Ticks
        painter.setPen(QPen(color, 2))
        painter.drawLine(px - 28, py, px - 12, py)
        painter.drawLine(px + 12, py, px + 28, py)
        painter.drawLine(px, py - 28, px, py - 12)
        painter.drawLine(px, py + 12, px, py + 28)

        # Gun Badge Label (e.g. "[G1] (1024, 768) L:1")
        badge_rect = QRect(px + 16, py + 16, 170, 42)
        painter.setPen(QPen(QColor("#30363d"), 1))
        painter.setBrush(QBrush(QColor(16, 20, 26, 220)))
        painter.drawRoundedRect(badge_rect, 6, 6)

        # Gun Tag
        painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        painter.setPen(color)
        gun_tag = f"GUN {gun.gun_id}" + (" [ACTIVE]" if is_active else "")
        painter.drawText(px + 22, py + 32, gun_tag)

        # Connection status indicator dot
        dot_color = QColor("#3fb950") if gun.connected else QColor("#da3633")
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(dot_color))
        painter.drawEllipse(px + 168, py + 24, 8, 8)

        # Coordinates & CrossLane Tag
        painter.setFont(QFont("Consolas", 8))
        painter.setPen(QColor("#c9d1d9"))
        cl_tag = " [CL]" if (gun.cross_lane and gun.gun_id == 1) else ""
        coord_txt = f"({px}, {py}){cl_tag}"
        painter.drawText(px + 22, py + 50, coord_txt)

    def _draw_shot_banner(self, painter: QPainter, gun: GunState, y_pos: int):
        """Displays visual confirmation banner when a gun fires."""
        banner_w = 340
        banner_h = 38
        banner_rect = QRect(24, y_pos, banner_w, banner_h)

        color = QColor(gun.color)
        painter.setPen(QPen(color, 1))
        painter.setBrush(QBrush(QColor(16, 45, 26, 230)))
        painter.drawRoundedRect(banner_rect, 6, 6)

        painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        painter.setPen(color)
        painter.drawText(banner_rect, Qt.AlignmentFlag.AlignCenter, gun.last_shot_text)

    def _draw_tracking_hud(self, painter: QPainter):
        """Mode A: Renders compact telemetry HUD for the active controller."""
        # Auto-fallback: if current active gun is disconnected, pick the first connected gun
        active_gun = self.gun_manager.get_gun(self.active_gun_id)
        if not active_gun or not active_gun.connected:
            connected = self.gun_manager.get_connected_guns()
            if connected:
                active_gun = connected[0]
                self.active_gun_id = active_gun.gun_id

        if not active_gun:
            active_gun = self.gun_manager.get_or_create_gun(self.active_gun_id)

        hud_w = 265
        hud_h = 195
        hud_rect = QRect(self.width() - hud_w - 24, 24, hud_w, hud_h)

        painter.setPen(QPen(QColor("#30363d"), 1))
        painter.setBrush(QBrush(QColor(16, 20, 26, 230)))
        painter.drawRoundedRect(hud_rect, 8, 8)

        color = QColor(active_gun.color)
        painter.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        painter.setPen(color)
        painter.drawText(hud_rect.x() + 14, hud_rect.y() + 26, f"GUN {active_gun.gun_id} STATUS")

        # Connection dot
        dot_color = QColor("#3fb950") if active_gun.connected else QColor("#da3633")
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(dot_color))
        painter.drawEllipse(hud_rect.x() + hud_w - 24, hud_rect.y() + 16, 10, 10)

        painter.setPen(QPen(QColor("#30363d"), 1))
        painter.drawLine(hud_rect.x() + 14, hud_rect.y() + 34, hud_rect.x() + hud_w - 14, hud_rect.y() + 34)

        if active_gun.gun_id == 1:
            cl_text = "ON" if active_gun.cross_lane else "OFF"
            cl_color = color if active_gun.cross_lane else QColor("#8b949e")
        else:
            cl_text = "N/A (Gun 1 Only)"
            cl_color = QColor("#8b949e")

        port_str = active_gun.port or "USB Auto"
        status_str = "Connected" if active_gun.connected else "Disconnected"
        status_col = QColor("#3fb950") if active_gun.connected else QColor("#da3633")

        aim_x_str = f"{active_gun.latest_x} px" if active_gun.latest_x is not None else "No Aim"
        aim_y_str = f"{active_gun.latest_y} px" if active_gun.latest_y is not None else "No Aim"

        rows = [
            ("Status:", status_str, status_col),
            ("Port:", port_str, QColor("#38bdf8")),
            ("Aim X:", aim_x_str, QColor("#58a6ff")),
            ("Aim Y:", aim_y_str, QColor("#58a6ff")),
            ("Lane:", f"{active_gun.lane}", QColor("#f0f6fc")),
            ("Cross-Lane:", cl_text, cl_color),
            ("Shots:", f"{active_gun.shot_count}", QColor("#f0f6fc")),
        ]

        painter.setFont(QFont("Consolas", 9, QFont.Weight.Bold))
        y = hud_rect.y() + 52
        for label, val, c in rows:
            painter.setPen(QColor("#8b949e"))
            painter.drawText(hud_rect.x() + 14, y, label)
            painter.setPen(c)
            painter.drawText(hud_rect.x() + 110, y, val)
            y += 18


    def _draw_diagnostic_hud(self, painter: QPainter, guns: List[GunState]):
        """Mode B: Diagnostic Mode status panel displaying all connected guns simultaneously."""
        card_w = 460
        card_h = 44 + max(1, len(guns)) * 26
        hud_rect = QRect(self.width() - card_w - 24, 24, card_w, card_h)

        painter.setPen(QPen(QColor("#388bfd"), 2))
        painter.setBrush(QBrush(QColor(13, 17, 23, 235)))
        painter.drawRoundedRect(hud_rect, 8, 8)

        painter.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        painter.setPen(QColor("#58a6ff"))
        painter.drawText(hud_rect.x() + 14, hud_rect.y() + 26, "CONNECTED GUNS STATUS")

        painter.setPen(QPen(QColor("#30363d"), 1))
        painter.drawLine(hud_rect.x() + 14, hud_rect.y() + 34, hud_rect.x() + card_w - 14, hud_rect.y() + 34)

        y = hud_rect.y() + 56
        painter.setFont(QFont("Consolas", 9, QFont.Weight.Bold))

        if not guns:
            painter.setPen(QColor("#8b949e"))
            painter.drawText(hud_rect.x() + 14, y, "No guns connected.")
            return

        for gun in guns:
            color = QColor(gun.color)

            # Dot
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(color))
            painter.drawEllipse(hud_rect.x() + 14, y - 9, 8, 8)

            # Label
            tag = f"G{gun.gun_id}" + ("*" if gun.gun_id == self.active_gun_id else " ")
            painter.setPen(color)
            painter.drawText(hud_rect.x() + 28, y, tag)

            # Port & Connection
            status_txt = "Connected" if gun.connected else "Disconnected"
            status_col = QColor("#3fb950") if gun.connected else QColor("#da3633")
            painter.setPen(status_col)
            port_label = gun.port or "USB Auto"
            painter.drawText(hud_rect.x() + 75, y, f"{port_label} [{status_txt}]")

            # Coordinates
            coords = f"({gun.latest_x},{gun.latest_y})" if gun.has_valid_aim else "(No Aim)"
            painter.setPen(QColor("#58a6ff"))
            painter.drawText(hud_rect.x() + 225, y, coords)

            # Trigger state
            trig_txt = "Firing" if gun.trigger_state == 1 else "Ready"
            trig_col = QColor("#ff7b72") if gun.trigger_state == 1 else QColor("#8b949e")
            painter.setPen(trig_col)
            painter.drawText(hud_rect.x() + 355, y, trig_txt)

            # Shots
            painter.setPen(QColor("#f0f6fc"))
            painter.drawText(hud_rect.x() + 410, y, f"#{gun.shot_count}")

            y += 26
