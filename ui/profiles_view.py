from functools import partial

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
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


class ProfilesView(QWidget):
    def __init__(self, profile_manager, firewall_manager, logger):
        super().__init__()
        self.profile_manager = profile_manager
        self.firewall_manager = firewall_manager
        self.logger = logger
        self.workers: list[ProfileWorker] = []

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<h3>Secure Environment Profiles</h3>"))
        layout.addWidget(
            QLabel(
                "Preview hardening steps, confirm, and apply profiles with progress feedback."
            )
        )

        content = QHBoxLayout()
        self.profile_list = QListWidget()
        self.profile_list.currentRowChanged.connect(self._on_profile_selected)
        content.addWidget(self.profile_list, 1)

        right = QVBoxLayout()
        self.preview_table = QTableWidget(0, 2)
        self.preview_table.setHorizontalHeaderLabels(["Category", "Action"])
        self.preview_table.horizontalHeader().setStretchLastSection(True)
        right.addWidget(self.preview_table, 4)

        self.apply_btn = QPushButton("Apply Profile")
        self.apply_btn.clicked.connect(self.apply_profile)
        right.addWidget(self.apply_btn)
        content.addLayout(right, 3)
        layout.addLayout(content)

        self._load_profiles()

    def _load_profiles(self) -> None:
        self.profiles = self.profile_manager.list_profiles()
        self.profile_list.clear()
        for profile in self.profiles:
            item = QListWidgetItem(profile["name"])
            item.setData(Qt.UserRole, profile["id"])
            item.setToolTip(profile["summary"])
            self.profile_list.addItem(item)
        if self.profiles:
            self.profile_list.setCurrentRow(0)

    def _on_profile_selected(self, row: int) -> None:
        if row < 0 or row >= len(self.profiles):
            return
        profile = self.profiles[row]
        actions = profile.get("actions", [])
        self.preview_table.setRowCount(len(actions))
        for idx, action in enumerate(actions):
            self.preview_table.setItem(idx, 0, QTableWidgetItem(action.get("category", "")))
            self.preview_table.setItem(idx, 1, QTableWidgetItem(action.get("description", "")))
        self.preview_table.resizeColumnsToContents()

    def apply_profile(self) -> None:
        row = self.profile_list.currentRow()
        if row < 0:
            return
        profile = self.profiles[row]
        if not confirm_action(
            self, "Apply Profile", f"Apply '{profile['name']}' profile with listed changes?"
        ):
            return
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
            self.logger.info("Profile '%s' applied", profile["name"])
        else:
            self.logger.error("Profile '%s' failed: %s", profile["name"], error)
