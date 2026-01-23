from functools import partial
import shutil
import subprocess
import os

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QPixmap, QColor, QIcon
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
    QMessageBox,
    QSplitter,
    QListWidget,
    QStackedWidget,
    QListWidgetItem,
    QInputDialog,
    QLineEdit
)
from core.utils import resource_path
from ui.widgets.flow_layout import FlowLayout


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
        # Better sizing
        self.setMinimumSize(280, 180)
        self.setMaximumSize(380, 220)
        
        # Modern glass card styling
        self.setStyleSheet("""
            #ToolCard {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(30, 41, 59, 0.95),
                    stop:1 rgba(15, 23, 42, 0.98));
                border: 1px solid rgba(56, 189, 248, 0.15);
                border-radius: 16px;
                padding: 16px;
            }
            #ToolCard:hover {
                border: 1px solid rgba(56, 189, 248, 0.35);
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(30, 41, 59, 0.98),
                    stop:1 rgba(20, 30, 50, 0.98));
            }
        """)
        
        self.setLayout(self._build_layout())
        self.running = False
        self.check_installation()

    def _build_layout(self) -> QVBoxLayout:
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(14, 14, 14, 14)
        
        header = QHBoxLayout()

        # Icon with gradient background
        icon_container = QFrame()
        icon_container.setFixedSize(48, 48)
        icon_container.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(56, 189, 248, 0.25),
                    stop:1 rgba(139, 92, 246, 0.25));
                border-radius: 12px;
                border: 1px solid rgba(56, 189, 248, 0.2);
            }
        """)
        icon_layout = QVBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_label = QLabel("⚔️")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("font-size: 24px; background: transparent; border: none;")
        icon_layout.addWidget(icon_label)
        header.addWidget(icon_container)

        # Title and status
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title = QLabel(self.tool['name'])
        title.setWordWrap(True)
        title.setStyleSheet("""
            font-size: 15px; 
            color: #f1f5f9; 
            font-weight: 600;
            background: transparent; 
            border: none;
        """)
        title_box.addWidget(title)
        
        self.status_label = QLabel("") 
        self.status_label.setStyleSheet("font-size: 11px; font-weight: 600; color: #64748b; background: transparent; border: none;")
        title_box.addWidget(self.status_label)
        
        header.addLayout(title_box)
        header.addStretch()
        layout.addLayout(header)

        # Description
        desc = QLabel(self.tool.get("description", ""))
        desc.setWordWrap(True)
        desc.setStyleSheet("""
            color: #94a3b8; 
            font-size: 12px; 
            line-height: 1.5;
            background: transparent; 
            border: none;
        """)
        desc.setMinimumHeight(38)
        desc.setMaximumHeight(50)
        layout.addWidget(desc)

        # Progress Bar
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.progress.setFixedHeight(4)
        self.progress.setStyleSheet("""
            QProgressBar {
                background: rgba(30, 41, 59, 0.5);
                border: none;
                border-radius: 2px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #38bdf8, stop:1 #8b5cf6);
                border-radius: 2px;
            }
        """)
        layout.addWidget(self.progress)
        
        layout.addStretch()

        # Action Buttons - modern pill style
        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        
        self.action_btn = QPushButton("Install")
        self.action_btn.setCursor(Qt.PointingHandCursor)
        self.action_btn.setFixedHeight(34)
        self.action_btn.setMinimumWidth(100)
        
        buttons.addWidget(self.action_btn)
        buttons.addStretch()
        
        self.remove_btn = QPushButton("🗑️")
        self.remove_btn.setCursor(Qt.PointingHandCursor)
        self.remove_btn.setFixedSize(34, 34)
        self.remove_btn.setToolTip("Remove Tool")
        self.remove_btn.setStyleSheet("""
            QPushButton {
                background: rgba(239, 68, 68, 0.1);
                color: #ef4444;
                border: 1px solid rgba(239, 68, 68, 0.3);
                border-radius: 8px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: rgba(239, 68, 68, 0.25);
                border: 1px solid rgba(239, 68, 68, 0.5);
            }
        """)
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
        self.status_label.setText("✓ INSTALLED")
        self.status_label.setStyleSheet("color: #34d399; font-weight: 600; background: transparent; border: none;")
        self.action_btn.setText("▶ Open")
        self.action_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 rgba(16, 185, 129, 0.9), stop:1 rgba(5, 150, 105, 0.9)); 
                color: white; 
                border: none; 
                padding: 8px 16px; 
                border-radius: 8px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover { 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 rgba(16, 185, 129, 1), stop:1 rgba(5, 150, 105, 1)); 
            }
        """)
        self.remove_btn.setVisible(True)

    def set_not_installed_state(self):
        self.status_label.setText("○ NOT INSTALLED")
        self.status_label.setStyleSheet("color: #64748b; font-weight: 600; background: transparent; border: none;")
        self.action_btn.setText("⬇ Install")
        self.action_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 rgba(56, 189, 248, 0.9), stop:1 rgba(59, 130, 246, 0.9)); 
                color: white; 
                border: none; 
                padding: 8px 16px; 
                border-radius: 8px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover { 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 rgba(56, 189, 248, 1), stop:1 rgba(59, 130, 246, 1)); 
            }
        """)
        self.remove_btn.setVisible(False)

    def set_running(self, running: bool, message: str | None = None) -> None:
        self.running = running
        self.action_btn.setDisabled(running)
        self.remove_btn.setDisabled(running)
        self.progress.setVisible(running)
        self.progress.setRange(0, 0 if running else 1)
        if message:
            self.status_label.setText(f"⏳ {message}")
            self.status_label.setStyleSheet("color: #fbbf24; font-weight: 600; background: transparent; border: none;")

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

        # Main Layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)
        
        # Compact Header
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 rgba(56, 189, 248, 0.1), 
                    stop:0.5 rgba(139, 92, 246, 0.08),
                    stop:1 rgba(30, 41, 59, 0.9));
                border: 1px solid rgba(56, 189, 248, 0.2);
                border-radius: 14px;
            }
        """)
        head_layout = QHBoxLayout(header_frame)
        head_layout.setContentsMargins(20, 12, 20, 12)
        
        # Icon
        icon_lbl = QLabel("⚔️")
        icon_lbl.setStyleSheet("font-size: 28px; background: transparent; border: none;")
        head_layout.addWidget(icon_lbl)
        
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title = QLabel("Tool Arsenal")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #f1f5f9; background: transparent; border: none;")
        title_box.addWidget(title)
        
        subtitle = QLabel("Professional security tools for penetration testing")
        subtitle.setStyleSheet("color: #64748b; font-size: 12px; background: transparent; border: none;")
        title_box.addWidget(subtitle)
        
        head_layout.addLayout(title_box)
        head_layout.addStretch()
        
        # Tools count badge
        self.tools_count = QLabel("0 Tools")
        self.tools_count.setStyleSheet("""
            background: rgba(56, 189, 248, 0.15);
            color: #38bdf8;
            padding: 6px 14px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
            border: 1px solid rgba(56, 189, 248, 0.25);
        """)
        head_layout.addWidget(self.tools_count)
        
        main_layout.addWidget(header_frame)

        # Content Splitter (Left: Categories, Right: Tools)
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(1)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background: transparent;
            }
        """)
        
        # Left: Category List - more compact
        self.category_list = QListWidget()
        self.category_list.setObjectName("ToolsCategoryList")
        self.category_list.setStyleSheet("""
            QListWidget#ToolsCategoryList {
                background-color: rgba(15, 23, 42, 0.7);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 12px;
                outline: none;
                font-size: 13px;
                padding: 8px;
            }
            QListWidget#ToolsCategoryList::item {
                padding: 10px 12px;
                margin: 2px 4px;
                border-radius: 8px;
                color: #94a3b8;
            }
            QListWidget#ToolsCategoryList::item:selected {
                background-color: rgba(56, 189, 248, 0.15);
                color: #38bdf8;
                font-weight: bold;
                border-left: 3px solid #38bdf8;
            }
            QListWidget#ToolsCategoryList::item:hover {
                background-color: rgba(255, 255, 255, 0.04);
                color: #e2e8f0;
            }
        """)
        self.category_list.setFixedWidth(200)
        self.category_list.currentRowChanged.connect(self._switch_category)
        splitter.addWidget(self.category_list)

        # Right: Tool Stack
        self.stack = QStackedWidget()
        splitter.addWidget(self.stack)
        
        main_layout.addWidget(splitter)

        # Load Catalog
        total_tools = 0
        try:
            catalog_path = resource_path("assets/tools_catalog.yml")
            catalog = self.installer.load_catalog(catalog_path)
            categories = catalog.get("categories", [])
            for cat in categories:
                total_tools += len(cat.get("tools", []))
                self.add_category_list_item(cat)
                
            # Update tools count
            self.tools_count.setText(f"🔧 {total_tools} Tools")
                
            # Select first if exists
            if self.category_list.count() > 0:
                self.category_list.setCurrentRow(0)
                
        except Exception as e:
            self.logger.error(f"Failed to init tools view: {e}")
            main_layout.addWidget(QLabel(f"Error loading catalog: {e}"))

    def _switch_category(self, index):
        self.stack.setCurrentIndex(index)

    def add_category_list_item(self, category: dict):
        # Add Item to Left List - with emoji icons
        emoji_map = {
            "recon": "🔍", "info": "🔍", "analysis": "📊", "web": "🌐",
            "database": "🗄️", "password": "🔐", "wireless": "📡", "wifi": "📡",
            "reverse": "⚙️", "exploitation": "💥", "sniffing": "🕵️",
            "maintaining": "🔗", "reporting": "📝", "forensics": "🔬"
        }
        
        name_lower = category["name"].lower()
        emoji = "🛠️"
        for key, val in emoji_map.items():
            if key in name_lower:
                emoji = val
                break
        
        item = QListWidgetItem(f"{emoji}  {category['name']}")
        self.category_list.addItem(item)

        # Create Page for Right Stack
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(10, 5, 5, 5)
        page_layout.setSpacing(10)
        
        # Category Header - more compact
        if "description" in category:
            desc_frame = QFrame()
            desc_frame.setStyleSheet("""
                QFrame {
                    background: rgba(30, 41, 59, 0.6);
                    border: 1px solid rgba(255, 255, 255, 0.05);
                    border-radius: 10px;
                    padding: 8px;
                }
            """)
            df_layout = QHBoxLayout(desc_frame)
            df_layout.setContentsMargins(12, 8, 12, 8)
            
            cat_icon = QLabel(emoji)
            cat_icon.setStyleSheet("font-size: 24px; background: transparent; border: none;")
            df_layout.addWidget(cat_icon)
            
            lbl = QLabel(f"<span style='color:#e2e8f0; font-weight:600;'>{category['name']}</span><br>"
                        f"<span style='color:#64748b; font-size:11px;'>{category['description']}</span>")
            lbl.setStyleSheet("font-size: 13px; background: transparent; border: none;")
            df_layout.addWidget(lbl)
            df_layout.addStretch()
            
            # Category tool count
            tool_count = len(category.get("tools", []))
            count_lbl = QLabel(f"{tool_count}")
            count_lbl.setStyleSheet("""
                background: rgba(56, 189, 248, 0.15);
                color: #38bdf8;
                padding: 4px 10px;
                border-radius: 10px;
                font-weight: 600;
                font-size: 12px;
                border: none;
            """)
            df_layout.addWidget(count_lbl)
            
            page_layout.addWidget(desc_frame)
        
        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea { 
                border: none; 
                background: transparent; 
            }
            QScrollBar:vertical {
                background: rgba(30, 41, 59, 0.3);
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(56, 189, 248, 0.3);
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(56, 189, 248, 0.5);
            }
        """)
        
        container = QWidget()
        # Responsive Flow Layout - tighter spacing
        layout_flow = FlowLayout(container, margin=10, spacing=14)
        
        tools = category.get("tools", [])
        for idx, tool in enumerate(tools):
            card = ToolCard(tool)
            self.cards[tool["id"]] = card 
            
            card.action_btn.clicked.connect(partial(self._handle_action_click, tool))
            card.remove_btn.clicked.connect(partial(self._start_task, "remove", tool))
            
            layout_flow.addWidget(card)
            
        container.setLayout(layout_flow)
        scroll.setWidget(container)
        page_layout.addWidget(scroll)
        
        self.stack.addWidget(page)

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

        # Check if we need sudo (not root)
        is_root = os.geteuid() == 0
        password = None
        
        if not is_root and action in ["install", "remove"]:
            # Ask for password before starting
            pwd, ok = QInputDialog.getText(
                self,
                "🔐 Authentication Required",
                f"Installing/removing tools requires administrator privileges.\nPlease enter your password:",
                QLineEdit.Password
            )
            if not ok or not pwd:
                QMessageBox.warning(self, "Cancelled", "Operation cancelled - no password provided.")
                return
            password = pwd

        action_title = action.capitalize()
        card.set_running(True, f"{action_title}ing...")
        self.logger.info("%s %s...", action_title, tool["name"])

        def run_with_password(emit):
            """Wrapper to run installer with sudo password"""
            if password:
                # Set password in installer for this operation
                self.installer._sudo_password = password
            try:
                fn_map = {
                    "install": self.installer.install_tool,
                    "update": self.installer.update_tool,
                    "remove": self.installer.remove_tool,
                }
                fn_map[action](tool, emit)
            finally:
                # Clear password after use
                if hasattr(self.installer, '_sudo_password'):
                    self.installer._sudo_password = None

        worker = CommandWorker(run_with_password)
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
