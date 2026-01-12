from functools import partial
import shutil
import subprocess

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QPixmap, QColor
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QScrollArea,
    QVBoxLayout,
    QWidget,
    QTabWidget,
    QMessageBox
)


class CommandWorker(QThread):
    progress = Signal(str)
    finished = Signal(bool, str)

    def __init__(self, func):
        super().__init__()
        self.func = func

    def run(self) -> None:
        try:
            self.func(self.progress.emit)
            self.finished.emit(True, "")
        except Exception as exc:  # pragma: no cover - defensive
            self.finished.emit(False, str(exc))


class ToolCard(QFrame):
    def __init__(self, tool: dict):
        super().__init__()
        self.tool = tool
        self.setObjectName("ToolCard")
        
        # Match UserCard neon styling
        self.setStyleSheet("""
            #ToolCard {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #001f27, stop:0.5 #073642, stop:1 #001f27
                );
                border: 2px solid #0d6f7c;
                border-radius: 12px;
                padding: 15px;
            }
            #ToolCard:hover {
                border: 2px solid #2aa198;
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #073642, stop:0.5 #0a4f5c, stop:1 #073642
                );
            }
        """)
        self.setLayout(self._build_layout())
        self.running = False
        self.check_installation()

    def _build_layout(self) -> QVBoxLayout:
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        header = QHBoxLayout()

        # Icon
        icon_label = QLabel("🛠️")
        icon_label.setStyleSheet("font-size: 28px;")
        header.addWidget(icon_label)

        # Title with neon color
        title = QLabel(f"<b>{self.tool['name']}</b>")
        title.setStyleSheet("""
            font-size: 16px; 
            color: #2aa198; 
            font-weight: bold;
        """)
        header.addWidget(title)
        header.addStretch(1)
        
        self.status_label = QLabel("") 
        self.status_label.setStyleSheet("font-size: 11px; font-weight: bold; color: #268bd2;")
        header.addWidget(self.status_label)
        layout.addLayout(header)

        # Description
        desc = QLabel(self.tool.get("description", ""))
        desc.setWordWrap(True)
        desc.setStyleSheet("""
            color: #93a1a1; 
            font-size: 12px; 
            margin-top: 5px;
            line-height: 1.4;
        """)
        desc.setMinimumHeight(45)
        layout.addWidget(desc)

        # Progress Bar
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.progress.setFixedHeight(6)
        self.progress.setStyleSheet("""
            QProgressBar { 
                background: #002b36; 
                border: 1px solid #0d4f5c;
                border-radius: 3px;
            } 
            QProgressBar::chunk { 
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2aa198, stop:1 #268bd2
                );
                border-radius: 2px;
            }
        """)
        layout.addWidget(self.progress)
        
        layout.addStretch()

        # Action Button
        buttons = QHBoxLayout()
        self.action_btn = QPushButton("Install")
        self.action_btn.setCursor(Qt.PointingHandCursor)
        self.action_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #268bd2, stop:1 #2aa198
                );
                color: white; 
                border: none; 
                padding: 8px 16px; 
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2aa198, stop:1 #268bd2
                );
            }
            QPushButton:disabled {
                background-color: #073642;
                color: #586e75;
            }
        """)
        # Don't connect here - ToolsView will handle connections
        buttons.addWidget(self.action_btn)
        
        buttons.addStretch()
        
        self.remove_btn = QPushButton("Remove")
        self.remove_btn.setCursor(Qt.PointingHandCursor)
        self.remove_btn.setStyleSheet("""
            QPushButton {
                color: #dc322f; 
                background: transparent; 
                font-weight: bold;
                border: 1px solid #dc322f;
                padding: 8px 16px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #dc322f;
                color: white;
            }
        """)
        # Don't connect here - ToolsView will handle connections
        buttons.addWidget(self.remove_btn)
        
        layout.addLayout(buttons)
        return layout

    def check_installation(self):
        # Check if installed
        is_installed = False
        if shutil.which(self.tool['package']) or shutil.which(self.tool['id']):
             is_installed = True
        
        # Also could use dpkg but shutil.which is faster for a quick UI check
        if is_installed:
            self.set_installed_state()
        else:
            self.set_not_installed_state()

    def set_installed_state(self):
        self.status_label.setText("INSTALLED")
        self.status_label.setStyleSheet("color: #859900; font-weight: bold;")
        self.action_btn.setText("Open")
        self.action_btn.setStyleSheet("""
            QPushButton {
                background-color: #859900; 
                color: white; 
                border: none; 
                padding: 6px 12px; 
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #2aa198; }
        """)
        self.remove_btn.setVisible(True)

    def set_not_installed_state(self):
        self.status_label.setText("NOT INSTALLED")
        self.status_label.setStyleSheet("color: #657b83; font-weight: bold;")
        self.action_btn.setText("Install")
        self.action_btn.setStyleSheet("""
            QPushButton {
                background-color: #268bd2; 
                color: white; 
                border: none; 
                padding: 6px 12px; 
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #2aa198; }
        """)
        self.remove_btn.setVisible(False)

    def set_running(self, running: bool, message: str | None = None) -> None:
        self.running = running
        self.action_btn.setDisabled(running)
        self.remove_btn.setDisabled(running)
        self.progress.setVisible(running)
        self.progress.setRange(0, 0 if running else 1)
        if message:
            self.status_label.setText(message)

    def set_status(self, status: str) -> None:
        self.status_label.setText(status)


class ToolsView(QWidget):
    def __init__(self, installer, logger, log_signal):
        super().__init__()
        self.installer = installer
        self.logger = logger
        self.log_signal = log_signal
        self.cards = {}
        self.workers: list[CommandWorker] = []

        layout = QVBoxLayout(self)
        
        header_area = QHBoxLayout()
        title = QLabel("<h2>Ultimate Tool Arsenal</h2>")
        title.setStyleSheet("color: #268bd2;")
        header_area.addWidget(title)
        header_area.addStretch()
        layout.addLayout(header_area)
        
        layout.addWidget(QLabel("Browse, install, and launch advanced security tools."))

        # Main Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 0px solid #586e75; top: -1px; }
            QTabBar::tab { background: #002b36; color: #586e75; padding: 10px 15px; border-top-left-radius: 4px; border-top-right-radius: 4px; font-weight: bold; }
            QTabBar::tab:selected { background: #073642; color: #268bd2; border-bottom: 2px solid #268bd2; }
        """)
        layout.addWidget(self.tabs)
        
        # Load Catalog
        try:
            catalog = self.installer.load_catalog("assets/tools_catalog.yml")
            categories = catalog.get("categories", [])
            for cat in categories:
                self.add_category_tab(cat)
        except Exception as e:
            self.logger.error(f"Failed to init tools view: {e}")
            layout.addWidget(QLabel(f"Error loading catalog: {e}"))

    def add_category_tab(self, category: dict):
        tab = QWidget()
        tab_layout = QVBoxLayout(tab)
        tab_layout.setContentsMargins(10, 20, 10, 10)
        
        # Description
        if "description" in category:
            desc = QLabel(f"<i>{category['description']}</i>")
            desc.setStyleSheet("color: #93a1a1; margin-bottom: 15px;")
            tab_layout.addWidget(desc)
        
        # Scroll Area for Grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        container = QWidget()
        grid = QGridLayout(container)
        grid.setSpacing(20)
        
        tools = category.get("tools", [])
        cols = 3
        for idx, tool in enumerate(tools):
            card = ToolCard(tool)
            self.cards[tool["id"]] = card # Register card for updates
            
            # Connect buttons
            card.action_btn.clicked.connect(partial(self._handle_action_click, tool))
            card.remove_btn.clicked.connect(partial(self._start_task, "remove", tool))
            
            row, col = divmod(idx, cols)
            grid.addWidget(card, row, col)
            
        # Spacer for empty cells
        grid.setRowStretch( (len(tools) + cols - 1) // cols, 1)

        container.setLayout(grid)
        scroll.setWidget(container)
        tab_layout.addWidget(scroll)
        
        self.tabs.addTab(tab, category["name"])

    def _handle_action_click(self, tool: dict):
        card = self.cards.get(tool["id"])
        if card.action_btn.text() == "Open":
            self._open_tool(tool)
        else:
            self._start_task("install", tool)

    def _open_tool(self, tool: dict):
        """Launch a tool with smart terminal detection."""
        cmd = tool['package']
        self.logger.info(f"Opening {cmd}...")
        
        # Check if command exists
        if not shutil.which(cmd):
            QMessageBox.warning(self, "Tool Not Found", 
                              f"{cmd} is not installed or not in PATH.\nPlease install it first.")
            self.logger.error(f"{cmd} not found in PATH")
            return
        
        # Known GUI tools that should run directly without terminal
        gui_tools = [
            'burpsuite', 'maltego', 'wireshark', 'ghidra', 'zaproxy', 
            'armitage', 'ettercap', 'zenmap', 'bettercap', 'msfconsole'
        ]
        
        # Tools that require root/sudo
        sudo_tools = [
            'masscan', 'aircrack-ng', 'airodump-ng', 'aireplay-ng', 
            'tcpdump', 'ettercap', 'bettercap', 'kismet', 'wifite',
            'reaver', 'pixiewps', 'macchanger', 'arpspoof', 'mitmdump'
        ]
        
        # Check if tool needs sudo
        needs_sudo = cmd in sudo_tools
        
        # If it's a known GUI tool, try direct launch
        if cmd in gui_tools:
            try:
                self.logger.debug(f"Attempting direct launch of GUI tool {cmd}")
                launch_cmd = [cmd]
                if needs_sudo and cmd not in ['wireshark']:  # wireshark has its own sudo handling
                    launch_cmd = ['sudo', cmd]
                subprocess.Popen(launch_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
                self.logger.info(f"Launched {cmd} directly (GUI mode)")
                return
            except Exception as e:
                self.logger.debug(f"Direct launch failed: {e}")
        
        # For CLI tools, use interactive terminal
        # Build the command to run in terminal
        if needs_sudo:
            bash_cmd = f'sudo {cmd}; exec bash'  # Keep terminal open after tool exits
        else:
            bash_cmd = f'{cmd}; exec bash'
        
        # Terminal options with interactive bash
        terminals = [
            (['xterm', '-e', 'bash', '-c', bash_cmd], 'xterm'),
            (['konsole', '-e', 'bash', '-c', bash_cmd], 'konsole'),
            (['tilix', '-e', 'bash', '-c', bash_cmd], 'tilix'),
            (['terminator', '-e', f'bash -c "{bash_cmd}"'], 'terminator'),
            (['mate-terminal', '-e', f'bash -c "{bash_cmd}"'], 'mate-terminal'),
        ]
        
        # Try each terminal
        for term_cmd, term_name in terminals:
            if shutil.which(term_cmd[0]):
                try:
                    self.logger.debug(f"Trying {term_name}...")
                    subprocess.Popen(term_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
                    sudo_msg = " (with sudo)" if needs_sudo else ""
                    self.logger.info(f"Launched {cmd} using {term_name}{sudo_msg}")
                    return
                except Exception as e:
                    self.logger.debug(f"{term_name} failed: {e}")
                    continue
        
        # Last resort: gnome-terminal
        if shutil.which('gnome-terminal'):
            try:
                self.logger.debug("Trying gnome-terminal...")
                subprocess.Popen(['gnome-terminal', '--', 'bash', '-c', bash_cmd], 
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
                sudo_msg = " (with sudo)" if needs_sudo else ""
                self.logger.info(f"Launched {cmd} using gnome-terminal{sudo_msg}")
                return
            except Exception as e:
                self.logger.debug(f"gnome-terminal failed: {e}")
        
        # All attempts failed
        error_msg = (f"Could not launch {cmd}.\n\n"
                    f"No suitable terminal emulator found.\n"
                    f"Please install one of:\n"
                    f"  • xterm (recommended): sudo apt install xterm\n"
                    f"  • konsole: sudo apt install konsole")
        QMessageBox.warning(self, "Launch Failed", error_msg)
        self.logger.error(f"Failed to launch {cmd} - no terminal found")

    def _start_task(self, action: str, tool: dict) -> None:
        card = self.cards.get(tool["id"])
        if not card: return

        action_title = action.capitalize()
        card.set_running(True, f"{action_title}ing...")
        self.logger.info("%s %s...", action_title, tool["name"])

        fn_map = {
            "install": self.installer.install_tool,
            "update": self.installer.update_tool,
            "remove": self.installer.remove_tool,
        }

        worker = CommandWorker(lambda emit: fn_map[action](tool, emit))
        worker.progress.connect(self.log_signal)
        worker.finished.connect(
            partial(self._task_finished, tool=tool, action=action, worker=worker)
        )
        self.workers.append(worker)
        worker.start()

    def _task_finished(self, success: bool, error: str, tool: dict, action: str, worker: CommandWorker) -> None:
        card = self.cards.get(tool["id"])
        if card:
             card.set_running(False)
        try:
            self.workers.remove(worker)
        except ValueError:
            pass

        if success:
            status_msg = f"{tool['name']} {action}ed successfully"
            self.logger.info(status_msg)
            self.log_signal.emit(status_msg)
            card.check_installation() # Re-check status
        else:
            status_msg = f"{action.capitalize()} failed: {error}"
            self.logger.error(status_msg)
            if card: card.set_status("Error")
            self.log_signal.emit(status_msg)
