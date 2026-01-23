from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
    QLabel,
    QStatusBar,
)
import psutil
import os

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

        self.setWindowTitle("Linux Ring By Maestro Nero")
        self.resize(1200, 800)
        self.setMinimumSize(1000, 700) # Ensure layout integrity

        self._build_ui()
        self._setup_status_bar()

    def _setup_status_bar(self):
        """Create professional status bar with system info"""
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        
        # User info
        user = os.environ.get("USER", "root")
        is_root = os.geteuid() == 0
        user_icon = "🔐" if is_root else "👤"
        self.user_label = QLabel(f"{user_icon} {user}")
        self.user_label.setStyleSheet("color: #38bdf8; font-weight: bold; padding: 0 10px;")
        
        # CPU indicator
        self.cpu_label = QLabel("CPU: --%")
        self.cpu_label.setStyleSheet("color: #94a3b8; padding: 0 10px;")
        
        # RAM indicator
        self.ram_label = QLabel("RAM: --%")
        self.ram_label.setStyleSheet("color: #94a3b8; padding: 0 10px;")
        
        # Version
        version_label = QLabel("v1.0.0")
        version_label.setStyleSheet("color: #64748b; padding: 0 10px;")
        
        status_bar.addWidget(self.user_label)
        status_bar.addWidget(self.cpu_label)
        status_bar.addWidget(self.ram_label)
        status_bar.addPermanentWidget(version_label)
        
        status_bar.showMessage("✨ Ready", 3000)
        
        # Update timer
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self._update_status_bar)
        self.status_timer.start(2000)
        self._update_status_bar()
    
    def _update_status_bar(self):
        """Update CPU/RAM in status bar"""
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory().percent
        
        cpu_color = "#22c55e" if cpu < 50 else "#eab308" if cpu < 80 else "#ef4444"
        ram_color = "#22c55e" if mem < 50 else "#eab308" if mem < 80 else "#ef4444"
        
        self.cpu_label.setText(f"CPU: {cpu:.0f}%")
        self.cpu_label.setStyleSheet(f"color: {cpu_color}; padding: 0 10px;")
        
        self.ram_label.setText(f"RAM: {mem:.0f}%")
        self.ram_label.setStyleSheet(f"color: {ram_color}; padding: 0 10px;")

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



