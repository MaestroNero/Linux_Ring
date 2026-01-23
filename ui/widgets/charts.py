from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QBrush, QColor, QPen, QLinearGradient, QPainterPath

class CPUChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(180)
        self.history = [0] * 60  # Store last 60 data points
        self.accent_color = QColor("#38bdf8")  # Cyan Blue
        self.bg_color = QColor(0, 0, 0, 0) # Transparent

    def update_value(self, value):
        self.history.append(value)
        self.history.pop(0)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Background
        painter.fillRect(self.rect(), self.bg_color)

        width = self.width()
        height = self.height()
        padding = 10

        # Draw Grid Lines with subtle glow
        pen_grid = QPen(QColor(255, 255, 255, 15))
        pen_grid.setStyle(Qt.DotLine)
        painter.setPen(pen_grid)
        for i in range(1, 5):
            y = int(height * i / 5)
            painter.drawLine(padding, y, width - padding, y)
        
        # Draw percentage labels
        painter.setPen(QColor(100, 116, 139))
        font = painter.font()
        font.setPixelSize(9)
        painter.setFont(font)
        for i, pct in enumerate([100, 75, 50, 25, 0]):
            y = int(height * (100 - pct) / 100)
            painter.drawText(2, y + 3, f"{pct}%")

        # Build Path
        path = QPainterPath()
        # Start at first data point
        step_x = (width - padding * 2) / (len(self.history) - 1)

        first_y = height - (self.history[0] / 100.0 * (height - padding))
        path.moveTo(padding, first_y)

        for i, val in enumerate(self.history[1:], 1):
            x = padding + i * step_x
            y = height - (val / 100.0 * (height - padding))
            path.lineTo(x, y)

        # Close path for fill
        fill_path = QPainterPath(path)
        fill_path.lineTo(width - padding, height)
        fill_path.lineTo(padding, height)
        fill_path.closeSubpath()

        # Gradient Fill
        grad = QLinearGradient(0, 0, 0, height)
        color_top = QColor(self.accent_color)
        color_top.setAlpha(100)
        color_mid = QColor(self.accent_color)
        color_mid.setAlpha(30)
        color_bottom = QColor(self.accent_color)
        color_bottom.setAlpha(5)
        grad.setColorAt(0, color_top)
        grad.setColorAt(0.5, color_mid)
        grad.setColorAt(1, color_bottom)
        
        painter.fillPath(fill_path, QBrush(grad))

        # Stroke Line with glow effect
        glow_pen = QPen(QColor(56, 189, 248, 40))
        glow_pen.setWidth(6)
        glow_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(glow_pen)
        painter.drawPath(path)
        
        # Main line
        pen_line = QPen(self.accent_color)
        pen_line.setWidth(2)
        pen_line.setCapStyle(Qt.RoundCap)
        painter.setPen(pen_line)
        painter.drawPath(path)
        
        # Draw current value dot
        if self.history:
            last_x = width - padding
            last_y = height - (self.history[-1] / 100.0 * (height - padding))
            painter.setBrush(self.accent_color)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(int(last_x) - 4, int(last_y) - 4, 8, 8)


class CircularGauge(QWidget):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setMinimumSize(130, 130)
        self.value = 0
        self.title = title
        self.color = QColor("#38bdf8") # Sky Blue

    def set_value(self, val):
        self.value = val
        self.update()

    def set_color(self, hex_color):
        self.color = QColor(hex_color)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()
        side = min(width, height)
        
        painter.translate(width / 2, height / 2)
        painter.scale(side / 110.0, side / 110.0)

        # Outer glow effect
        glow_color = QColor(self.color)
        glow_color.setAlpha(30)
        pen_glow = QPen(glow_color)
        pen_glow.setWidth(14)
        pen_glow.setCapStyle(Qt.RoundCap)
        painter.setPen(pen_glow)
        span_angle = int((self.value / 100.0) * 270 * 16)
        start_angle = 225 * 16
        painter.drawArc(-42, -42, 84, 84, start_angle, -span_angle)

        # Background Arc
        pen_bg = QPen(QColor(255, 255, 255, 20))
        pen_bg.setWidth(10)
        pen_bg.setCapStyle(Qt.RoundCap)
        painter.setPen(pen_bg)
        painter.drawArc(-40, -40, 80, 80, -45 * 16, 270 * 16)

        # Value Arc with gradient
        pen_val = QPen(self.color)
        pen_val.setWidth(10)
        pen_val.setCapStyle(Qt.RoundCap)
        painter.setPen(pen_val)
        painter.drawArc(-40, -40, 80, 80, start_angle, -span_angle)

        # Inner circle for text
        painter.setPen(Qt.NoPen)
        inner_bg = QColor(15, 23, 42, 200)
        painter.setBrush(inner_bg)
        painter.drawEllipse(-30, -30, 60, 60)

        # Value Text
        painter.setPen(QColor(241, 245, 249))
        font = painter.font()
        font.setPixelSize(16)
        font.setBold(True)
        painter.setFont(font)
        
        text_val = f"{int(self.value)}%"
        rect_val = painter.fontMetrics().boundingRect(text_val)
        painter.drawText(-rect_val.width() / 2, 5, text_val)

        # Title
        painter.setPen(QColor(148, 163, 184))
        font.setPixelSize(9)
        font.setBold(False)
        painter.setFont(font)
        rect_title = painter.fontMetrics().boundingRect(self.title)
        painter.drawText(-rect_title.width() / 2, 18, self.title)
