from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QBrush, QColor, QPen, QLinearGradient, QPainterPath

class CPUChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(150)
        self.history = [0] * 60  # Store last 60 data points
        self.accent_color = QColor("#8b5cf6")  # Neon Purple
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

        # Draw Grid Lines
        pen_grid = QPen(QColor(60, 60, 60))
        pen_grid.setStyle(Qt.DotLine)
        painter.setPen(pen_grid)
        for i in range(1, 4):
            y = int(height * i / 4)
            painter.drawLine(0, y, width, y)

        # Build Path
        path = QPainterPath()
        # Start bottom-left
        path.moveTo(0, height)
        
        step_x = width / (len(self.history) - 1)

        for i, val in enumerate(self.history):
            x = i * step_x
            # val is 0..100 -> height..0
            y = height - (val / 100.0 * height)
            path.lineTo(x, y)

        # Close path for fill
        fill_path = QPainterPath(path)
        fill_path.lineTo(width, height)
        fill_path.lineTo(0, height)

        # Gradient Fill
        grad = QLinearGradient(0, 0, 0, height)
        color_top = QColor(self.accent_color)
        color_top.setAlpha(150)
        color_bottom = QColor(self.accent_color)
        color_bottom.setAlpha(10)
        grad.setColorAt(0, color_top)
        grad.setColorAt(1, color_bottom)
        
        painter.fillPath(fill_path, QBrush(grad))

        # Stroke Line
        pen_line = QPen(self.accent_color)
        pen_line.setWidth(2)
        painter.setPen(pen_line)
        painter.drawPath(path)


class CircularGauge(QWidget):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setMinimumSize(120, 120)
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
        painter.scale(side / 100.0, side / 100.0)

        # Background Arc
        pen_bg = QPen(QColor(255, 255, 255, 30))
        pen_bg.setWidth(8)
        pen_bg.setCapStyle(Qt.RoundCap)
        painter.setPen(pen_bg)
        painter.drawArc(-40, -40, 80, 80, -45 * 16, 270 * 16)

        # Value Arc
        pen_val = QPen(self.color)
        pen_val.setWidth(8)
        pen_val.setCapStyle(Qt.RoundCap)
        painter.setPen(pen_val)
        
        # 0 to 100 maps to 0 to 270 degrees
        span_angle = int((self.value / 100.0) * 270 * 16)
        start_angle = 225 * 16 # Start at bottom left/225deg
        painter.drawArc(-40, -40, 80, 80, start_angle, -span_angle)

        # Text
        painter.setPen(QColor(220, 220, 220))
        font = painter.font()
        font.setPixelSize(14)
        font.setBold(True)
        painter.setFont(font)
        
        text_val = f"{int(self.value)}%"
        rect_val = painter.fontMetrics().boundingRect(text_val)
        painter.drawText(-rect_val.width() / 2, 5, text_val)

        font.setPixelSize(8)
        font.setBold(False)
        painter.setFont(font)
        rect_title = painter.fontMetrics().boundingRect(self.title)
        painter.drawText(-rect_title.width() / 2, 20, self.title)
