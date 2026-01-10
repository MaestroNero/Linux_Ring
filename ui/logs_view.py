from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QTextEdit, QVBoxLayout, QWidget


class LogsView(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        header = QHBoxLayout()
        header.addWidget(QLabel("<h4>Execution Logs</h4>"))
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear)
        header.addWidget(clear_btn)
        header.addStretch(1)
        layout.addLayout(header)

        self.text = QTextEdit()
        self.text.setReadOnly(True)
        layout.addWidget(self.text)

    def append_log(self, message: str) -> None:
        self.text.append(message)

    def clear(self) -> None:
        self.text.clear()
