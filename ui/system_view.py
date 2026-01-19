from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QVBoxLayout,
    QWidget,
    QTabWidget,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QPushButton,
    QHBoxLayout
)
import psutil
import subprocess
import re
from ui.services_view import ServicesView
from ui.processes_view import ProcessesView


class NetworkTable(QTableWidget):
    def __init__(self):
        super().__init__()
        self.setColumnCount(6)
        self.setHorizontalHeaderLabels([
            "Proto", "Local Address", "Remote Address", "Status", "PID", "Process"
        ])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.verticalHeader().setVisible(False)
        self.setStyleSheet("""
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
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setAlternatingRowColors(True)

    def update_data(self):
        self.setRowCount(0)
        
        # Method 1: Try psutil (preferred)
        # Note: On many Linuxes, psutil.net_connections() returns [] for non-root users
        # or raises AccessDenied.
        try:
            conns = psutil.net_connections(kind='inet')
        except psutil.AccessDenied:
            conns = []

        if conns:
            self._fill_from_psutil(conns)
        else:
            # Method 2: Fallback to ss (Socket Stat)
            self._fill_from_ss()
            
    def _fill_from_psutil(self, conns):
        # Implementation similar to previous dashboard
        self.setRowCount(len(conns))
        for row, c in enumerate(conns):
            # ... fill ...
            # Code reusing existing logic in briefer form
            proto = "tcp" if c.type == 1 else "udp"
            laddr = f"{c.laddr.ip}:{c.laddr.port}"
            raddr = f"{c.raddr.ip}:{c.raddr.port}" if c.raddr else "*"
            
            proc_name = "?"
            if c.pid:
                try:
                    p = psutil.Process(c.pid)
                    proc_name = p.name()
                except:
                    pass

            self.setItem(row, 0, QTableWidgetItem(proto))
            self.setItem(row, 1, QTableWidgetItem(laddr))
            self.setItem(row, 2, QTableWidgetItem(raddr))
            self.setItem(row, 3, QTableWidgetItem(c.status))
            self.setItem(row, 4, QTableWidgetItem(str(c.pid) or "-"))
            self.setItem(row, 5, QTableWidgetItem(proc_name))

    def _fill_from_ss(self):
        # specific command: ss -tunap (tcp, udp, numeric, all, processes)
        # Check if we can run it. Standard users might not see PIDs of others, but will see their own.
        try:
            res = subprocess.run(["ss", "-tunapH"], capture_output=True, text=True) # H for no header
            lines = res.stdout.strip().split('\n')
            
            rows_data = []
            
            for line in lines:
                parts = line.split()
                if len(parts) < 5:
                    continue
                
                # Format: Netid State Recv-Q Send-Q Local_Address:Port Peer_Address:Port Process
                # Example: tcp ESTAB 0 0 10.0.0.1:443 1.1.1.1:53 users:(("chrome",pid=123,fd=4))
                
                proto = parts[0]
                state = parts[1]
                local = parts[4]
                peer = parts[5]
                process_info = parts[6] if len(parts) > 6 else "-"
                
                pid = "-"
                pname = "-"
                
                # Parse users:(("name",pid=123,fd=4))
                if "users:" in line:
                    try:
                        match = re.search(r'users:\(\("([^"]+)",pid=(\d+)', line)
                        if match:
                            pname = match.group(1)
                            pid = match.group(2)
                    except:
                        pass
                
                rows_data.append((proto, local, peer, state, pid, pname))
            
            self.setRowCount(len(rows_data))
            for row, data in enumerate(rows_data):
                for col, val in enumerate(data):
                    self.setItem(row, col, QTableWidgetItem(str(val)))
                    
        except Exception as e:
            self.setRowCount(1)
            self.setItem(0, 0, QTableWidgetItem(f"Failed to load network data: {e}"))


class SystemView(QWidget):
    """
    Unified System Monitor combining Services and Processes management.
    """
    def __init__(self, service_manager, process_manager, logger):
        super().__init__()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 0)
        
        # Header with Refresh
        header = QHBoxLayout()
        title = QLabel("<h2>System Monitor</h2>")
        title.setStyleSheet("color: #268bd2;")
        header.addWidget(title)
        header.addStretch()
        refresh_btn = QPushButton("Refresh Data")
        refresh_btn.clicked.connect(self.refresh_all)
        header.addWidget(refresh_btn)
        layout.addLayout(header)
        
        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #073642; top: -1px; }
            QTabBar::tab { background: #002b36; color: #839496; padding: 8px 20px; border-top-left-radius: 4px; border-top-right-radius: 4px; }
            QTabBar::tab:selected { background: #073642; color: #268bd2; font-weight: bold; }
        """)
        
        self.services_view = ServicesView(service_manager, logger)
        self.processes_view = ProcessesView(process_manager, logger)
        
        self.tabs.addTab(self.services_view, "Services")
        self.tabs.addTab(self.processes_view, "Processes")
        
        # Network Tab
        self.network_table = NetworkTable()
        self.tabs.addTab(self.network_table, "Network Connections")
        
        layout.addWidget(self.tabs)

        # Auto-refresh Timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_all)
        self.timer.start(5000) # 5 seconds
        
        # Initial Load
        self.refresh_all()

    def refresh_all(self):
        self.services_view.refresh()
        self.processes_view.refresh()
        self.network_table.update_data()
