from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QScrollArea,
    QFrame,
    QGroupBox,
    QGridLayout
)
from PySide6.QtGui import QIcon
from ui.dialogs import confirm_action, prompt_text


class UserCard(QFrame):
    def __init__(self, user: dict, parent_view):
        super().__init__()
        self.user = user
        self.parent_view = parent_view
        self.setObjectName("NeonCard")
        
        self.setFixedSize(260, 160)
        
        # Neon Style
        self.setStyleSheet("""
            #NeonCard {
                background-color: #001f27;
                border: 2px solid #2aa198;
                border-radius: 12px;
            }
            #NeonCard:hover {
                background-color: #073642;
                border: 2px solid #268bd2;
                
            }
            QLabel {
                color: #fdf6e3;
                font-family: 'Segoe UI', sans-serif;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        
        # Header: Icon + Username
        header = QHBoxLayout()
        icon_label = QLabel("👤") 
        icon_label.setStyleSheet("font-size: 26px; color: #2aa198;")
        header.addWidget(icon_label)
        
        name_label = QLabel(user["username"])
        name_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #ffffff;")
        header.addWidget(name_label)
        header.addStretch()
        
        # Status Dot
        status = user.get("status", "Active")
        color = "#859900" if status == "Active" else "#dc322f"
        status_dot = QLabel("●")
        status_dot.setStyleSheet(f"color: {color}; font-size: 14px; text-shadow: 0 0 5px {color};")
        header.addWidget(status_dot)
        
        layout.addLayout(header)
        
        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background-color: #586e75;")
        layout.addWidget(sep)

        # Details
        info_layout = QGridLayout()
        info_layout.setSpacing(2)
        
        user_role = user['role']
        role_color = "#d33682" if "Admin" in user_role or "Root" in user_role else "#268bd2"
        role_lbl = QLabel(user_role)
        role_lbl.setStyleSheet(f"color: {role_color}; font-weight: bold; font-size: 12px;")
        
        uid_val = QLabel(str(user['uid']))
        uid_val.setStyleSheet("color: #93a1a1;")
        
        shell_val = QLabel(user['shell'])
        shell_val.setStyleSheet("color: #859900; font-family: monospace; font-size: 11px;")
        
        info_layout.addWidget(QLabel("Role:"), 0, 0)
        info_layout.addWidget(role_lbl, 0, 1)
        info_layout.addWidget(QLabel("UID:"), 1, 0)
        info_layout.addWidget(uid_val, 1, 1)
        info_layout.addWidget(QLabel("Shell:"), 2, 0)
        info_layout.addWidget(shell_val, 2, 1)
        
        layout.addLayout(info_layout)
        
        layout.addStretch()

        # Actions
        actions = QHBoxLayout()
        btn_del = QPushButton("Delete")
        btn_del.setCursor(Qt.PointingHandCursor)
        btn_del.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #dc322f;
                color: #dc322f;
                border-radius: 6px;
                padding: 4px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #dc322f;
                color: white;
            }
        """)
        btn_del.clicked.connect(self.on_delete)
        
        if user["uid"] < 1000:
             btn_del.setEnabled(False)
             btn_del.setStyleSheet("border: 1px solid #002b36; color: #586e75;")

        actions.addStretch()
        actions.addWidget(btn_del)
        layout.addLayout(actions)

    def on_delete(self):
        self.parent_view.remove_user(self.user["username"])


class UsersView(QWidget):
    def __init__(self, manager, logger):
        super().__init__()
        self.manager = manager
        self.logger = logger
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("<h2>User Management</h2>")
        title.setStyleSheet("color: #2aa198; text-shadow: 0 0 10px #2aa198;")
        header.addWidget(title)
        
        header.addStretch()
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.clicked.connect(self.refresh)
        
        add_btn = QPushButton("+ Add User")
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #268bd2; 
                color: white; 
                font-weight: bold; 
                padding: 6px 15px; 
                border-radius: 4px;
                border: none;
            }
            QPushButton:hover { background-color: #2aa198; box-shadow: 0 0 10px #2aa198; }
        """)
        add_btn.clicked.connect(self.add_user)
        
        header.addWidget(refresh_btn)
        header.addWidget(add_btn)
        layout.addLayout(header)
        
        layout.addSpacing(20)

        # Content Area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setAlignment(Qt.AlignTop)
        
        self.scroll.setWidget(self.content_widget)
        layout.addWidget(self.scroll)

        self.refresh()

    def refresh(self) -> None:
        # Clear previous items
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
                
        try:
            users = self.manager.list_users()
            
            # Group Users
            admins = [u for u in users if "Admin" in u['role'] or "Root" in u['role']]
            others = [u for u in users if u not in admins]

            if admins:
                self.add_section("Administrators", admins)
            if others:
                self.add_section("Standard & System Users", others)
                
            self.content_layout.addStretch()
            
        except Exception as e:
            self.logger.error(f"Failed to list users: {e}")
            self.content_layout.addWidget(QLabel(f"Error: {e}"))

    def add_section(self, title, user_list):
        group = QGroupBox(title)
        group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 16px; margin-top: 20px; color: #268bd2; border: none; } QGroupBox::title { subcontrol-origin: margin; left: 0px; padding: 0 3px 0 3px; }")
        
        # Grid Layout for Cards
        from PySide6.QtWidgets import QGridLayout # Local import to ensure availability
        grid = QGridLayout(group)
        grid.setSpacing(20)
        
        cols = 3 # Cards per row
        for i, user in enumerate(user_list):
            card = UserCard(user, self)
            grid.addWidget(card, i // cols, i % cols)
            
        self.content_layout.addWidget(group)

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
            QMessageBox.critical(self, "Error", f"Failed to add user: {exc}")

    def remove_user(self, username: str) -> None:
        if not confirm_action(self, "Remove User", f"Are you sure you want to PERMANENTLY delete user '{username}'?"):
            return
        try:
            self.manager.remove_user(username)
            self.logger.info("Removed user %s", username)
            self.refresh()
        except Exception as exc:
            self.logger.error("Failed to remove user %s: %s", username, exc)
            QMessageBox.critical(self, "Error", f"Failed to remove user: {exc}")

