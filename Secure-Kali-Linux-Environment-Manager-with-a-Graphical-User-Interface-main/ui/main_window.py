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
from ui.system_view import SystemView
from ui.tools_view import ToolsView
from ui.profiles_view import ProfilesView
from ui.logs_view import LogsView
from ui.updates_view import UpdatesView
from ui.terminal import TerminalWidget
from ui.about_view import AboutView
from ui.task_queue_view import TaskQueueView
from core.task_queue import TaskQueueManager


class MainWindow(QMainWindow):
    def __init__(self, managers: dict, emitter, logger):
        super().__init__()
        self.managers = managers
        self.logger = logger
        self.emitter = emitter
        
        # Create Task Queue Manager
        self.task_queue = TaskQueueManager()

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
                "System Monitor",
                "Users",
                "Tools",
                "Updates",
                "Terminal",
                "Logs",
                "About Developer",
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
            "System Monitor": SystemView(
                self.managers["services"], self.managers["processes"], self.logger
            ),
            "Users": UsersView(self.managers["users"], self.logger),
            "Tools": ToolsView(
                self.managers["tools"], self.logger, self.emitter.message
            ),
            "Updates": UpdatesView(self.managers["tools"], self.logger, self.task_queue),
            "Terminal": TerminalWidget(),
            "Logs": LogsView(),
            "About Developer": AboutView(),
        }

        for key in [
            "Dashboard",
            "Secure Profiles",
            "System Monitor",
            "Users",
            "Tools",
            "Updates",
            "Terminal",
            "Logs",
            "About Developer",
        ]:
            self.stack.addWidget(self.views[key])

        content_splitter.addWidget(self.sidebar)
        content_splitter.addWidget(self.stack)
        content_splitter.setStretchFactor(1, 3)

        # Bottom: log panel (dedicated instance to avoid sharing parents)
        self.log_view = LogsView()
        # The original main_splitter is replaced by a new structure
        # that includes the task queue view.
        # The content_splitter's stretch factors are also adjusted here.
        content_splitter.setStretchFactor(0, 0) # Adjust sidebar stretch
        content_splitter.setStretchFactor(1, 1) # Adjust stack stretch

        # Vertical splitter for main content + task queue
        main_splitter = QSplitter(Qt.Vertical)
        main_splitter.addWidget(content_splitter)
        
        # Task Queue Panel
        self.task_queue_view = TaskQueueView(self.task_queue)
        self.task_queue_view.setMinimumHeight(180)
        self.task_queue_view.setMaximumHeight(300)
        main_splitter.addWidget(self.task_queue_view)
        main_splitter.setStretchFactor(0, 5)
        main_splitter.setStretchFactor(1, 1)

        central_layout.addWidget(main_splitter)

        self.setCentralWidget(central)

    def _switch_view(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        label = self.sidebar.item(index).text()
        self.statusBar().showMessage(f"{label} loaded")
        # Refresh logic is now auto-handled by SystemView timers, 
        # but manual refresh for Users still valid
        if label == "Users":
            self.views["Users"].refresh()

    def append_log(self, message: str) -> None:
        self.log_view.append_log(message)
        logs_page = self.views.get("Logs")
        if logs_page is not self.log_view:
            logs_page.append_log(message)



