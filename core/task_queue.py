import logging
from enum import Enum
from typing import Callable, Optional
from PySide6.QtCore import QObject, Signal, QThread

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Task:
    def __init__(self, task_id: str, name: str, func: Callable, callback=None):
        self.id = task_id
        self.name = name
        self.func = func
        self.callback = callback
        self.status = TaskStatus.PENDING
        self.progress = 0
        self.error = None

class TaskWorker(QThread):
    """Worker thread to execute a single task."""
    progress = Signal(str)  # Progress message
    finished = Signal(bool, str)  # (success, error_message)

    def __init__(self, func):
        super().__init__()
        self.func = func

    def run(self):
        try:
            self.func(self.progress.emit)
            self.finished.emit(True, "")
        except Exception as e:
            self.finished.emit(False, str(e))

class TaskQueueManager(QObject):
    """
    Manages a queue of tasks that execute sequentially.
    """
    task_added = Signal(str, str)  # (task_id, task_name)
    task_started = Signal(str)  # task_id
    task_progress = Signal(str, str)  # (task_id, message)
    task_completed = Signal(str, bool, str)  # (task_id, success, error)
    
    def __init__(self):
        super().__init__()
        self.tasks = []
        self.current_task = None
        self.current_worker = None
        self.logger = logging.getLogger("TaskQueueManager")
        self.task_counter = 0

    def add_task(self, name: str, func: Callable) -> str:
        """Add a task to the queue and start processing if idle."""
        self.task_counter += 1
        task_id = f"task_{self.task_counter}"
        
        task = Task(task_id, name, func)
        self.tasks.append(task)
        
        self.task_added.emit(task_id, name)
        self.logger.info(f"Task added: {name} (ID: {task_id})")
        
        # Start processing if no task is running
        if self.current_task is None:
            self._process_next()
        
        return task_id

    def _process_next(self):
        """Process the next task in queue."""
        if not self.tasks:
            self.current_task = None
            return
        
        # Get next pending task
        pending = [t for t in self.tasks if t.status == TaskStatus.PENDING]
        if not pending:
            self.current_task = None
            return
        
        task = pending[0]
        self.current_task = task
        task.status = TaskStatus.RUNNING
        
        self.task_started.emit(task.id)
        self.logger.info(f"Task started: {task.name}")
        
        # Create worker
        self.current_worker = TaskWorker(task.func)
        self.current_worker.progress.connect(lambda msg: self._on_progress(task.id, msg))
        self.current_worker.finished.connect(lambda success, error: self._on_finished(task.id, success, error))
        self.current_worker.start()

    def _on_progress(self, task_id: str, message: str):
        """Handle progress updates from worker."""
        self.task_progress.emit(task_id, message)

    def _on_finished(self, task_id: str, success: bool, error: str):
        """Handle task completion."""
        task = next((t for t in self.tasks if t.id == task_id), None)
        if task:
            task.status = TaskStatus.COMPLETED if success else TaskStatus.FAILED
            task.error = error if not success else None
        
        self.task_completed.emit(task_id, success, error)
        self.logger.info(f"Task completed: {task_id} (Success: {success})")
        
        # Clean up worker
        if self.current_worker:
            self.current_worker.deleteLater()
            self.current_worker = None
        
        # Process next task
        self._process_next()

    def get_all_tasks(self):
        """Return all tasks."""
        return self.tasks

    def get_task(self, task_id: str):
        """Get task by ID."""
        return next((t for t in self.tasks if t.id == task_id), None)

    def clear_completed(self):
        """Remove completed/failed tasks from queue."""
        self.tasks = [t for t in self.tasks if t.status in (TaskStatus.PENDING, TaskStatus.RUNNING)]
