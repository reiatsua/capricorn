"""
Cyberpunk dialogue popup window for Capri with terminal chat and animated avatar.
"""

import random
from PyQt6.QtCore import Qt, QPoint, QRectF, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QKeyEvent
)
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit,
    QPushButton, QLabel, QFrame, QGraphicsOpacityEffect
)
from capri_star import CapriAvatarWidget

class CyberpunkDialogueBox(QWidget):
    """Cyberpunk Terminal HUD Popup window."""

    user_submitted_text = pyqtSignal(str)
    closed_by_user = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # Frameless, transparent, stays on top
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.SubWindow
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedSize(440, 440)

        # Speech typewriter animation timer
        self._typewriter_timer = QTimer(self)
        self._typewriter_timer.timeout.connect(self._typewriter_tick)
        self._full_reply_text = ""
        self._current_type_idx = 0

        # Avatar mouth glitch timer
        self._avatar_glitch_timer = QTimer(self)
        self._avatar_glitch_timer.timeout.connect(self._avatar_glitch_tick)

        self._init_ui()

    def _init_ui(self):
        # Outer layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(6)

        # 1. Header Bar
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(4, 2, 4, 2)

        self.title_label = QLabel("CAPRI // ONLINE")
        self.title_label.setStyleSheet("color: #00F0FF; font-family: 'Consolas', monospace; font-weight: bold; font-size: 11px;")
        header_layout.addWidget(self.title_label)

        header_layout.addStretch()

        self.btn_close = QPushButton("✕")
        self.btn_close.setFixedSize(20, 20)
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #FEEB00;
                border: 1px solid #FEEB00;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #FEEB00;
                color: #000;
            }
        """)
        self.btn_close.clicked.connect(self._on_close_clicked)
        header_layout.addWidget(self.btn_close)
        main_layout.addLayout(header_layout)

        # 2. Dialogue / Terminal History Area
        self.dialogue_view = QTextEdit()
        self.dialogue_view.setReadOnly(True)
        self.dialogue_view.setStyleSheet("""
            QTextEdit {
                background-color: rgba(6, 9, 15, 0.95);
                color: #E0E6ED;
                border: 1.5px solid #FEEB00;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
                padding: 8px;
                line-height: 1.4;
            }
        """)
        main_layout.addWidget(self.dialogue_view, stretch=3)

        # 3. Avatar Section & Status Label
        avatar_row = QHBoxLayout()
        avatar_row.setContentsMargins(0, 0, 0, 0)
        avatar_row.setSpacing(8)

        self.avatar = CapriAvatarWidget()
        avatar_row.addWidget(self.avatar)

        # Side Status / Stats Box
        stats_box = QFrame()
        stats_box.setStyleSheet("""
            QFrame {
                background-color: rgba(10, 15, 24, 0.85);
                border: 1px solid #00F0FF;
                padding: 4px;
            }
        """)
        stats_layout = QVBoxLayout(stats_box)
        stats_layout.setContentsMargins(6, 4, 6, 4)
        stats_layout.setSpacing(2)

        self.status_tag = QLabel("CONSTRUCT // ACTIVE")
        self.status_tag.setStyleSheet("color: #00F0FF; font-family: 'Consolas', monospace; font-size: 10px; font-weight: bold;")
        stats_layout.addWidget(self.status_tag)

        self.fps_tag = QLabel("NET: STABLE | SESS: #0921")
        self.fps_tag.setStyleSheet("color: #7D8B99; font-family: 'Consolas', monospace; font-size: 9px;")
        stats_layout.addWidget(self.fps_tag)

        stats_layout.addStretch()

        self.hotkey_hint = QLabel("Mic Hotkey: '\\'")
        self.hotkey_hint.setStyleSheet("color: #FEEB00; font-family: 'Consolas', monospace; font-size: 9px;")
        stats_layout.addWidget(self.hotkey_hint)

        avatar_row.addWidget(stats_box, stretch=1)
        main_layout.addLayout(avatar_row)

        # 4. User Input Line
        input_layout = QHBoxLayout()
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(6)

        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("Type a message or press '\\' to speak...")
        self.input_edit.setStyleSheet("""
            QLineEdit {
                background-color: rgba(10, 14, 22, 0.95);
                color: #FFFFFF;
                border: 1.5px solid #00F0FF;
                font-family: 'Consolas', monospace;
                font-size: 12px;
                padding: 6px 8px;
            }
            QLineEdit:focus {
                border: 1.5px solid #FEEB00;
            }
        """)
        self.input_edit.returnPressed.connect(self._send_input)
        input_layout.addWidget(self.input_edit, stretch=1)

        self.btn_send = QPushButton("SEND ↵")
        self.btn_send.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_send.setStyleSheet("""
            QPushButton {
                background-color: #00F0FF;
                color: #000000;
                font-family: 'Consolas', monospace;
                font-weight: bold;
                font-size: 11px;
                padding: 6px 14px;
                border: none;
            }
            QPushButton:hover {
                background-color: #FEEB00;
            }
            QPushButton:pressed {
                background-color: #FF0055;
                color: #FFF;
            }
        """)
        self.btn_send.clicked.connect(self._send_input)
        input_layout.addWidget(self.btn_send)

        main_layout.addLayout(input_layout)

    def paintEvent(self, event):
        """Draw Cyberpunk neon HUD borders and scanline accents."""
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        w, h = self.width(), self.height()

        # Dark HUD background
        p.fillRect(0, 0, w, h, QColor(7, 10, 16, 240))

        # Cyberpunk corner chamfers & border
        pen = QPen(QColor(0, 240, 255), 1.5)
        p.setPen(pen)
        p.drawRect(1, 1, w - 2, h - 2)

        # Accent yellow top and corner markers
        p.setPen(QPen(QColor(254, 235, 0), 2.5))
        corner_len = 16
        # Top-left
        p.drawLine(1, 1, corner_len, 1)
        p.drawLine(1, 1, 1, corner_len)
        # Top-right
        p.drawLine(w - corner_len, 1, w - 1, 1)
        p.drawLine(w - 1, 1, w - 1, corner_len)
        # Bottom-left
        p.drawLine(1, h - 1, corner_len, h - 1)
        p.drawLine(1, h - corner_len, 1, h - 1)
        # Bottom-right
        p.drawLine(w - corner_len, h - 1, w - 1, h - 1)
        p.drawLine(w - 1, h - corner_len, w - 1, h - 1)

    def show_animated(self, target_pos: QPoint):
        """Open with a quick glitch appearance at target position."""
        self.move(target_pos)
        self.show()
        self.raise_()
        self.activateWindow()
        self.input_edit.setFocus()

    def set_capri_speaking(self, text: str, source: str = "TALKING"):
        """Displays Capri speaking with typewriter text and animated avatar."""
        self.title_label.setText(f"CAPRI // {source}")
        self.status_tag.setText(f"STATE // {source}")
        self.avatar.set_talking(True)

        # Prepare typewriter
        self._full_reply_text = text
        self._current_type_idx = 0

        # Append prompt prefix
        self.dialogue_view.append(
            f"<div style='margin-bottom: 4px;'>"
            f"<span style='color: #FEEB00; font-weight: bold;'>CAPRI :</span> "
            f"<span id='cur_capri' style='color: #00F0FF; font-weight: 500;'></span>"
            f"</div>"
        )

        self._typewriter_timer.start(18) # 18ms per char
        self._avatar_glitch_timer.start(80)

    def append_user_message(self, text: str, is_voice: bool = False):
        """Add user message to dialogue."""
        label = "you (voice)" if is_voice else "you"
        self.dialogue_view.append(
            f"<div style='margin-bottom: 6px; color: #55FF99;'>"
            f"&gt; <span style='color: #00FFAA; font-weight: bold;'>{label}:</span> "
            f"<span style='color: #FFFFFF;'>{text}</span>"
            f"</div>"
        )
        self.dialogue_view.ensureCursorVisible()

    def set_thinking_state(self):
        """Show thinking indicator."""
        self.title_label.setText("CAPRI // THINKING")
        self.status_tag.setText("STATE // THINKING")
        self.avatar.set_talking(False)

    def _typewriter_tick(self):
        if self._current_type_idx < len(self._full_reply_text):
            self._current_type_idx += 1
            cur_slice = self._full_reply_text[:self._current_type_idx]
            # Replace the last paragraph
            cursor = self.dialogue_view.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            cursor.select(cursor.SelectionType.BlockUnderCursor)
            cursor.removeSelectedText()
            cursor.insertHtml(
                f"<div style='margin-bottom: 8px;'>"
                f"<span style='color: #FEEB00; font-weight: bold;'>CAPRI :</span> "
                f"<span style='color: #00F0FF; font-weight: 500;'>{cur_slice}</span>"
                f"</div>"
            )
            self.dialogue_view.setTextCursor(cursor)
            self.dialogue_view.ensureCursorVisible()
        else:
            self._typewriter_timer.stop()
            self.avatar.set_talking(False)
            self._avatar_glitch_timer.stop()
            self.title_label.setText("CAPRI // ONLINE")
            self.status_tag.setText("STATE // ONLINE")

    def _avatar_glitch_tick(self):
        self.avatar.mouth_offset = random.choice([-2.0, 0.0, 2.0, 3.5])
        self.avatar.update()

    def _send_input(self):
        text = self.input_edit.text().strip()
        if text:
            self.input_edit.clear()
            self.append_user_message(text, is_voice=False)
            self.set_thinking_state()
            self.user_submitted_text.emit(text)

    def _on_close_clicked(self):
        self.hide()
        self.closed_by_user.emit()
