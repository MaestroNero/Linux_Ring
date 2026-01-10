from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ui.dialogs import confirm_action, prompt_text


class UsersView(QWidget):
    headers = ["Username", "UID", "Shell", "Status", "Role"]

    def __init__(self, manager, logger):
        super().__init__()
        self.manager = manager
        self.logger = logger

        layout = QVBoxLayout(self)
        header = QHBoxLayout()
        header.addWidget(QLabel("<h3>User Management</h3>"))
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh)
        add_btn = QPushButton("Add User")
        add_btn.clicked.connect(self.add_user)
        del_btn = QPushButton("Remove User")
        del_btn.clicked.connect(self.remove_user)
        for btn in (refresh_btn, add_btn, del_btn):
            header.addWidget(btn)
        header.addStretch(1)
        layout.addLayout(header)

        self.table = QTableWidget(0, len(self.headers))
        self.table.setHorizontalHeaderLabels(self.headers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

        self.refresh()

    def refresh(self) -> None:
        users = self.manager.list_users()
        self.table.setRowCount(len(users))
        for row, user in enumerate(users):
            self.table.setItem(row, 0, QTableWidgetItem(user.get("username", "")))
            self.table.setItem(row, 1, QTableWidgetItem(str(user.get("uid", ""))))
            self.table.setItem(row, 2, QTableWidgetItem(user.get("shell", "")))
            self.table.setItem(row, 3, QTableWidgetItem(user.get("status", "")))
            self.table.setItem(row, 4, QTableWidgetItem(user.get("role", "")))
        self.table.resizeColumnsToContents()

    def add_user(self) -> None:
        username = prompt_text(self, "New User", "Username")
        if not username:
            return
        shell = prompt_text(self, "Shell", "Shell (e.g. /bin/bash)", "/bin/bash")
        if not shell:
            return
        try:
            self.manager.add_user(username, shell)
            self.logger.info("Added user %s", username)
            self.refresh()
        except Exception as exc:
            self.logger.error("Failed to add user %s: %s", username, exc)

    def remove_user(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            return
        username = self.table.item(row, 0).text()
        if not confirm_action(self, "Remove User", f"Delete user {username}?"):
            return
        try:
            self.manager.remove_user(username)
            self.logger.info("Removed user %s", username)
            self.refresh()
        except Exception as exc:
            self.logger.error("Failed to remove user %s: %s", username, exc)
