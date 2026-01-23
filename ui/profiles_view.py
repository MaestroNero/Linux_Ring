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
    QDialogButtonBox,
    QComboBox,
    QMessageBox
)
from ui.dialogs import confirm_action
from core.ghost_manager import GhostManager

class GhostModeCard(QFrame):
    def __init__(self, manager, logger):
        super().__init__()
        self.manager = manager
        self.logger = logger
        self.setFixedSize(320, 240) 
        self.setObjectName("GhostCard") 
        self.setStyleSheet("""
            #GhostCard { 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(139, 92, 246, 0.15),
                    stop:1 rgba(30, 41, 59, 0.9));
                border: 1px solid rgba(139, 92, 246, 0.5);
                border-radius: 16px; 
            }
            #GhostCard:hover {
                border: 1px solid #a855f7;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(168, 85, 247, 0.2),
                    stop:1 rgba(51, 65, 85, 0.9));
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        
        icon_label = QLabel("👻")
        icon_label.setStyleSheet("font-size: 40px; background: transparent;")
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)
        
        title_label = QLabel("Ghost Mode")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #a855f7; background: transparent;")
        layout.addWidget(title_label)
        
        desc_label = QLabel("Anonymize your network identity\nby spoofing MAC address")
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet("color: #94a3b8; font-size: 11px; background: transparent;")
        layout.addWidget(desc_label)

        self.iface_combo = QComboBox()
        self.iface_combo.addItems(self.manager.get_interfaces())
        self.iface_combo.setStyleSheet("""
            QComboBox {
                background-color: rgba(30, 41, 59, 0.8);
                color: #e2e8f0;
                border: 1px solid rgba(168, 85, 247, 0.4);
                border-radius: 6px;
                padding: 8px;
            }
        """)
        layout.addWidget(self.iface_combo)
        
        self.btn = QPushButton("⚡ Enable Ghost Mode")
        self.btn.setCursor(Qt.PointingHandCursor)
        self.btn.clicked.connect(self.toggle_ghost)
        self.btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8b5cf6, stop:1 #a855f7);
                color: white;
                border: none;
                padding: 10px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #a855f7, stop:1 #c084fc);
            }
        """)
        layout.addWidget(self.btn)

    def toggle_ghost(self):
        iface = self.iface_combo.currentText()
        if not iface: return

        if not self.manager.is_ghost_active:
            success, msg = self.manager.enable_ghost_mode(iface)
            if success:
                self.btn.setText("🔓 Disable Ghost Mode")
                self.btn.setStyleSheet("""
                    QPushButton {
                        background: rgba(30, 41, 59, 0.8);
                        color: #a855f7;
                        border: 1px solid #a855f7;
                        padding: 10px;
                        border-radius: 8px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background: rgba(168, 85, 247, 0.2);
                    }
                """)
                QMessageBox.information(self, "Ghost Mode", msg)
            else:
                QMessageBox.critical(self, "Error", msg)
        else:
            success, msg = self.manager.disable_ghost_mode(iface)
            if success:
                self.btn.setText("⚡ Enable Ghost Mode")
                self.btn.setStyleSheet("""
                    QPushButton {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8b5cf6, stop:1 #a855f7);
                        color: white;
                        border: none;
                        padding: 10px;
                        border-radius: 8px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #a855f7, stop:1 #c084fc);
                    }
                """)
                QMessageBox.information(self, "Ghost Mode", msg)
            else:
                 QMessageBox.critical(self, "Error", msg)

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
        except Exception as exc:
            self.finished.emit(False, str(exc))

class ProfilePreviewDialog(QDialog):
    def __init__(self, profile, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Profile: {profile['name']}")
        self.setMinimumSize(650, 450)
        self.setStyleSheet("""
            QDialog {
                background-color: #0f172a;
                color: #e2e8f0;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)
        
        # Header
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 rgba(56, 189, 248, 0.1), 
                    stop:1 rgba(139, 92, 246, 0.1));
                border: 1px solid rgba(56, 189, 248, 0.3);
                border-radius: 12px;
            }
        """)
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 15, 20, 15)
        
        header = QLabel(f"🛡️ {profile['name']}")
        header.setStyleSheet("font-size: 22px; font-weight: bold; color: #38bdf8; background: transparent;")
        header_layout.addWidget(header)
        
        desc = QLabel(profile.get('summary', ''))
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #94a3b8; font-size: 13px; background: transparent;")
        header_layout.addWidget(desc)
        
        layout.addWidget(header_frame)
        
        # Actions table
        actions_label = QLabel("📋 Planned Changes:")
        actions_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #f1f5f9;")
        layout.addWidget(actions_label)
        
        table = QTableWidget(0, 2)
        table.setHorizontalHeaderLabels(["Category", "Action"])
        table.horizontalHeader().setStretchLastSection(True)
        table.verticalHeader().setVisible(False)
        table.setStyleSheet("""
            QTableWidget {
                background-color: rgba(30, 41, 59, 0.6);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                gridline-color: rgba(255, 255, 255, 0.05);
            }
            QTableWidget::item {
                padding: 10px;
                color: #e2e8f0;
            }
            QHeaderView::section {
                background-color: rgba(51, 65, 85, 0.8);
                color: #94a3b8;
                padding: 10px;
                border: none;
                font-weight: bold;
            }
        """)
        
        actions = profile.get("actions", [])
        table.setRowCount(len(actions))
        for idx, action in enumerate(actions):
            cat_item = QTableWidgetItem(action.get("category", ""))
            cat_item.setForeground(Qt.cyan)
            table.setItem(idx, 0, cat_item)
            table.setItem(idx, 1, QTableWidgetItem(action.get("description", "")))
        
        layout.addWidget(table)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: rgba(51, 65, 85, 0.6);
                color: #94a3b8;
                border: 1px solid rgba(255, 255, 255, 0.1);
                padding: 12px 30px;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(71, 85, 105, 0.8);
                color: #f1f5f9;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        apply_btn = QPushButton("✅ Apply Profile")
        apply_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #22c55e, stop:1 #10b981);
                color: white;
                border: none;
                padding: 12px 30px;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10b981, stop:1 #34d399);
            }
        """)
        apply_btn.clicked.connect(self.accept)
        btn_layout.addWidget(apply_btn)
        
        layout.addLayout(btn_layout)

class ProfileCard(QFrame):
    def __init__(self, profile, parent_view):
        super().__init__()
        self.profile = profile
        self.parent_view = parent_view
        self.setFixedSize(320, 200)
        self.setObjectName("ProfileCard")
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            #ProfileCard { 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(30, 41, 59, 0.9),
                    stop:1 rgba(51, 65, 85, 0.7));
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 16px;
            }
            #ProfileCard:hover {
                border: 1px solid rgba(56, 189, 248, 0.5);
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(51, 65, 85, 0.95),
                    stop:1 rgba(71, 85, 105, 0.8));
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(8)
        
        icon_label = QLabel("🛡️")
        icon_label.setStyleSheet("font-size: 36px; background: transparent;")
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)
        
        title_label = QLabel(profile["name"])
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #38bdf8; background: transparent;")
        layout.addWidget(title_label)
        
        summary = profile.get("summary", "")
        if len(summary) > 70:
            summary = summary[:67] + "..."
        desc_label = QLabel(summary)
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet("color: #94a3b8; font-size: 12px; background: transparent;")
        layout.addWidget(desc_label)
        
        layout.addStretch()
        
        btn = QPushButton("🔍 Inspect & Apply")
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(self.on_click)
        btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0ea5e9, stop:1 #38bdf8);
                color: white;
                border: none;
                padding: 10px;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #38bdf8, stop:1 #7dd3fc);
            }
        """)
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
        
        self.ghost_manager = GhostManager(logger)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
        
        # Header
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
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 15, 20, 15)
        
        header = QLabel("🛡️ Secure Environment Profiles")
        header.setStyleSheet("font-size: 20px; font-weight: bold; color: #38bdf8; background: transparent;")
        header_layout.addWidget(header)
        
        subtitle = QLabel("Select a pre-configured security profile to harden your environment")
        subtitle.setStyleSheet("color: #64748b; font-size: 13px; background: transparent;")
        header_layout.addWidget(subtitle)
        
        layout.addWidget(header_frame)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        self.grid_layout = QGridLayout(container)
        self.grid_layout.setSpacing(20)
        self.grid_layout.setContentsMargins(10, 10, 10, 10)
        scroll.setWidget(container)
        
        layout.addWidget(scroll)

        self._load_profiles()

    def _load_profiles(self) -> None:
        if hasattr(self.profile_manager, 'list_profiles'):
             profiles = self.profile_manager.list_profiles()
        else:
             profiles = self.profile_manager.profiles
        
        # Clear existing
        for i in reversed(range(self.grid_layout.count())):
             widget = self.grid_layout.itemAt(i).widget()
             if widget: widget.setParent(None)

        cols = 3
        current_row = 0
        current_col = 0
        
        for profile in profiles:
            card = ProfileCard(profile, self)
            self.grid_layout.addWidget(card, current_row, current_col)
            current_col += 1
            if current_col >= cols:
                current_col = 0
                current_row += 1
                
        # Add Ghost Mode Card
        ghost_card = GhostModeCard(self.ghost_manager, self.logger)
        self.grid_layout.addWidget(ghost_card, current_row, current_col)
            
        # Add stretch
        self.grid_layout.setRowStretch(current_row + 1, 1)

    def open_profile(self, profile):
        dlg = ProfilePreviewDialog(profile, self)
        if dlg.exec():
            self.apply_profile(profile)

    def apply_profile(self, profile) -> None:
        worker = ProfileWorker(
            # Using profile["id"] assuming apply_profile method uses ID
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
