from functools import partial

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class CommandWorker(QThread):
    progress = Signal(str)
    finished = Signal(bool, str)

    def __init__(self, func):
        super().__init__()
        self.func = func

    def run(self) -> None:
        try:
            self.func(self.progress.emit)
            self.finished.emit(True, "")
        except Exception as exc:  # pragma: no cover - defensive
            self.finished.emit(False, str(exc))


class ToolCard(QFrame):
    def __init__(self, tool: dict):
        super().__init__()
        self.tool = tool
        self.setObjectName("Card")
        self.setFrameShape(QFrame.StyledPanel)
        self.setLayout(self._build_layout())
        self.running = False

    def _build_layout(self) -> QVBoxLayout:
        layout = QVBoxLayout()
        header = QHBoxLayout()

        icon_label = QLabel()
        icon_path = self.tool.get("icon")
        if icon_path:
            pixmap = QPixmap(icon_path).scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(pixmap)
        header.addWidget(icon_label)

        title = QLabel(f"<b>{self.tool['name']}</b>")
        header.addWidget(title)
        header.addStretch(1)
        self.status_label = QLabel("Not installed")
        header.addWidget(self.status_label)
        layout.addLayout(header)

        layout.addWidget(QLabel(self.tool["description"]))

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        buttons = QHBoxLayout()
        self.install_btn = QPushButton("Install")
        self.update_btn = QPushButton("Update")
        self.remove_btn = QPushButton("Remove")
        for btn in (self.install_btn, self.update_btn, self.remove_btn):
            buttons.addWidget(btn)
        buttons.addStretch(1)
        layout.addLayout(buttons)
        return layout

    def set_running(self, running: bool, message: str | None = None) -> None:
        self.running = running
        for btn in (self.install_btn, self.update_btn, self.remove_btn):
            btn.setDisabled(running)
        self.progress.setVisible(running)
        self.progress.setRange(0, 0 if running else 1)
        if message:
            self.status_label.setText(message)

    def set_status(self, status: str) -> None:
        self.status_label.setText(status)


class ToolsView(QWidget):
    def __init__(self, installer, logger, log_signal):
        super().__init__()
        self.installer = installer
        self.logger = logger
        self.log_signal = log_signal
        self.cards = {}
        self.workers: list[CommandWorker] = []

        outer = QVBoxLayout(self)
        outer.addWidget(QLabel("<h3>Tools Manager</h3>"))
        outer.addWidget(QLabel("Install, update, and remove security tools with background tasks."))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        self.grid = QGridLayout(container)
        self.grid.setSpacing(12)

        self.tools = [
            {
                "id": "nmap",
                "name": "Nmap",
                "package": "nmap",
                "description": "Network discovery and security auditing.",
                "icon": "",
            },
            {
                "id": "metasploit",
                "name": "Metasploit Framework",
                "package": "metasploit-framework",
                "description": "Penetration testing framework.",
                "icon": "",
            },
            {
                "id": "wireshark",
                "name": "Wireshark",
                "package": "wireshark",
                "description": "Protocol analyzer for traffic inspection.",
                "icon": "",
            },
            {
                "id": "sqlmap",
                "name": "sqlmap",
                "package": "sqlmap",
                "description": "Automated SQL injection tool.",
                "icon": "",
            },
            {
                "id": "john",
                "name": "John the Ripper",
                "package": "john",
                "description": "Password auditing and recovery.",
                "icon": "",
            },
            {
                "id": "aircrack-ng",
                "name": "Aircrack-ng",
                "package": "aircrack-ng",
                "description": "Wireless security assessment suite.",
                "icon": "",
            },
        ]

        for idx, tool in enumerate(self.tools):
            card = ToolCard(tool)
            row, col = divmod(idx, 2)
            self.grid.addWidget(card, row, col)
            card.install_btn.clicked.connect(partial(self._start_task, "install", tool))
            card.update_btn.clicked.connect(partial(self._start_task, "update", tool))
            card.remove_btn.clicked.connect(partial(self._start_task, "remove", tool))
            self.cards[tool["id"]] = card

        container.setLayout(self.grid)
        scroll.setWidget(container)
        outer.addWidget(scroll)
        outer.addStretch(1)

    def _start_task(self, action: str, tool: dict) -> None:
        card = self.cards[tool["id"]]
        action_title = action.capitalize()
        card.set_running(True, f"{action_title} in progress")
        self.logger.info("%s %s...", action_title, tool["name"])

        fn_map = {
            "install": self.installer.install_tool,
            "update": self.installer.update_tool,
            "remove": self.installer.remove_tool,
        }

        worker = CommandWorker(lambda emit: fn_map[action](tool, emit))
        worker.progress.connect(self.log_signal)
        worker.finished.connect(
            partial(self._task_finished, tool=tool, action=action, worker=worker)
        )
        self.workers.append(worker)
        worker.start()

    def _task_finished(self, success: bool, error: str, tool: dict, action: str, worker: CommandWorker) -> None:
        card = self.cards[tool["id"]]
        card.set_running(False)
        try:
            self.workers.remove(worker)
        except ValueError:
            pass

        if success:
            status = f"{tool['name']} {action}ed"
            self.logger.info(status)
            self.log_signal.emit(status)
            card.set_status("Installed" if action != "remove" else "Removed")
        else:
            status = f"{action.capitalize()} failed for {tool['name']}: {error}"
            self.logger.error(status)
            card.set_status("Error")
            self.log_signal.emit(status)
