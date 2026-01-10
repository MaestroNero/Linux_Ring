from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ui.sidebar import Sidebar
from ui.dashboard import Dashboard
from ui.users_view import UsersView
from ui.services_view import ServicesView
from ui.tools_view import ToolsView
from ui.profiles_view import ProfilesView
from ui.processes_view import ProcessesView
from ui.logs_view import LogsView
from ui.updates_view import UpdatesView


class MainWindow(QMainWindow):
    def __init__(self, managers: dict, emitter, logger):
        super().__init__()
        self.managers = managers
        self.logger = logger
        self.emitter = emitter

        self.setWindowTitle("Secure Kali Linux Environment Manager")
        self.resize(1200, 800)

        self._build_ui()
        self.statusBar().showMessage("Ready")

    def _build_ui(self) -> None:
        central = QWidget()
        central_layout = QVBoxLayout(central)
        central_layout.setContentsMargins(0, 0, 0, 0)

        # Top: navigation + stacked views
        content_splitter = QSplitter(Qt.Horizontal)
        self.sidebar = Sidebar(
            [
                "Dashboard",
                "Secure Profiles",
                "Users",
                "Services",
                "Tools",
                "Updates",
                "Processes",
                "Logs",
            ]
        )
        self.sidebar.setMaximumWidth(220)
        self.sidebar.currentRowChanged.connect(self._switch_view)

        self.stack = QStackedWidget()
        self.views = {
            "Dashboard": Dashboard(self.managers),
            "Secure Profiles": ProfilesView(
                self.managers["profiles"], self.managers["firewall"], self.logger
            ),
            "Users": UsersView(self.managers["users"], self.logger),
            "Services": ServicesView(self.managers["services"], self.logger),
            "Tools": ToolsView(
                self.managers["tools"], self.logger, self.emitter.message
            ),
            "Updates": UpdatesView(self.managers["services"], self.logger),
            "Processes": ProcessesView(self.managers["processes"], self.logger),
            "Logs": LogsView(),
        }

        for key in [
            "Dashboard",
            "Secure Profiles",
            "Users",
            "Services",
            "Tools",
            "Updates",
            "Processes",
            "Logs",
        ]:
            self.stack.addWidget(self.views[key])

        content_splitter.addWidget(self.sidebar)
        content_splitter.addWidget(self.stack)
        content_splitter.setStretchFactor(1, 3)

        # Bottom: log panel (dedicated instance to avoid sharing parents)
        self.log_view = LogsView()
        main_splitter = QSplitter(Qt.Vertical)
        main_splitter.addWidget(content_splitter)
        main_splitter.addWidget(self.log_view)
        main_splitter.setStretchFactor(0, 4)
        main_splitter.setStretchFactor(1, 1)

        central_layout.addWidget(main_splitter)
        self.setCentralWidget(central)

    def _switch_view(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        label = self.sidebar.item(index).text()
        self.statusBar().showMessage(f"{label} loaded")
        if label == "Processes":
            self.views["Processes"].refresh()
        elif label == "Services":
            self.views["Services"].refresh()
        elif label == "Users":
            self.views["Users"].refresh()

    def append_log(self, message: str) -> None:
        self.log_view.append_log(message)
        logs_page = self.views.get("Logs")
        if logs_page is not self.log_view:
            logs_page.append_log(message)
