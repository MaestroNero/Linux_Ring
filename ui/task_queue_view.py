from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QScrollArea, QFrame, QPushButton, QProgressBar
)
from core.task_queue import TaskQueueManager, TaskStatus

class TaskCard(QFrame):
    """Widget to display a single task."""
    def __init__(self, task_id: str, task_name: str):
        super().__init__()
        self.task_id = task_id
        self.task_name = task_name
        
        self.setObjectName("TaskCard")
        self.setStyleSheet("""
            #TaskCard {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #073642, stop:1 #001f27);
                border-radius: 8px;
                border: 1px solid #586e75;
                padding: 10px;
                margin: 5px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        
        # Header: Name + Status
        header = QHBoxLayout()
        self.name_label = QLabel(task_name)
        self.name_label.setStyleSheet("font-weight: bold; color: #eee8d5; font-size: 13px;")
        header.addWidget(self.name_label)
        
        self.status_label = QLabel("⏳ Pending")
        self.status_label.setStyleSheet("color: #b58900; font-size: 12px;")
        header.addWidget(self.status_label)
        layout.addLayout(header)
        
        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setMaximumHeight(4)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: #002b36;
                border-radius: 2px;
            }
            QProgressBar::chunk {
                background-color: #268bd2;
                border-radius: 2px;
            }
        """)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)
        
        # Message Label
        self.message_label = QLabel("")
        self.message_label.setStyleSheet("color: #93a1a1; font-size: 11px;")
        self.message_label.setWordWrap(True)
        layout.addWidget(self.message_label)

    def set_status(self, status: TaskStatus):
        """Update task status display."""
        if status == TaskStatus.PENDING:
            self.status_label.setText("⏳ Pending")
            self.status_label.setStyleSheet("color: #b58900;")
            self.progress_bar.hide()
        elif status == TaskStatus.RUNNING:
            self.status_label.setText("▶️ Running")
            self.status_label.setStyleSheet("color: #268bd2;")
            self.progress_bar.show()
        elif status == TaskStatus.COMPLETED:
            self.status_label.setText("✅ Completed")
            self.status_label.setStyleSheet("color: #859900;")
            self.progress_bar.hide()
        elif status == TaskStatus.FAILED:
            self.status_label.setText("❌ Failed")
            self.status_label.setStyleSheet("color: #dc322f;")
            self.progress_bar.hide()

    def set_message(self, message: str):
        """Update progress message."""
        self.message_label.setText(message)


class TaskQueueView(QWidget):
    """Panel to display all tasks in the queue."""
    def __init__(self, task_manager: TaskQueueManager):
        super().__init__()
        self.task_manager = task_manager
        self.task_cards = {}  # task_id -> TaskCard
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("<h3>Task Queue</h3>")
        title.setStyleSheet("color: #268bd2;")
        header.addWidget(title)
        
        header.addStretch()
        
        clear_btn = QPushButton("Clear Completed")
        clear_btn.clicked.connect(self.clear_completed)
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #073642;
                color: #93a1a1;
                border: 1px solid #586e75;
                border-radius: 4px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #002b36;
                border-color: #2aa198;
            }
        """)
        header.addWidget(clear_btn)
        layout.addLayout(header)
        
        # Scroll Area for Tasks
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self.tasks_container = QWidget()
        self.tasks_layout = QVBoxLayout(self.tasks_container)
        self.tasks_layout.setAlignment(Qt.AlignTop)
        scroll.setWidget(self.tasks_container)
        
        layout.addWidget(scroll)
        
        # Connect signals
        self.task_manager.task_added.connect(self.on_task_added)
        self.task_manager.task_started.connect(self.on_task_started)
        self.task_manager.task_progress.connect(self.on_task_progress)
        self.task_manager.task_completed.connect(self.on_task_completed)

    @Slot(str, str)
    def on_task_added(self, task_id: str, task_name: str):
        """Handle new task added."""
        card = TaskCard(task_id, task_name)
        self.task_cards[task_id] = card
        self.tasks_layout.addWidget(card)

    @Slot(str)
    def on_task_started(self, task_id: str):
        """Handle task started."""
        if task_id in self.task_cards:
            self.task_cards[task_id].set_status(TaskStatus.RUNNING)

    @Slot(str, str)
    def on_task_progress(self, task_id: str, message: str):
        """Handle task progress update."""
        if task_id in self.task_cards:
            self.task_cards[task_id].set_message(message)

    @Slot(str, bool, str)
    def on_task_completed(self, task_id: str, success: bool, error: str):
        """Handle task completion."""
        if task_id in self.task_cards:
            status = TaskStatus.COMPLETED if success else TaskStatus.FAILED
            self.task_cards[task_id].set_status(status)
            if error:
                self.task_cards[task_id].set_message(f"Error: {error}")
            else:
                self.task_cards[task_id].set_message("Task completed successfully.")

    def clear_completed(self):
        """Remove completed/failed task cards."""
        self.task_manager.clear_completed()
        
        # Remove cards for completed tasks
        for task_id in list(self.task_cards.keys()):
            task = self.task_manager.get_task(task_id)
            if task is None:  # Task was cleared
                card = self.task_cards.pop(task_id)
                self.tasks_layout.removeWidget(card)
                card.deleteLater()
