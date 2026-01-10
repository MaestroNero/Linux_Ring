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

from ui.dialogs import confirm_action


class ServicesView(QWidget):
    headers = ["Service", "Status", "Startup", "Port", "Risk Level"]

    def __init__(self, manager, logger):
        super().__init__()
        self.manager = manager
        self.logger = logger

        layout = QVBoxLayout(self)
        header = QHBoxLayout()
        header.addWidget(QLabel("<h3>Service Management</h3>"))
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh)
        start_btn = QPushButton("Start")
        start_btn.clicked.connect(self.start_service)
        stop_btn = QPushButton("Stop")
        stop_btn.clicked.connect(self.stop_service)
        restart_btn = QPushButton("Restart")
        restart_btn.clicked.connect(self.restart_service)
        for btn in (refresh_btn, start_btn, stop_btn, restart_btn):
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
        services = self.manager.list_services()
        self.table.setRowCount(len(services))
        for row, svc in enumerate(services):
            self.table.setItem(row, 0, QTableWidgetItem(svc.get("name", "")))
            self.table.setItem(row, 1, QTableWidgetItem(svc.get("status", "")))
            self.table.setItem(row, 2, QTableWidgetItem(svc.get("startup", "")))
            self.table.setItem(row, 3, QTableWidgetItem(svc.get("port", "")))
            self.table.setItem(row, 4, QTableWidgetItem(svc.get("risk", "")))
        self.table.resizeColumnsToContents()

    def _selected_service(self) -> str | None:
        row = self.table.currentRow()
        if row < 0:
            return None
        return self.table.item(row, 0).text()

    def start_service(self) -> None:
        svc = self._selected_service()
        if not svc:
            return
        self.manager.start_service(svc)
        self.logger.info("Started service %s", svc)
        self.refresh()

    def stop_service(self) -> None:
        svc = self._selected_service()
        if not svc:
            return
        if not confirm_action(self, "Stop Service", f"Stop {svc}?"):
            return
        self.manager.stop_service(svc)
        self.logger.info("Stopped service %s", svc)
        self.refresh()

    def restart_service(self) -> None:
        svc = self._selected_service()
        if not svc:
            return
        self.manager.restart_service(svc)
        self.logger.info("Restarted service %s", svc)
        self.refresh()
