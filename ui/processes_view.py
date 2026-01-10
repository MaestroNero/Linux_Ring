from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ui.dialogs import confirm_action


class ProcessesView(QWidget):
    headers = ["PID", "Name", "User", "CPU", "Memory", "Status"]

    def __init__(self, manager, logger):
        super().__init__()
        self.manager = manager
        self.logger = logger

        layout = QVBoxLayout(self)
        header = QHBoxLayout()
        header.addWidget(QLabel("<h3>System Processes</h3>"))
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh)
        kill_btn = QPushButton("Terminate")
        kill_btn.clicked.connect(self.terminate)
        for btn in (refresh_btn, kill_btn):
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
        processes = self.manager.list_processes()
        self.table.setRowCount(len(processes))
        for row, proc in enumerate(processes):
            self.table.setItem(row, 0, QTableWidgetItem(str(proc.get("pid", ""))))
            self.table.setItem(row, 1, QTableWidgetItem(proc.get("name", "")))
            self.table.setItem(row, 2, QTableWidgetItem(proc.get("user", "")))
            self.table.setItem(row, 3, QTableWidgetItem(f"{proc.get('cpu', 0):.1f}%"))
            self.table.setItem(row, 4, QTableWidgetItem(f"{proc.get('memory', 0):.1f}%"))
            self.table.setItem(row, 5, QTableWidgetItem(proc.get("status", "")))
        self.table.resizeColumnsToContents()

    def _selected_pid(self) -> int | None:
        row = self.table.currentRow()
        if row < 0:
            return None
        return int(self.table.item(row, 0).text())

    def terminate(self) -> None:
        pid = self._selected_pid()
        if not pid:
            return
        if not confirm_action(self, "Terminate", f"Terminate process {pid}?"):
            return
        try:
            self.manager.terminate_process(pid)
            self.logger.info("Terminated process %s", pid)
            self.refresh()
        except Exception as exc:
            self.logger.error("Terminate failed for %s: %s", pid, exc)
