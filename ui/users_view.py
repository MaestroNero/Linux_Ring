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
    QGridLayout,
    QMessageBox,
    QDialog,
    QCheckBox,
    QDialogButtonBox,
    QLineEdit,
    QTabWidget
)
from PySide6.QtGui import QIcon
from ui.dialogs import confirm_action, prompt_text


class ManageUserDialog(QDialog):
    def __init__(self, username, current_groups, user_info, parent_view, parent=None):
        """
        Comprehensive User Management Dialog
        - Tabs: Permissions (Groups), Security (Password), Danger Zone (Delete)
        """
        super().__init__(parent)
        self.setWindowTitle(f"Manage User: {username}")
        self.setFixedSize(600, 500)
        self.username = username
        self.parent_view = parent_view
        self.user_info = user_info
        
        # State tracking for groups
        self.current_groups = set(current_groups)
        self.groups_to_add = set()
        self.groups_to_remove = set()
        
        main_layout = QVBoxLayout(self)
        
        # Header
        header = QHBoxLayout()
        lbl_icon = QLabel("👤")
        lbl_icon.setStyleSheet("font-size: 40px;")
        header.addWidget(lbl_icon)
        
        lbl_name = QLabel(f"<h2>{username}</h2>")
        header.addWidget(lbl_name)
        header.addStretch()
        main_layout.addLayout(header)

        # Tabs
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # --- TAB 1: PRIVILEGES (Groups) ---
        self.tab_groups = QWidget()
        self._init_groups_tab()
        self.tabs.addTab(self.tab_groups, "Privileges")
        
        # --- TAB 2: SECURITY (Password) ---
        self.tab_security = QWidget()
        self._init_security_tab()
        self.tabs.addTab(self.tab_security, "Security")
        
        # --- TAB 3: DANGER ZONE ---
        self.tab_danger = QWidget()
        self._init_danger_tab()
        self.tabs.addTab(self.tab_danger, "Danger Zone")

        # Footer Actions
        footer = QHBoxLayout()
        self.btn_save = QPushButton("Save Changes")
        self.btn_save.setProperty("class", "primary")
        self.btn_save.clicked.connect(self.save_changes)
        
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.reject)
        
        footer.addStretch()
        footer.addWidget(btn_close)
        footer.addWidget(self.btn_save)
        main_layout.addLayout(footer)

    def _init_groups_tab(self):
        layout = QVBoxLayout(self.tab_groups)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Show Current Groups explicitly
        current_str = ", ".join(sorted(self.current_groups)) if self.current_groups else "None"
        lbl_current = QLabel(f"<b>Current Groups:</b> {current_str}")
        lbl_current.setWordWrap(True)
        lbl_current.setStyleSheet("color: #cfd8dc; font-size: 13px; padding: 5px; background: rgba(255,255,255,0.05); border-radius: 4px;")
        layout.addWidget(lbl_current)

        layout.addWidget(QLabel("<b>Manage User Groups & Permissions</b>"))
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        g_layout = QGridLayout(container)
        
        # Common powerful groups in Linux/Kali
        common_groups = [
            "sudo", "root", "adm", "docker", "plugdev", "netdev", 
            "wireshark", "kali-trusted", "video", "audio", "disk"
        ]
        
        self.group_checkboxes = {}
        row, col = 0, 0
        for grp in common_groups:
            chk = QCheckBox(grp)
            self.group_checkboxes[grp] = chk
            
            if grp in self.current_groups:
                chk.setChecked(True)
                chk.setStyleSheet("color: #00bcd4; font-weight: bold;")
            
            # chk.stateChanged.connect(...) # No longer needed, calculation on save
            g_layout.addWidget(chk, row, col)
            
            col += 1
            if col > 2:
                col = 0
                row += 1
                
        scroll.setWidget(container)
        layout.addWidget(scroll)

    # _on_group_change removed effectively by not connecting signal

    def _init_security_tab(self):
        layout = QVBoxLayout(self.tab_security)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        layout.addWidget(QLabel("<b>Change Password</b>"))
        
        self.pass1 = QLineEdit()
        self.pass1.setPlaceholderText("New Password")
        self.pass1.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.pass1)
        
        self.pass2 = QLineEdit()
        self.pass2.setPlaceholderText("Confirm Password")
        self.pass2.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.pass2)
        
        layout.addStretch()
        
        self.lbl_sec_status = QLabel("Enter new password to update.")
        self.lbl_sec_status.setStyleSheet("color: #888;")
        layout.addWidget(self.lbl_sec_status)

    def _init_danger_tab(self):
        layout = QVBoxLayout(self.tab_danger)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        warn_box = QGroupBox("Warning")
        w_layout = QVBoxLayout(warn_box)
        w_layout.addWidget(QLabel("Deleting a user is irreversible. All their files may be lost."))
        layout.addWidget(warn_box)
        
        btn_del = QPushButton("Delete User Permanently")
        btn_del.setProperty("class", "danger")
        if self.user_info.get('uid', 1001) < 1000:
             btn_del.setEnabled(False)
             btn_del.setText("Cannot delete system user (UID < 1000)")
        
        btn_del.clicked.connect(self._handle_delete)
        layout.addWidget(btn_del)
        layout.addStretch()

    def _handle_delete(self):
        confirm = QMessageBox.question(
            self, "Confirm Deletion", 
            f"Are you sure you want to delete user {self.username}?\nThis cannot be undone.",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            # Pass skip_confirm=True to avoid double dialog
            self.parent_view.remove_user(self.username, skip_confirm=True)
            self.reject() # Close dialog

    def save_changes(self):
        # 1. Process Password
        p1 = self.pass1.text()
        p2 = self.pass2.text()
        if p1:
            if p1 != p2:
                QMessageBox.warning(self, "Error", "Passwords do not match.")
                return
            if len(p1) < 4:
                QMessageBox.warning(self, "Error", "Password too short.")
                return
            
            # Call parent view method which calls manager
            self.parent_view.manager.change_password(self.username, p1)
            self.parent_view.logger.info(f"Password update requested for {self.username}")

        # 2. Process Groups
        # Calculate changes based on final checkbox states
        final_groups_to_add = set()
        final_groups_to_remove = set()
        
        for grp, chk in self.group_checkboxes.items():
            if chk.isChecked():
                if grp not in self.current_groups:
                    final_groups_to_add.add(grp)
            else:
                if grp in self.current_groups:
                    final_groups_to_remove.add(grp)
        
        if final_groups_to_add or final_groups_to_remove:
            success = self.parent_view.apply_group_changes(
                self.username, final_groups_to_add, final_groups_to_remove
            )
            if not success:
                return # Error message handled in apply_group_changes
            else:
                # Crucial Step: Warn user about logout
                QMessageBox.warning(
                    self, 
                    "Log Out Required", 
                    "Permissions updated successfully.\n\n"
                    "⚠ NOTE: The user must LOG OUT and LOG BACK IN for these changes to take effect!"
                )
                
        # QMessageBox.information(self, "Success", "User settings updated successfully.")
        self.accept()


# Replaced older dialog classes with ManageUserDialog

class UserCard(QFrame):
    def __init__(self, user: dict, parent_view):
        super().__init__()
        self.user = user
        self.parent_view = parent_view
        self.setObjectName("ToolCard") # Use shared card style
        
        self.setFixedSize(300, 220) 

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Header: Icon + Username
        header = QHBoxLayout()
        icon_label = QLabel("👤") 
        icon_label.setStyleSheet("font-size: 32px; color: #00bcd4; background: transparent;")
        header.addWidget(icon_label)
        
        name_layout = QVBoxLayout()
        name_label = QLabel(user["username"])
        name_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #ffffff; background: transparent;")
        
        role_label = QLabel(user.get('role', 'User'))
        role_label.setStyleSheet("font-size: 12px; color: #888888; background: transparent;")
        
        name_layout.addWidget(name_label)
        name_layout.addWidget(role_label)
        header.addLayout(name_layout)
        header.addStretch()
        
        layout.addLayout(header)
        
        # Details
        info_layout = QGridLayout()
        info_layout.setSpacing(5)
        
        uid_val = QLabel(str(user['uid']))
        uid_val.setStyleSheet("color: #bbbbbb; background: transparent;")
        
        shell_val = QLabel(user['shell'])
        shell_val.setStyleSheet("color: #888888; font-family: monospace; font-size: 11px; background: transparent;")
        shell_val.setToolTip(user['shell'])
        
        info_layout.addWidget(QLabel("UID:"), 0, 0)
        info_layout.addWidget(uid_val, 0, 1)
        info_layout.addWidget(QLabel("Shell:"), 1, 0)
        info_layout.addWidget(shell_val, 1, 1)
        
        layout.addLayout(info_layout)
        layout.addStretch()

        # Actions - Single "Manage" Button
        self.btn_manage = QPushButton("Manage Settings")
        self.btn_manage.setCursor(Qt.PointingHandCursor)
        self.btn_manage.setProperty("class", "primary") # Black text on cyan
        self.btn_manage.clicked.connect(self.on_manage)
        
        layout.addWidget(self.btn_manage)

    def on_manage(self):
        self.parent_view.open_manage_dialog(self.user)


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
        # Global QSS handles color, but override for specifics if needed
        header.addWidget(title)
        
        header.addStretch()
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.clicked.connect(self.refresh)
        
        add_btn = QPushButton("+ Add User")
        add_btn.setCursor(Qt.PointingHandCursor)
        # Using QSS class or global style preferred to inline
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
        # Style handled by QSS
        
        from PySide6.QtWidgets import QGridLayout 
        grid = QGridLayout(group)
        grid.setSpacing(15)
        
        # Determine cols based on list size for now, ideally strictly width based.
        # Fixed 3 is okay for desktop, but let's make it a bit dynamic if list is short
        cols = 3
        
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
            
            # UX Improvement: Ask to configure immediately
            reply = QMessageBox.question(
                self, 
                "User Created", 
                f"User '{username}' created successfully.\nDo you want to set a password and permissions now?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # Need to fetch fresh info. Since list_users parsed it, let's find it.
                # Or just construct a basic info dict since we know username/shell.
                # Better to get it from manager to get UID etc.
                users = self.manager.list_users()
                user_info = next((u for u in users if u['username'] == username), None)
                if user_info:
                    self.open_manage_dialog(user_info)
                
        except Exception as exc:
            self.logger.error("Failed to add user %s: %s", username, exc)
            QMessageBox.critical(self, "Error", f"Failed to add user: {exc}")

    def open_manage_dialog(self, user_info: dict) -> None:
        """Opens the comprehensive management dialog."""
        username = user_info['username']
        try:
            current_groups = self.manager.get_user_groups(username)
            dlg = ManageUserDialog(username, current_groups, user_info, self)
            if dlg.exec():
                self.refresh()
        except Exception as e:
            self.logger.error(f"Failed to open manage dialog for {username}: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load user details: {e}")

    def apply_group_changes(self, username: str, to_add: set, to_remove: set) -> bool:
        """Helper to apply group changes from dialog."""
        try:
            for grp in to_add:
                self.manager.add_user_to_group(username, grp)
                self.logger.info(f"Added {username} to {grp}")
            
            for grp in to_remove:
                self.manager.remove_user_from_group(username, grp)
                self.logger.info(f"Removed {username} from {grp}")
            return True
        except Exception as e:
            self.logger.error(f"Group update failed for {username}: {e}")
            QMessageBox.critical(self, "Error", f"Failed to update groups: {e}")
            return False

    def remove_user(self, username: str, skip_confirm: bool = False) -> None:
        if not skip_confirm:
            if not confirm_action(self, "Remove User", f"Are you sure you want to PERMANENTLY delete user '{username}'?"):
                return
        try:
            self.manager.remove_user(username)
            self.logger.info("Removed user %s", username)
            self.refresh()
        except Exception as exc:
            self.logger.error("Failed to remove user %s: %s", username, exc)
            QMessageBox.critical(self, "Error", f"Failed to remove user: {exc}")




    def change_password(self, username: str) -> None:
        """Opens dialog to change password."""
        dlg = PasswordDialog(username, self)
        if dlg.exec():
            try:
                self.manager.change_password(username, dlg.password)
                self.logger.info(f"Password changed for {username}")
                QMessageBox.information(self, "Success", "Password updated successfully.")
            except Exception as e:
                self.logger.error(f"Failed to change password: {e}")
                QMessageBox.critical(self, "Error", f"Failed: {e}")