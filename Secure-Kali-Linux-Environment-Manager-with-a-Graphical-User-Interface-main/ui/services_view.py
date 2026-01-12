from PySide6.QtCore import Qt, QTimer
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
        layout.setContentsMargins(0, 10, 0, 0)
        
        # Action Bar (No Title, No Refresh - handled by auto/parent)
        action_bar = QHBoxLayout()
        
        start_btn = QPushButton("Start")
        start_btn.clicked.connect(self.start_service)
        start_btn.setStyleSheet("background-color: #859900; color: white;") # Green
        
        stop_btn = QPushButton("Stop")
        stop_btn.clicked.connect(self.stop_service)
        stop_btn.setStyleSheet("background-color: #dc322f; color: white;") # Red
        
        restart_btn = QPushButton("Restart")
        restart_btn.clicked.connect(self.restart_service)
        
        for btn in (start_btn, stop_btn, restart_btn):
            action_bar.addWidget(btn)
        action_bar.addStretch(1)
        layout.addLayout(action_bar)

        self.table = QTableWidget(0, len(self.headers))
        self.table.setHorizontalHeaderLabels(self.headers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet("""
            QTableWidget { 
                background-color: #001f27;
                alternate-background-color: #073642;
                gridline-color: #0d6f7c;
                color: #eee8d5;
                border: 2px solid #0d6f7c;
                border-radius: 6px;
            }
            QHeaderView::section {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #073642, stop:1 #001f27
                );
                color: #2aa198;
                font-weight: bold;
                font-size: 13px;
                border: none;
                padding: 8px;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #0a4f5c;
                color: #ffffff;
            }
        """)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)
        
        # Auto Refresh
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(5000) # 5s auto refresh

        self.refresh()

    def refresh(self) -> None:
        try:
            services = self.manager.list_services()
            self.table.setRowCount(len(services))
            for row, svc in enumerate(services):
                self.table.setItem(row, 0, QTableWidgetItem(svc.get("name", "")))
                self.table.setItem(row, 1, QTableWidgetItem(svc.get("status", "")))
                self.table.setItem(row, 2, QTableWidgetItem(svc.get("startup", "")))
                self.table.setItem(row, 3, QTableWidgetItem(svc.get("port", "")))
                self.table.setItem(row, 4, QTableWidgetItem(svc.get("risk", "")))
            self.table.resizeColumnsToContents()
        except Exception as e:
            self.logger.error(f"Service refresh failed: {e}")

    def _selected_service(self) -> str | None:
        row = self.table.currentRow()
        if row < 0:
            return None
        return self.table.item(row, 0).text()

    def start_service(self) -> None:
        svc = self._selected_service()
        if not svc:
            return
        try:
            self.manager.start_service(svc)
            self.logger.info("Started service %s", svc)
            self.refresh()
        except Exception as e:
             self.logger.error(f"Failed to start {svc}: {e}")

    def stop_service(self) -> None:
        svc = self._selected_service()
        if not svc:
            return
        if not confirm_action(self, "Stop Service", f"Stop {svc}?"):
            return
        try:
            self.manager.stop_service(svc)
            self.logger.info("Stopped service %s", svc)
            self.refresh()
        except Exception as e:
             self.logger.error(f"Failed to stop {svc}: {e}")

    def restart_service(self) -> None:
        svc = self._selected_service()
        if not svc:
            return
        try:
            self.manager.restart_service(svc)
            self.logger.info("Restarted service %s", svc)
            self.refresh()
        except Exception as e:
             self.logger.error(f"Failed to restart {svc}: {e}")
