import platform
import shutil
import psutil
import subprocess
from PySide6.QtWidgets import (
    QLabel, QGridLayout, QGroupBox, QVBoxLayout, QWidget, QHBoxLayout, 
    QProgressBar, QPushButton, QFrame, QScrollArea
)
from PySide6.QtCore import QTimer, Qt, QThread, Signal
from PySide6.QtGui import QFont

from ui.widgets.charts import CPUChart, CircularGauge
from core.security_auditor import SecurityAuditor


class AuditWorker(QThread):
    finished = Signal(int, list, list)

    def __init__(self, auditor):
        super().__init__()
        self.auditor = auditor

    def run(self):
        score, issues, notes = self.auditor.scan_system()
        self.finished.emit(score, issues, notes)


class SecurityScoreWidget(QWidget):
    issues_signal = Signal(list)  # Signal to pass issues to parent
    
    def __init__(self):
        super().__init__()
        self.auditor = SecurityAuditor(None)
        self.worker = None
        self.current_issues = []
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # Header row
        header = QHBoxLayout()
        title = QLabel("🛡️ Security")
        title.setStyleSheet("font-weight: bold; font-size: 13px; color: #38bdf8; background: transparent; border: none;")
        header.addWidget(title)
        header.addStretch()
        
        self.score_lbl = QLabel("--")
        self.score_lbl.setStyleSheet("font-weight: bold; font-size: 24px; color: #22c55e; background: transparent; border: none;")
        header.addWidget(self.score_lbl)
        layout.addLayout(header)
        
        # Progress bar
        self.bar = QProgressBar()
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(8)
        self.bar.setRange(0, 100)
        self.bar.setStyleSheet("""
            QProgressBar::chunk { 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #22c55e, stop:1 #38bdf8); 
                border-radius: 4px; 
            } 
            QProgressBar { 
                background-color: rgba(255, 255, 255, 0.1); 
                border: none; 
                border-radius: 4px; 
            }
        """)
        layout.addWidget(self.bar)
        
        # Details label
        self.details = QLabel("Click to scan...")
        self.details.setStyleSheet("color: #94a3b8; font-size: 11px; background: transparent; border: none;")
        self.details.setWordWrap(True)
        self.details.setCursor(Qt.PointingHandCursor)
        layout.addWidget(self.details)
        
    def mousePressEvent(self, event):
        self.update_score()
        super().mousePressEvent(event)
        
    def update_score(self):
        if self.worker and self.worker.isRunning():
            return
        self.details.setText("⏳ Scanning...")
        self.worker = AuditWorker(self.auditor)
        self.worker.finished.connect(self._on_audit_finished)
        self.worker.start()

    def _on_audit_finished(self, score, issues, notes):
        self.current_issues = issues
        self.bar.setValue(score)
        color = "#22c55e" if score > 80 else "#eab308" if score > 50 else "#ef4444"
        self.score_lbl.setText(f"{score}")
        self.score_lbl.setStyleSheet(f"font-weight: bold; font-size: 24px; color: {color}; background: transparent; border: none;")
        
        if issues:
            self.details.setText(f"⚠️ {len(issues)} issues - Click for details")
            self.details.setStyleSheet("color: #fbbf24; font-size: 11px; background: transparent; border: none;")
            # Create tooltip with all issues
            tooltip_text = "Security Issues Found:\n" + "\n".join([f"• {issue}" for issue in issues[:10]])
            if len(issues) > 10:
                tooltip_text += f"\n... and {len(issues) - 10} more"
            self.details.setToolTip(tooltip_text)
        else:
            self.details.setText("✅ System is secure")
            self.details.setStyleSheet("color: #22c55e; font-size: 11px; background: transparent; border: none;")
            self.details.setToolTip("No security issues detected")


class QuickActionCard(QFrame):
    """Modern action button card"""
    clicked = Signal()
    
    def __init__(self, icon: str, title: str, subtitle: str, color: str = "#38bdf8"):
        super().__init__()
        self.color = color
        self.setObjectName("QuickActionCard")
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(90)
        self.setStyleSheet(f"""
            #QuickActionCard {{
                background-color: rgba(30, 41, 59, 0.8);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
            }}
            #QuickActionCard:hover {{
                background-color: rgba(51, 65, 85, 0.9);
                border: 1px solid {color};
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        
        # Icon
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet(f"font-size: 32px; color: {color}; background: transparent;")
        layout.addWidget(icon_lbl)
        
        # Text
        text_box = QVBoxLayout()
        text_box.setSpacing(2)
        
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"font-size: 14px; font-weight: bold; color: #f1f5f9; background: transparent;")
        text_box.addWidget(title_lbl)
        
        sub_lbl = QLabel(subtitle)
        sub_lbl.setStyleSheet("font-size: 11px; color: #64748b; background: transparent;")
        text_box.addWidget(sub_lbl)
        
        layout.addLayout(text_box)
        layout.addStretch()
        
        # Arrow
        arrow = QLabel("→")
        arrow.setStyleSheet(f"font-size: 18px; color: {color}; background: transparent;")
        layout.addWidget(arrow)

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


class ActivityItem(QFrame):
    """Single activity log item"""
    def __init__(self, icon: str, message: str, time: str):
        super().__init__()
        self.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border-bottom: 1px solid rgba(255, 255, 255, 0.05);
                padding: 5px;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 8, 5, 8)
        
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 16px;")
        layout.addWidget(icon_lbl)
        
        msg_lbl = QLabel(message)
        msg_lbl.setStyleSheet("color: #cbd5e1; font-size: 12px;")
        layout.addWidget(msg_lbl)
        
        layout.addStretch()
        
        time_lbl = QLabel(time)
        time_lbl.setStyleSheet("color: #64748b; font-size: 10px;")
        layout.addWidget(time_lbl)


class Dashboard(QWidget):
    def __init__(self, managers: dict):
        super().__init__()
        self.managers = managers
        self.process_manager = managers.get("processes")
        self.firewall_manager = managers.get("firewall")
        
        self._build_ui()
        
        # Update Timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(3000)
        
        QTimer.singleShot(500, self.update_stats)

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(20)

        # === HEADER ===
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 rgba(30, 41, 59, 0.8), 
                    stop:1 rgba(51, 65, 85, 0.6));
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 16px;
            }
        """)
        header = QHBoxLayout(header_frame)
        header.setContentsMargins(20, 15, 20, 15)
        
        # Logo + Welcome text
        welcome_box = QHBoxLayout()
        welcome_box.setSpacing(15)
        
        logo = QLabel("💎")
        logo.setStyleSheet("font-size: 36px;")
        welcome_box.addWidget(logo)
        
        text_box = QVBoxLayout()
        text_box.setSpacing(3)
        
        greeting = QLabel("Linux Ring")
        greeting.setStyleSheet("""
            font-size: 22px; 
            font-weight: bold; 
            color: #f1f5f9;
            background: transparent;
        """)
        text_box.addWidget(greeting)
        
        self.lbl_sysinfo = QLabel("Loading...")
        self.lbl_sysinfo.setStyleSheet("font-size: 12px; color: #64748b; background: transparent;")
        text_box.addWidget(self.lbl_sysinfo)
        
        welcome_box.addLayout(text_box)
        header.addLayout(welcome_box)
        header.addStretch()
        
        # Security Score (compact)
        self.security_score = SecurityScoreWidget()
        self.security_score.setFixedWidth(240)
        self.security_score.setStyleSheet("""
            background-color: rgba(15, 23, 42, 0.6);
            border: 1px solid rgba(56, 189, 248, 0.3);
            border-radius: 12px;
        """)
        header.addWidget(self.security_score)
        
        main_layout.addWidget(header_frame)

        # === MAIN CONTENT (2 columns) ===
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)
        
        # LEFT COLUMN: Gauges + Chart
        left_col = QVBoxLayout()
        left_col.setSpacing(15)
        
        # Resource Gauges
        gauge_frame = QFrame()
        gauge_frame.setObjectName("GlassPanel")
        gauge_frame.setStyleSheet("""
            #GlassPanel {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(30, 41, 59, 0.7),
                    stop:1 rgba(15, 23, 42, 0.8));
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 16px;
            }
        """)
        gauge_layout_wrapper = QVBoxLayout(gauge_frame)
        gauge_layout_wrapper.setContentsMargins(15, 10, 15, 15)
        
        gauge_title = QLabel("📈 System Resources")
        gauge_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #38bdf8; margin-bottom: 5px;")
        gauge_layout_wrapper.addWidget(gauge_title)
        
        gauge_layout = QHBoxLayout()
        gauge_layout.setContentsMargins(10, 10, 10, 10)
        
        self.cpu_gauge = CircularGauge("CPU")
        self.cpu_gauge.set_color("#38bdf8")
        
        self.ram_gauge = CircularGauge("RAM")
        self.ram_gauge.set_color("#a855f7")
        
        self.disk_gauge = CircularGauge("DISK")
        self.disk_gauge.set_color("#22c55e")

        gauge_layout.addStretch()
        gauge_layout.addWidget(self.cpu_gauge)
        gauge_layout.addStretch()
        gauge_layout.addWidget(self.ram_gauge)
        gauge_layout.addStretch()
        gauge_layout.addWidget(self.disk_gauge)
        gauge_layout.addStretch()
        
        gauge_layout_wrapper.addLayout(gauge_layout)
        left_col.addWidget(gauge_frame)
        
        # CPU Chart
        chart_frame = QFrame()
        chart_frame.setObjectName("GlassPanel")
        chart_frame.setStyleSheet("""
            #GlassPanel {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(30, 41, 59, 0.7),
                    stop:1 rgba(15, 23, 42, 0.8));
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 16px;
            }
        """)
        chart_layout = QVBoxLayout(chart_frame)
        chart_layout.setContentsMargins(15, 15, 15, 15)
        
        chart_title = QLabel("📊 CPU Activity")
        chart_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #38bdf8;")
        chart_layout.addWidget(chart_title)
        
        self.cpu_chart = CPUChart()
        chart_layout.addWidget(self.cpu_chart)
        
        left_col.addWidget(chart_frame)
        
        content_layout.addLayout(left_col, 3)
        
        # RIGHT COLUMN: Quick Actions + Activity
        right_col = QVBoxLayout()
        right_col.setSpacing(15)
        
        # Quick Actions Title
        actions_title = QLabel("⚡ Quick Actions")
        actions_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #f1f5f9;")
        right_col.addWidget(actions_title)
        
        # Action Cards
        self.firewall_card = QuickActionCard("🔥", "Firewall", "Toggle protection", "#f97316")
        self.firewall_card.clicked.connect(self._toggle_firewall)
        right_col.addWidget(self.firewall_card)
        
        scan_card = QuickActionCard("🔍", "Security Scan", "Check vulnerabilities", "#22c55e")
        scan_card.clicked.connect(self._run_scan)
        right_col.addWidget(scan_card)
        
        update_card = QuickActionCard("🔄", "Check Updates", "System packages", "#38bdf8")
        update_card.clicked.connect(self._check_updates)
        right_col.addWidget(update_card)
        
        # Activity Feed
        activity_title = QLabel("📋 Recent Activity")
        activity_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #f1f5f9; margin-top: 10px;")
        right_col.addWidget(activity_title)
        
        activity_frame = QFrame()
        activity_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(30, 41, 59, 0.6);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
            }
        """)
        activity_frame.setMinimumHeight(180)
        
        activity_outer = QVBoxLayout(activity_frame)
        activity_outer.setContentsMargins(0, 0, 0, 0)
        
        # Scrollable activity area
        activity_scroll = QScrollArea()
        activity_scroll.setWidgetResizable(True)
        activity_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 6px;
            }
            QScrollBar::handle:vertical {
                background: rgba(56, 189, 248, 0.3);
                border-radius: 3px;
            }
        """)
        
        activity_widget = QWidget()
        activity_widget.setStyleSheet("background: transparent;")
        self.activity_container = QVBoxLayout(activity_widget)
        self.activity_container.setContentsMargins(10, 10, 10, 10)
        self.activity_container.setSpacing(2)
        self.activity_container.addStretch()
        
        activity_scroll.setWidget(activity_widget)
        activity_outer.addWidget(activity_scroll)
        
        right_col.addWidget(activity_frame)
        right_col.addStretch()
        
        content_layout.addLayout(right_col, 2)
        
        main_layout.addLayout(content_layout)
        
        # Initial activity
        self._add_activity("🚀", "Dashboard loaded", "just now")
        self._update_sysinfo()
        
        # Start security scan
        QTimer.singleShot(1000, self.security_score.update_score)

    def _add_activity(self, icon: str, message: str, time: str):
        # Remove stretch if exists (it's at the end)
        count = self.activity_container.count()
        if count > 0:
            last_item = self.activity_container.itemAt(count - 1)
            if last_item and last_item.spacerItem():
                self.activity_container.takeAt(count - 1)
        
        # Limit to 15 items for scroll
        while self.activity_container.count() >= 15:
            item = self.activity_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        activity = ActivityItem(icon, message, time)
        self.activity_container.addWidget(activity)
        
        # Add stretch back at the end
        self.activity_container.addStretch()

    def _update_sysinfo(self):
        uname = platform.uname()
        uptime = ""
        try:
            with open("/proc/uptime", "r") as f:
                uptime_sec = float(f.read().split()[0])
                hours = int(uptime_sec // 3600)
                mins = int((uptime_sec % 3600) // 60)
                uptime = f" • Uptime: {hours}h {mins}m"
        except:
            pass
        self.lbl_sysinfo.setText(f"{uname.system} {uname.release}{uptime}")

    def _toggle_firewall(self):
        if self.firewall_manager:
            try:
                if self.firewall_manager.is_active():
                    self.firewall_manager.disable()
                    self._add_activity("🔥", "Firewall disabled", "now")
                else:
                    self.firewall_manager.enable()
                    self._add_activity("🛡️", "Firewall enabled", "now")
            except Exception as e:
                self._add_activity("❌", f"Firewall error: {str(e)[:30]}", "now")
                print(f"Firewall error: {e}")
        else:
            self._add_activity("⚠️", "UFW not installed", "now")

    def _run_scan(self):
        self._add_activity("🔍", "Security scan started", "now")
        self.security_score.update_score()

    def _check_updates(self):
        self._add_activity("🔄", "Checking for updates...", "now")
        # Run apt update in background
        import subprocess
        import threading
        def check():
            try:
                import os
                if os.geteuid() == 0:
                    result = subprocess.run(["apt-get", "update", "-qq"], capture_output=True, text=True, timeout=60)
                    result2 = subprocess.run(["apt", "list", "--upgradable"], capture_output=True, text=True, timeout=30)
                else:
                    result = subprocess.run(["sudo", "apt-get", "update", "-qq"], capture_output=True, text=True, timeout=60)
                    result2 = subprocess.run(["apt", "list", "--upgradable"], capture_output=True, text=True, timeout=30)
                
                lines = [l for l in result2.stdout.strip().split('\n') if l and 'Listing' not in l]
                count = len(lines)
                if count > 0:
                    self._add_activity("📦", f"{count} updates available", "now")
                else:
                    self._add_activity("✅", "System is up to date", "now")
            except Exception as e:
                self._add_activity("❌", f"Update check failed", "now")
        
        threading.Thread(target=check, daemon=True).start()

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
        
        # Update sysinfo periodically
        self._update_sysinfo()
