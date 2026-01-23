from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame, QMessageBox, QGridLayout,
    QInputDialog, QLineEdit
)
from functools import partial
import os
import subprocess

class UpdateCard(QFrame):
    def __init__(self, title, desc, icon_text, color, callback):
        super().__init__()
        self.callback = callback
        self.color = color
        self.setObjectName("UpdateCard")
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            #UpdateCard {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(30, 41, 59, 0.9),
                    stop:1 rgba(51, 65, 85, 0.7));
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 16px;
            }}
            #UpdateCard:hover {{
                border: 1px solid {color};
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(51, 65, 85, 0.95),
                    stop:1 rgba(71, 85, 105, 0.8));
            }}
            QLabel {{ background: transparent; }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)
        
        # Icon
        icon_lbl = QLabel(icon_text)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet(f"font-size: 52px;")
        layout.addWidget(icon_lbl)
        
        # Text
        main_lbl = QLabel(title)
        main_lbl.setAlignment(Qt.AlignCenter)
        main_lbl.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {color};")
        layout.addWidget(main_lbl)
        
        sub_lbl = QLabel(desc)
        sub_lbl.setAlignment(Qt.AlignCenter)
        sub_lbl.setWordWrap(True)
        sub_lbl.setStyleSheet("font-size: 12px; color: #94a3b8;")
        layout.addWidget(sub_lbl)
        
        layout.addStretch()
        
        # Button
        btn = QPushButton("▶ Run Update")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 {color}, stop:1 {self._lighten_color(color)});
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 {self._lighten_color(color)}, stop:1 {color});
            }}
        """)
        btn.clicked.connect(self.callback)
        layout.addWidget(btn)
    
    def _lighten_color(self, hex_color):
        """Simple color lightening"""
        # Just return a slightly different shade
        color_map = {
            "#38bdf8": "#7dd3fc",
            "#22c55e": "#4ade80",
            "#ef4444": "#f87171",
            "#eab308": "#facc15",
            "#8b5cf6": "#a78bfa",
        }
        return color_map.get(hex_color, hex_color)

class UpdatesView(QWidget):
    def __init__(self, installer, logger, task_queue):
        super().__init__()
        self.installer = installer
        self.logger = logger
        self.task_queue = task_queue
        self._cached_password = None
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(25)
        
        # Header Frame
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
        
        header = QLabel("🔄 Update Center")
        header.setStyleSheet("font-size: 20px; font-weight: bold; color: #38bdf8; background: transparent;")
        header_layout.addWidget(header)
        
        subtitle = QLabel("Keep your system and tools up to date")
        subtitle.setStyleSheet("color: #64748b; font-size: 13px; background: transparent;")
        header_layout.addWidget(subtitle)
        
        layout.addWidget(header_frame)
        
        grid = QGridLayout()
        grid.setSpacing(25)
        
        # Card 1: Update App (Git Pull)
        app_card = UpdateCard(
            "Update Application", 
            "Pull latest changes from the repository.", 
            "🚀", 
            "#38bdf8",
            self.update_app
        )
        grid.addWidget(app_card, 0, 0)

        # Card 2: Update Packages
        pkg_card = UpdateCard(
            "System Packages", 
            "Refresh package lists and upgrade installed tools.", 
            "📦", 
            "#22c55e",
            self.update_system
        )
        grid.addWidget(pkg_card, 0, 1)

        # Card 3: Distro Upgrade
        dist_card = UpdateCard(
            "Distro Upgrade", 
            "Perform a full distribution upgrade (Use with caution).", 
            "⚠️", 
            "#ef4444",
            self.upgrade_distro
        )
        grid.addWidget(dist_card, 0, 2)
        
        layout.addLayout(grid)
        layout.addStretch()

    def _request_sudo_password(self) -> str:
        """Request sudo password from user with styled dialog"""
        pwd, ok = QInputDialog.getText(
            self,
            "🔐 Authentication Required",
            "This operation requires administrator privileges.\nPlease enter your password:",
            QLineEdit.Password
        )
        if ok and pwd:
            self._cached_password = pwd
            return pwd
        return None

    def _run_with_sudo(self, cmd: list, emit, password: str) -> bool:
        """Run command with sudo using provided password"""
        full_cmd = ["sudo", "-S"] + cmd
        proc = subprocess.Popen(
            full_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        # Send password
        proc.stdin.write(password + "\n")
        proc.stdin.flush()
        
        for line in proc.stdout:
            line = line.strip()
            if line and "password" not in line.lower() and "[sudo]" not in line:
                emit(line)
        
        proc.wait()
        return proc.returncode == 0

    def update_app(self):
        import os
        app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        def run_git(emit):
            import subprocess
            
            emit("📍 Checking current directory...")
            emit(f"Working in: {app_dir}")
            
            # Check if git repo exists
            if not os.path.exists(os.path.join(app_dir, ".git")):
                emit("⚠️ Not a git repository. Initializing...")
                subprocess.run(["git", "init"], cwd=app_dir, capture_output=True)
            
            emit("🔗 Configuring remote repository...")
            repo_url = "https://github.com/MaestroNero/Linux_Ring.git"
            subprocess.run(["git", "remote", "remove", "origin"], cwd=app_dir, capture_output=True)
            subprocess.run(["git", "remote", "add", "origin", repo_url], cwd=app_dir, capture_output=True)
            
            emit("📥 Fetching latest changes...")
            res = subprocess.run(["git", "fetch", "origin"], cwd=app_dir, capture_output=True, text=True)
            
            emit("🔄 Pulling updates...")
            res = subprocess.run(["git", "pull", "origin", "main", "--allow-unrelated-histories"], 
                                cwd=app_dir, capture_output=True, text=True)
            
            if res.returncode != 0:
                if "couldn't find remote ref main" in res.stderr:
                    emit("Trying master branch...")
                    res = subprocess.run(["git", "pull", "origin", "master", "--allow-unrelated-histories"], 
                                        cwd=app_dir, capture_output=True, text=True)
                
                if res.returncode != 0:
                    emit(f"⚠️ Git output: {res.stderr or res.stdout}")
                    emit("ℹ️ You may need to commit local changes first.")
                    return
            
            emit("✅ Application updated successfully!")
            emit("🔄 Please restart the application to apply changes.")

        self.task_queue.add_task("Update Application", run_git)

    def update_system(self):
        is_root = os.geteuid() == 0
        
        # If not root, ask for password BEFORE starting the task
        password = None
        if not is_root:
            password = self._request_sudo_password()
            if not password:
                QMessageBox.warning(self, "Cancelled", "Operation cancelled - no password provided.")
                return
        
        def run_apt(emit):
            emit("📦 Updating package lists...")
            
            if is_root:
                # Run directly as root
                proc = subprocess.Popen(
                    ["apt-get", "update", "-y"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True
                )
                for line in proc.stdout:
                    if line.strip():
                        emit(line.strip())
                proc.wait()
                
                if proc.returncode != 0:
                    emit("⚠️ Update failed.")
                    return
                
                emit("⬆️ Upgrading packages...")
                proc = subprocess.Popen(
                    ["apt-get", "upgrade", "-y"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True
                )
                for line in proc.stdout:
                    if line.strip():
                        emit(line.strip())
                proc.wait()
            else:
                # Use sudo with password
                if not self._run_with_sudo(["apt-get", "update", "-y"], emit, password):
                    emit("⚠️ Update failed. Incorrect password or network issue.")
                    return
                
                emit("⬆️ Upgrading packages...")
                self._run_with_sudo(["apt-get", "upgrade", "-y"], emit, password)
            
            emit("✅ System packages updated successfully!")

        self.task_queue.add_task("System Packages Update", run_apt)

    def upgrade_distro(self):
        is_root = os.geteuid() == 0
        
        res = QMessageBox.warning(self, "Distro Upgrade", 
                            "This will run `apt-get dist-upgrade`. It may take a long time.\nContinue?",
                            QMessageBox.Yes | QMessageBox.No)
        if res != QMessageBox.Yes:
            return

        # If not root, ask for password BEFORE starting the task
        password = None
        if not is_root:
            password = self._request_sudo_password()
            if not password:
                QMessageBox.warning(self, "Cancelled", "Operation cancelled - no password provided.")
                return

        def run_dist_upgrade(emit):
            emit("🚀 Starting distribution upgrade...")
            
            if is_root:
                proc = subprocess.Popen(
                    ["apt-get", "dist-upgrade", "-y"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True
                )
                for line in proc.stdout:
                    if line.strip():
                        emit(line.strip())
                proc.wait()
                
                if proc.returncode == 0:
                    emit("✅ Distribution upgrade completed!")
                else:
                    emit("⚠️ Upgrade completed with warnings. Check logs.")
            else:
                if self._run_with_sudo(["apt-get", "dist-upgrade", "-y"], emit, password):
                    emit("✅ Distribution upgrade completed!")
                else:
                    emit("⚠️ Upgrade failed or completed with warnings.")

        self.task_queue.add_task("Distribution Upgrade", run_dist_upgrade)
