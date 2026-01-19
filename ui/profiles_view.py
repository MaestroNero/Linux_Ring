from functools import partial
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QGridLayout,
    QFrame,
    QScrollArea,
    QDialog,
    QDialogButtonBox
)
from ui.dialogs import confirm_action


class ProfileWorker(QThread):
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


class ProfilePreviewDialog(QDialog):
    def __init__(self, profile, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Profile: {profile['name']}")
        self.setMinimumSize(600, 400)
        self.setStyleSheet("background-color: #1a1a1a; color: #e0e0e0;")
        
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel(f"<h2>{profile['name']}</h2>")
        header.setStyleSheet("color: #268bd2;")
        layout.addWidget(header)
        
        desc = QLabel(f"<i>{profile.get('summary', '')}</i>")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        layout.addWidget(QLabel("<b>Planned Changes:</b>"))
        
        # Table
        table = QTableWidget(0, 2)
        table.setHorizontalHeaderLabels(["Category", "Action"])
        table.horizontalHeader().setStretchLastSection(True)
        table.verticalHeader().setVisible(False)
        
        actions = profile.get("actions", [])
        table.setRowCount(len(actions))
        for idx, action in enumerate(actions):
            table.setItem(idx, 0, QTableWidgetItem(action.get("category", "")))
            table.setItem(idx, 1, QTableWidgetItem(action.get("description", "")))
        
        layout.addWidget(table)
        
        # Buttons
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setText("Apply Profile")
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)


class ProfileCard(QFrame):
    def __init__(self, profile, parent_view):
        super().__init__()
        self.profile = profile
        self.parent_view = parent_view
        self.setFixedSize(300, 180)
        self.setObjectName("Card") # Styled in CSS
        
        layout = QVBoxLayout(self)
        
        # Icon
        icon_label = QLabel("🛡️")
        icon_label.setStyleSheet("font-size: 32px;")
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)
        
        # Title
        title_label = QLabel(profile["name"])
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #268bd2;")
        layout.addWidget(title_label)
        
        # Summary
        summary = profile.get("summary", "")
        # Truncate
        if len(summary) > 60:
            summary = summary[:57] + "..."
        desc_label = QLabel(summary)
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet("color: #aaa; font-size: 12px;")
        layout.addWidget(desc_label)
        
        layout.addStretch()
        
        # Action
        btn = QPushButton("Inspect & Apply")
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(self.on_click)
        layout.addWidget(btn)

    def on_click(self):
        self.parent_view.open_profile(self.profile)


class ProfilesView(QWidget):
    def __init__(self, profile_manager, firewall_manager, logger):
        super().__init__()
        self.profile_manager = profile_manager
        self.firewall_manager = firewall_manager
        self.logger = logger
        self.workers: list[ProfileWorker] = []

        layout = QVBoxLayout(self)
        
        header = QLabel("<h3>Secure Environment Profiles</h3>")
        header.setStyleSheet("color: #268bd2;")
        layout.addWidget(header)
        layout.addWidget(
            QLabel("Select a pre-configured security profile to harden your environment.")
        )

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        container = QWidget()
        self.grid_layout = QGridLayout(container)
        self.grid_layout.setSpacing(20)
        scroll.setWidget(container)
        
        layout.addWidget(scroll)

        self._load_profiles()

    def _load_profiles(self) -> None:
        profiles = self.profile_manager.list_profiles()
        
        # Clear existing
        for i in reversed(range(self.grid_layout.count())):
             self.grid_layout.itemAt(i).widget().setParent(None)

        cols = 3
        for i, profile in enumerate(profiles):
            card = ProfileCard(profile, self)
            self.grid_layout.addWidget(card, i // cols, i % cols)
            
        # Add stretch to fill empty space if few profiles
        row_count = (len(profiles) + cols - 1) // cols
        self.grid_layout.setRowStretch(row_count, 1)

    def open_profile(self, profile):
        dlg = ProfilePreviewDialog(profile, self)
        if dlg.exec():
            self.apply_profile(profile)

    def apply_profile(self, profile) -> None:
        # Confirmation happens in Dialog "Apply" button implicitly, but we can double check or just proceed
        # since it is "Ok" button on a Dialog explicitly showing changes.
        worker = ProfileWorker(
            lambda emit: self.profile_manager.apply_profile(profile["id"], emit)
        )
        worker.progress.connect(self.logger.info)
        worker.finished.connect(partial(self._on_finished, profile=profile, worker=worker))
        self.workers.append(worker)
        worker.start()

    def _on_finished(self, success: bool, error: str, profile: dict, worker: ProfileWorker) -> None:
        try:
            self.workers.remove(worker)
        except ValueError:
            pass
        if success:
            self.logger.info("Profile '%s' applied successfully", profile["name"])
        else:
            self.logger.error("Profile '%s' failed: %s", profile["name"], error)

