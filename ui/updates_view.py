from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame, QMessageBox, QGridLayout
)
from functools import partial

class UpdateCard(QFrame):
    def __init__(self, title, desc, icon_text, color, callback):
        super().__init__()
        self.callback = callback
        self.setObjectName("UpdateCard")
        self.setStyleSheet(f"""
            #UpdateCard {{
                background-color: #073642;
                border: 2px solid #586e75;
                border-radius: 15px;
            }}
            #UpdateCard:hover {{
                border: 2px solid {color};
                background-color: #002b36;
            }}
            QLabel {{ background: transparent; }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Icon
        icon_lbl = QLabel(icon_text)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet(f"font-size: 48px; color: {color};")
        layout.addWidget(icon_lbl)
        
        # Text
        main_lbl = QLabel(title)
        main_lbl.setAlignment(Qt.AlignCenter)
        main_lbl.setStyleSheet("font-size: 18px; font-weight: bold; color: #eee8d5;")
        layout.addWidget(main_lbl)
        
        sub_lbl = QLabel(desc)
        sub_lbl.setAlignment(Qt.AlignCenter)
        sub_lbl.setWordWrap(True)
        sub_lbl.setStyleSheet("font-size: 13px; color: #93a1a1;")
        layout.addWidget(sub_lbl)
        
        # Button
        btn = QPushButton("Run Update")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{
                /* filter: brightness(110%); Not supported in QSS */
            }}
        """)
        btn.clicked.connect(self.callback)
        layout.addWidget(btn)

class UpdatesView(QWidget):
    def __init__(self, installer, logger, task_queue):
        super().__init__()
        self.installer = installer
        self.logger = logger
        self.task_queue = task_queue
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(30)
        
        header = QLabel("<h2>Update Center</h2>")
        header.setStyleSheet("color: #268bd2;")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        grid = QGridLayout()
        grid.setSpacing(30)
        
        # Card 1: Update App (Git Pull)
        app_card = UpdateCard(
            "Update Application", 
            "Pull latest changes from the repository.", 
            "🚀", 
            "#268bd2",
            self.update_app
        )
        grid.addWidget(app_card, 0, 0)

        # Card 2: Update Packages
        pkg_card = UpdateCard(
            "System Packages", 
            "Refresh package lists and upgrade installed tools.", 
            "📦", 
            "#859900",
            self.update_system
        )
        grid.addWidget(pkg_card, 0, 1)

        # Card 3: Distro Upgrade
        dist_card = UpdateCard(
            "Distro Upgrade", 
            "Perform a full distribution upgrade (Use with caution).", 
            "⚠️", 
            "#dc322f",
            self.upgrade_distro
        )
        grid.addWidget(dist_card, 0, 2)
        
        layout.addLayout(grid)
        layout.addStretch()

    def update_app(self):
        repo_url = "https://github.com/MaestroNero/Secure-Kali-Linux-Environment-Manager-with-a-Graphical-User-Interface"
        
        def run_git(emit):
            import subprocess
            emit("Configuring remote repository...")
            subprocess.run(["git", "remote", "set-url", "origin", repo_url], capture_output=True)
            
            emit("Fetching latest changes...")
            subprocess.run(["git", "fetch", "origin"], capture_output=True)
            
            emit("Pulling updates...")
            res = subprocess.run(["git", "pull", "origin", "main"], capture_output=True, text=True)
            
            if res.returncode != 0:
                 if "couldn't find remote ref main" in res.stderr:
                      emit("Main branch not found, trying master...")
                      res = subprocess.run(["git", "pull", "origin", "master"], capture_output=True, text=True)
                 
                 if res.returncode != 0:
                    raise Exception(f"Git failed: {res.stderr}")
            
            emit("Successfully updated from repository.")

        self.task_queue.add_task("Update Application", run_git)

    def update_system(self):
        def run_apt(emit):
            emit("Updating package lists...")
            self.installer.sudo_manager.run_stream_privileged(["apt-get", "update", "-y"], emit)
            emit("Upgrading packages...")
            self.installer.sudo_manager.run_stream_privileged(["apt-get", "upgrade", "-y"], emit)
            emit("Done.")

        self.task_queue.add_task("System Packages Update", run_apt)

    def upgrade_distro(self):
        res = QMessageBox.warning(self, "Distro Upgrade", 
                            "This will run `apt-get dist-upgrade`. It may take a long time.\\nContinue?",
                            QMessageBox.Yes | QMessageBox.No)
        if res != QMessageBox.Yes:
            return

        def run_dist_upgrade(emit):
            self.installer.sudo_manager.run_stream_privileged(["apt-get", "dist-upgrade", "-y"], emit)

        self.task_queue.add_task("Distribution Upgrade", run_dist_upgrade)
