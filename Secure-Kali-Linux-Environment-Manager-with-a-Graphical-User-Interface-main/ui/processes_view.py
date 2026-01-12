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


class ProcessesView(QWidget):
    headers = ["PID", "Name", "User", "CPU", "Memory", "Status"]

    def __init__(self, manager, logger):
        super().__init__()
        self.manager = manager
        self.logger = logger

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 0)
        
        # Action Bar
        action_bar = QHBoxLayout()
        kill_btn = QPushButton("Terminate Process")
        kill_btn.clicked.connect(self.terminate)
        kill_btn.setStyleSheet("background-color: #dc322f; color: white;")
        
        action_bar.addStretch(1)
        action_bar.addWidget(kill_btn)
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
        self.timer.start(3000) # 3s auto refresh for processes

        self.refresh()

    def refresh(self) -> None:
        try:
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
        except Exception as e:
            self.logger.error(f"Process refresh failed: {e}")

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
