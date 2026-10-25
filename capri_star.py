"""
Capri Visual Assets and Rendering Components.
Draws the cyberpunk 8-pointed star and avatar using QPainter.
"""

import math
from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QBrush, QPainterPath,
    QRadialGradient, QLinearGradient, QFont
)
from PyQt6.QtWidgets import QWidget

class CapriStarDrawer:
    """Renders the authentic Cyberpunk 8-pointed construct star."""

    @staticmethod
    def draw_star(painter: QPainter, cx: float, cy: float, size: float,
                  angle_deg: float = 0.0, pulse: float = 1.0, state: str = "DORMANT"):
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(angle_deg)
        painter.scale(pulse, pulse)

        # Color schemes based on state
        if "WATCH" in state:
            c_main = QColor(255, 165, 0)     # Orange/Amber
            c_accent = QColor(0, 255, 120)   # Cyberpunk Neon Green
            c_glow = QColor(255, 180, 0, 100)
        elif "LISTEN" in state:
            c_main = QColor(255, 0, 128)     # Magenta/Pink
            c_accent = QColor(0, 255, 140)   # Neon Green
            c_glow = QColor(255, 0, 180, 120)
        elif "THINK" in state:
            c_main = QColor(254, 235, 0)     # Cyberpunk Yellow
            c_accent = QColor(255, 60, 60)   # Red
            c_glow = QColor(254, 235, 0, 110)
        else: # DORMANT / ONLINE
            c_main = QColor(245, 15, 65)     # Cyberpunk Neon Red
            c_accent = QColor(0, 255, 110)   # Electric Neon Green
            c_glow = QColor(0, 255, 110, 85)

        # 1. Subtle Outer Glow
        glow_grad = QRadialGradient(0, 0, size * 1.1)
        glow_grad.setColorAt(0.0, c_glow)
        glow_grad.setColorAt(0.7, QColor(c_glow.red(), c_glow.green(), c_glow.blue(), 30))
        glow_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(glow_grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(0, 0), size * 1.1, size * 1.1)

        # 2. Diagonal Points (NE, NW, SE, SW) - shorter neon blades
        diag_len = size * 0.62
        diag_width = size * 0.18
        for a in [45, 135, 225, 315]:
            painter.save()
            painter.rotate(a)
            path = QPainterPath()
            path.moveTo(0, -size * 0.22)
            path.lineTo(-diag_width * 0.5, -size * 0.35)
            path.lineTo(0, -diag_len)
            path.lineTo(diag_width * 0.5, -size * 0.35)
            path.closeSubpath()

            painter.setBrush(QBrush(c_accent))
            painter.setPen(QPen(QColor(80, 255, 160), 1.0))
            painter.drawPath(path)
            painter.restore()

        # 3. Cardinal Points (N, E, S, W) - long sharp stylized blades
        card_len = size * 0.95
        card_w = size * 0.26
        for a in [0, 90, 180, 270]:
            painter.save()
            painter.rotate(a)

            # Main blade body (Red)
            blade_path = QPainterPath()
            blade_path.moveTo(0, -size * 0.25)
            blade_path.lineTo(-card_w * 0.5, -size * 0.42)
            blade_path.lineTo(0, -card_len)
            blade_path.lineTo(card_w * 0.5, -size * 0.42)
            blade_path.closeSubpath()

            blade_grad = QLinearGradient(0, -size * 0.25, 0, -card_len)
            blade_grad.setColorAt(0.0, c_main)
            blade_grad.setColorAt(1.0, QColor(min(255, c_main.red() + 30), c_main.green(), c_main.blue()))

            painter.setBrush(QBrush(blade_grad))
            painter.setPen(QPen(QColor(255, 80, 120), 1.2))
            painter.drawPath(blade_path)

            # Center spine / inner accent on the blade
            spine_path = QPainterPath()
            spine_path.moveTo(0, -size * 0.32)
            spine_path.lineTo(0, -card_len * 0.88)
            painter.setPen(QPen(c_accent, 1.5))
            painter.drawPath(spine_path)

            # Lateral bevel line
            left_bevel = QPainterPath()
            left_bevel.moveTo(-card_w * 0.5, -size * 0.42)
            left_bevel.lineTo(0, -card_len)
            painter.setPen(QPen(QColor(255, 255, 255, 180), 1.0))
            painter.drawPath(left_bevel)

            painter.restore()

        # 4. Central Socket & Eye
        eye_rad = size * 0.24
        # Outer dark ring
        painter.setBrush(QBrush(QColor(10, 14, 22)))
        painter.setPen(QPen(c_accent, 2.0))
        painter.drawEllipse(QPointF(0, 0), eye_rad, eye_rad)

        # Iris ring
        painter.setBrush(QBrush(QColor(15, 25, 35)))
        painter.setPen(QPen(c_main, 1.2))
        painter.drawEllipse(QPointF(0, 0), eye_rad * 0.72, eye_rad * 0.72)

        # Glowing Diamond Pupil / Core
        diamond = QPainterPath()
        d_size = eye_rad * 0.45 * pulse
        diamond.moveTo(0, -d_size)
        diamond.lineTo(d_size, 0)
        diamond.lineTo(0, d_size)
        diamond.lineTo(-d_size, 0)
        diamond.closeSubpath()

        painter.setBrush(QBrush(c_accent))
        painter.setPen(QPen(QColor(255, 255, 255), 1.0))
        painter.drawPath(diamond)

        # Tiny white center spark
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(0, 0), 2.0, 2.0)

        painter.restore()


class CapriAvatarWidget(QWidget):
    """Renders the authentic stylized construct face from the video."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(160, 95)
        self.is_talking = False
        self.mouth_offset = 0.0

    def set_talking(self, talking: bool):
        self.is_talking = talking
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        w, h = self.width(), self.height()

        # 1. Cyberpunk Red Background
        p.fillRect(0, 0, w, h, QColor(220, 20, 60))

        # 2. Geometric jagged black silhouette (Hair / Collar / Helmet)
        p.setBrush(QBrush(QColor(15, 17, 24)))
        p.setPen(Qt.PenStyle.NoPen)

        # Back shadow
        path_shadow = QPainterPath()
        path_shadow.moveTo(0, 0)
        path_shadow.lineTo(w * 0.45, 0)
        path_shadow.lineTo(w * 0.25, h)
        path_shadow.lineTo(0, h)
        path_shadow.closeSubpath()
        p.drawPath(path_shadow)

        # Head / Hair angular silhouette
        head_path = QPainterPath()
        head_path.moveTo(w * 0.35, 10)
        head_path.lineTo(w * 0.85, 20)
        head_path.lineTo(w * 0.95, h * 0.65)
        head_path.lineTo(w * 0.75, h - 5)
        head_path.lineTo(w * 0.45, h - 10)
        head_path.lineTo(w * 0.30, h * 0.55)
        head_path.closeSubpath()
        p.drawPath(head_path)

        # 3. Neon Green Visor / Cybernetic Eye Mask
        visor_color = QColor(0, 255, 170)
        p.setBrush(QBrush(visor_color))
        p.setPen(QPen(QColor(255, 255, 255), 1.2))

        visor = QPainterPath()
        vx, vy = w * 0.52, h * 0.42
        visor.moveTo(vx, vy)
        visor.lineTo(vx + 32, vy - 6)
        visor.lineTo(vx + 38, vy + 14)
        visor.lineTo(vx + 10, vy + 18)
        visor.closeSubpath()
        p.drawPath(visor)

        # Inner dark pupil in visor
        p.setBrush(QBrush(QColor(15, 17, 24)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(vx + 20, vy + 5), 4.0, 4.0)

        # 4. Animated Mouth / Jaw Line (glitches when talking)
        mouth_y = h * 0.75 + (self.mouth_offset if self.is_talking else 0)
        p.setPen(QPen(visor_color, 2.0))
        p.drawLine(int(w * 0.55), int(mouth_y), int(w * 0.70), int(mouth_y + 3))

        # 5. Scanlines effect overlay
        p.setPen(QPen(QColor(0, 0, 0, 40), 1.0))
        for y in range(0, h, 3):
            p.drawLine(0, y, w, y)

        # 6. Yellow/Cyan frame border
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor(254, 235, 0), 2.0))
        p.drawRect(1, 1, w - 2, h - 2)
