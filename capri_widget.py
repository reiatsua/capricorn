"""
Floating Star Desktop Widget for Capri.
Drifts gently across the screen, displays status, and manages the dialogue popup.
"""

import sys
import math
import random
from PyQt6.QtCore import Qt, QPoint, QRectF, QTimer, pyqtSignal, QPointF
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QCursor, QGuiApplication,
    QMouseEvent, QAction
)
from PyQt6.QtWidgets import QWidget, QMenu

from capri_star import CapriStarDrawer
from capri_dialog import CyberpunkDialogueBox

class CapriFloatingStar(QWidget):
    """Floating desktop companion star widget with Cyberpunk aesthetic."""

    request_screen_check = pyqtSignal()
    request_voice_toggle = pyqtSignal()
    user_sent_message = pyqtSignal(str)
    closed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # Frameless, stay on top, transparent
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedSize(180, 140)

        # State management
        self.state = "DORMANT"  # DORMANT, WATCHING, LISTENING, THINKING, TALKING, ONLINE
        self._anim_time = 0.0

        # Gentle drifting physics
        self.pos_x = 1200.0
        self.pos_y = 200.0
        self.vel_x = random.choice([-0.45, 0.45])
        self.vel_y = random.choice([-0.30, 0.30])
        self.is_drifting = True

        # Mouse dragging state
        self._is_dragging = False
        self._drag_start_pos = QPoint()

        # Connect dialogue box
        self.dialogue_box = CyberpunkDialogueBox()
        self.dialogue_box.user_submitted_text.connect(self._on_user_submitted_text)
        self.dialogue_box.closed_by_user.connect(self._on_dialogue_closed)

        # Animation & Physics Timer (60 FPS)
        self._phys_timer = QTimer(self)
        self._phys_timer.timeout.connect(self._physics_tick)
        self._phys_timer.start(16)

        # Position widget on screen
        self._center_initial_position()

    def _center_initial_position(self):
        screen = QGuiApplication.primaryScreen()
        if screen:
            geom = screen.availableGeometry()
            self.pos_x = float(geom.width() - self.width() - 80)
            self.pos_y = float(geom.height() // 3)
            self.move(int(self.pos_x), int(self.pos_y))

    def set_state(self, state: str):
        """Update Capri's state."""
        self.state = state
        self.update()

    def on_screen_analyzed(self, comment: str):
        """Called when Screen Watcher finishes analyzing screen."""
        self.set_state("WATCHING")
        self._open_dialogue()
        self.dialogue_box.set_capri_speaking(comment, source="WATCHING")
        # Return to ONLINE after brief moment
        QTimer.singleShot(3500, lambda: self.set_state("ONLINE") if self.state == "WATCHING" else None)

    def on_voice_started(self):
        """Voice recording started."""
        self.set_state("LISTENING")

    def on_voice_transcribed(self, text: str):
        """Voice recognized."""
        self._open_dialogue()
        self.dialogue_box.append_user_message(text, is_voice=True)
        self.dialogue_box.set_thinking_state()
        self.set_state("THINKING")

    def on_ai_reply(self, reply_text: str):
        """AI replied."""
        self._open_dialogue()
        self.set_state("TALKING")
        self.dialogue_box.set_capri_speaking(reply_text, source="TALKING")

    def _open_dialogue(self):
        """Positions and displays the dialogue box next to the star."""
        screen = QGuiApplication.primaryScreen()
        if not screen:
            return

        screen_geom = screen.availableGeometry()
        star_pos = self.pos()

        # Try to place to the left of star if enough room, else to the right
        diag_w = self.dialogue_box.width()
        diag_h = self.dialogue_box.height()

        target_x = star_pos.x() - diag_w - 15
        if target_x < screen_geom.left() + 20:
            target_x = star_pos.x() + self.width() + 15

        target_y = star_pos.y() - 40
        if target_y + diag_h > screen_geom.bottom() - 20:
            target_y = screen_geom.bottom() - diag_h - 20
        if target_y < screen_geom.top() + 20:
            target_y = screen_geom.top() + 20

        self.dialogue_box.show_animated(QPoint(int(target_x), int(target_y)))
        # Pause drifting while dialogue is open
        self.is_drifting = False

    def _on_dialogue_closed(self):
        self.is_drifting = True
        self.set_state("DORMANT")

    def _on_user_submitted_text(self, text: str):
        self.set_state("THINKING")
        self.user_sent_message.emit(text)

    def _physics_tick(self):
        self._anim_time += 0.016

        # Drifting physics
        if self.is_drifting and not self._is_dragging:
            screen = QGuiApplication.primaryScreen()
            if screen:
                geom = screen.availableGeometry()
                pad = 40

                # Subtle sinusoidal perturbation to drift
                drift_noise_x = math.sin(self._anim_time * 0.4) * 0.15
                drift_noise_y = math.cos(self._anim_time * 0.35) * 0.12

                self.pos_x += self.vel_x + drift_noise_x
                self.pos_y += self.vel_y + drift_noise_y

                # Bounce off screen bounds
                min_x = geom.left() + pad
                max_x = geom.right() - self.width() - pad
                min_y = geom.top() + pad
                max_y = geom.bottom() - self.height() - pad

                if self.pos_x < min_x:
                    self.pos_x = min_x
                    self.vel_x = abs(self.vel_x)
                elif self.pos_x > max_x:
                    self.pos_x = max_x
                    self.vel_x = -abs(self.vel_x)

                if self.pos_y < min_y:
                    self.pos_y = min_y
                    self.vel_y = abs(self.vel_y)
                elif self.pos_y > max_y:
                    self.pos_y = max_y
                    self.vel_y = -abs(self.vel_y)

                self.move(int(self.pos_x), int(self.pos_y))

        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        cx = self.width() / 2.0
        cy = 52.0
        size = 38.0

        # Slight floating wobble & breathing pulse
        angle_wobble = math.sin(self._anim_time * 1.4) * 4.0
        pulse = 1.0 + math.sin(self._anim_time * 2.2) * 0.04

        # 1. Draw Star
        CapriStarDrawer.draw_star(p, cx, cy, size, angle_deg=angle_wobble, pulse=pulse, state=self.state)

        # 2. Draw Status Pill Underneath
        pill_w = 150
        pill_h = 24
        pill_x = int((self.width() - pill_w) / 2)
        pill_y = int(cy + size + 8)

        # Border & text color by state
        if "WATCH" in self.state:
            border_color = QColor(255, 165, 0)
            text_color = QColor(255, 200, 50)
            status_text = "CAPRI // WATCHING"
        elif "LISTEN" in self.state:
            border_color = QColor(255, 0, 150)
            text_color = QColor(255, 100, 200)
            # Animated progress dashes
            dots = "-" * (int(self._anim_time * 4) % 6 + 1)
            status_text = f"CAPRI // LISTENING [{dots:<6}]"
        elif "THINK" in self.state:
            border_color = QColor(254, 235, 0)
            text_color = QColor(254, 235, 0)
            status_text = "CAPRI // THINKING"
        elif "TALK" in self.state:
            border_color = QColor(0, 255, 130)
            text_color = QColor(0, 255, 180)
            status_text = "CAPRI // TALKING"
        elif "ONLINE" in self.state:
            border_color = QColor(0, 255, 120)
            text_color = QColor(0, 255, 120)
            status_text = "CAPRI // ONLINE"
        else: # DORMANT
            border_color = QColor(0, 255, 120, 180)
            text_color = QColor(0, 255, 120)
            status_text = "CAPRI // DORMANT"

        # Dark pill background
        p.setBrush(QBrush(QColor(8, 12, 18, 235)))
        p.setPen(QPen(border_color, 1.2))
        p.drawRoundedRect(pill_x, pill_y, pill_w, pill_h, 3.0, 3.0)

        # Status Text
        p.setFont(QFont("Consolas", 8, QFont.Weight.Bold))
        p.setPen(QPen(text_color))
        p.drawText(QRectF(pill_x, pill_y, pill_w, pill_h), Qt.AlignmentFlag.AlignCenter, status_text)

    # --- Mouse Drag & Click Handling ---
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = True
            self._drag_start_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
        elif event.button() == Qt.MouseButton.RightButton:
            self._show_context_menu(event.globalPosition().toPoint())
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._is_dragging:
            new_pos = event.globalPosition().toPoint() - self._drag_start_pos
            self.pos_x = float(new_pos.x())
            self.pos_y = float(new_pos.y())
            self.move(new_pos)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            if self._is_dragging:
                self._is_dragging = False
                # If barely moved, treat as click to toggle dialogue
                moved_dist = (event.globalPosition().toPoint() - (self.frameGeometry().topLeft() + self._drag_start_pos)).manhattanLength()
                if moved_dist < 6:
                    if self.dialogue_box.isVisible():
                        self.dialogue_box.hide()
                        self._on_dialogue_closed()
                    else:
                        self._open_dialogue()
            event.accept()

    def _show_context_menu(self, global_pos: QPoint):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #0B0F17;
                color: #00F0FF;
                border: 1px solid #FEEB00;
                font-family: 'Consolas', monospace;
                font-size: 11px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 18px;
            }
            QMenu::item:selected {
                background-color: #FEEB00;
                color: #000000;
                font-weight: bold;
            }
        """)

        act_talk = menu.addAction("Say something (Open Chat)...")
        act_watch = menu.addAction("Check screen now (/watch)")
        act_voice = menu.addAction("Talk to Capri (Mic '\\')...")
        menu.addSeparator()
        act_reset = menu.addAction("Reset position")
        act_quit = menu.addAction("Disconnect (Exit)")

        action = menu.exec(global_pos)
        if action == act_talk:
            self._open_dialogue()
        elif action == act_watch:
            self.request_screen_check.emit()
        elif action == act_voice:
            self.request_voice_toggle.emit()
        elif action == act_reset:
            self._center_initial_position()
        elif action == act_quit:
            self.dialogue_box.close()
            self.close()
            self.closed.emit()
