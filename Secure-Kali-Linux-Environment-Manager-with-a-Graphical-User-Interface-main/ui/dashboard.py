import platform
import shutil
import psutil
from PySide6.QtWidgets import (
    QLabel, QGridLayout, QGroupBox, QVBoxLayout, QWidget, QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar
)
from PySide6.QtCore import QTimer, Qt

from ui.widgets.charts import CPUChart, CircularGauge


class SecurityScoreWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        header = QHBoxLayout()
        header.addWidget(QLabel("<b>Security Health Score</b>"))
        self.score_lbl = QLabel("Calculating...")
        self.score_lbl.setStyleSheet("font-weight: bold; font-size: 14px;")
        header.addWidget(self.score_lbl)
        header.addStretch()
        layout.addLayout(header)
        
        self.bar = QProgressBar()
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(8)
        self.bar.setStyleSheet("QProgressBar::chunk { background-color: #859900; border-radius: 4px; } QProgressBar { background-color: #073642; border: none; border-radius: 4px; }")
        layout.addWidget(self.bar)
        
        self.details = QLabel("Analysis pending...")
        self.details.setStyleSheet("color: #93a1a1; font-size: 11px;")
        layout.addWidget(self.details)
        
    def update_score(self):
        score = 100
        issues = []
        
        # simple checks
        if psutil.users():
            # Check if root is logged in (simplified)
            for user in psutil.users():
                if user.name == 'root':
                    score -= 20
                    issues.append("Root user logged in")
                    break
        
        # Check sshd (example)
        if 22 in [c.laddr.port for c in psutil.net_connections(kind='inet') if c.status == 'LISTEN']:
             issues.append("SSH Service exposed")
             score -= 10

        self.bar.setValue(score)
        color = "#859900" if score > 80 else "#b58900" if score > 50 else "#dc322f"
        self.bar.setStyleSheet(f"QProgressBar::chunk {{ background-color: {color}; border-radius: 4px; }} QProgressBar {{ background-color: #073642; border: none; border-radius: 4px; }}")
        
        self.score_lbl.setText(f"{score}/100")
        self.score_lbl.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 14px;")
        
        if issues:
            self.details.setText("Issues: " + ", ".join(issues))
        else:
            self.details.setText("System appears healthy.")


class NetworkTable(QTableWidget):
    def __init__(self):
        super().__init__(0, 6) # Added Process Name column
        self.setHorizontalHeaderLabels(["Proto", "Local Address", "Remote Address", "Status", "PID", "Process"])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.verticalHeader().setVisible(False)
        self.setStyleSheet("QTableWidget { border: none; background-color: #073642; gridline-color: #586e75; } QHeaderView::section { background-color: #002b36; color: #268bd2; }")
        self.setAlternatingRowColors(True)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        
    def update_conns(self):
        try:
            # If not root, this might raise AccessDenied for some, or return limited list
            conns = psutil.net_connections(kind='inet')
            
            # Filter for ESTABLISHED/LISTEN and sort by PID
            filtered = [c for c in conns if c.status in ('ESTABLISHED', 'LISTEN')]
            filtered.sort(key=lambda x: x.pid)
            filtered = filtered[:30] # Limit to top 30
            
            self.setRowCount(len(filtered))
            
            if not filtered:
                # If validly empty, nothing to do, but if it's because of permissions?
                # We can't easily validly detect empty vs permission denied on listing unless exception raised.
                # But usually net_connections returns *something* (like 127.0.0.1 listeners).
                pass

            for row, c in enumerate(filtered):
                proto = "TCP" if c.type == 1 else "UDP"
                laddr = f"{c.laddr.ip}:{c.laddr.port}"
                raddr = f"{c.raddr.ip}:{c.raddr.port}" if c.raddr else "*"
                
                proc_name = "?"
                if c.pid:
                    try:
                        proc = psutil.Process(c.pid)
                        proc_name = proc.name()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass

                self.setItem(row, 0, QTableWidgetItem(proto))
                self.setItem(row, 1, QTableWidgetItem(laddr))
                self.setItem(row, 2, QTableWidgetItem(raddr))
                self.setItem(row, 3, QTableWidgetItem(c.status))
                self.setItem(row, 4, QTableWidgetItem(str(c.pid) if c.pid else "-"))
                self.setItem(row, 5, QTableWidgetItem(proc_name))
                
        except psutil.AccessDenied:
            self.setRowCount(1)
            item = QTableWidgetItem("Run as Root to view connections")
            item.setForeground(Qt.red)
            self.setItem(0, 0, item)
            self.setSpan(0, 0, 1, 6)
        except Exception:
            self.setRowCount(0)


class Dashboard(QWidget):
    def __init__(self, managers: dict):
        super().__init__()
        self.process_manager = managers.get("processes")
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(20)

        # Header with Security Score
        header_layout = QHBoxLayout()
        
        title_box = QVBoxLayout()
        title = QLabel("<h1>System Overview</h1>")
        title.setStyleSheet("color: #268bd2; font-weight: bold; margin-bottom: 0px;") 
        title_box.addWidget(title)
        
        self.lbl_sysinfo = QLabel("Loading system info...")
        self.lbl_sysinfo.setStyleSheet("color: #888; font-size: 14px;")
        title_box.addWidget(self.lbl_sysinfo)
        header_layout.addLayout(title_box)
        
        header_layout.addStretch()
        
        # Security Score Widget (Top Right)
        score_box = QGroupBox() # No title, just container
        score_box.setStyleSheet("QGroupBox { border: 1px solid #333; border-radius: 8px; background-color: #002b36; }")
        score_layout = QVBoxLayout(score_box)
        self.security_score = SecurityScoreWidget()
        score_layout.addWidget(self.security_score)
        score_box.setFixedWidth(300)
        header_layout.addWidget(score_box)
        
        self.layout.addLayout(header_layout)

        # Top Row: Gauges
        gauge_box = QGroupBox("Resource Usage")
        gauge_box.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #333; border-radius: 8px; margin-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }")
        gauge_layout = QHBoxLayout(gauge_box)
        
        self.cpu_gauge = CircularGauge("CPU")
        self.cpu_gauge.set_color("#00f0ff") # Cyan
        
        self.ram_gauge = CircularGauge("RAM")
        self.ram_gauge.set_color("#d33682") # Magenta
        
        self.disk_gauge = CircularGauge("DISK")
        self.disk_gauge.set_color("#859900") # Green

        gauge_layout.addStretch()
        gauge_layout.addWidget(self.cpu_gauge)
        gauge_layout.addStretch()
        gauge_layout.addWidget(self.ram_gauge)
        gauge_layout.addStretch()
        gauge_layout.addWidget(self.disk_gauge)
        gauge_layout.addStretch()
        
        self.layout.addWidget(gauge_box)

        # Middle Row: Graphs & Network
        mid_layout = QHBoxLayout()
        
        # CPU Chart
        graph_box = QGroupBox("CPU History")
        graph_box.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #333; border-radius: 8px; margin-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }")
        graph_layout = QVBoxLayout(graph_box)
        self.cpu_chart = CPUChart()
        graph_layout.addWidget(self.cpu_chart)
        mid_layout.addWidget(graph_box, 1)
        
        self.layout.addLayout(mid_layout)
        self.layout.addStretch()

        # Update Timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(2000) # 2 sec refresh

        self.update_sysinfo()

    def update_sysinfo(self):
        uname = platform.uname()
        info_str = f"{uname.system} {uname.release} | {uname.machine}"
        self.lbl_sysinfo.setText(info_str)

    def update_stats(self):
        # CPU
        cpu_percent = psutil.cpu_percent()
        self.cpu_gauge.set_value(cpu_percent)
        self.cpu_chart.update_value(cpu_percent)

        # Memory
        mem = psutil.virtual_memory()
        self.ram_gauge.set_value(mem.percent)

        # Disk
        disk = shutil.disk_usage("/")
        disk_percent = (disk.used / disk.total) * 100
        self.disk_gauge.set_value(disk_percent)
        
        # Score
        # Score
        self.security_score.update_score()
