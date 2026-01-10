from functools import partial

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class UpdateWorker(QThread):
    progress = Signal(str)
    finished = Signal(bool, str)

    def __init__(self, func):
        super().__init__()
        self.func = func

    def run(self) -> None:
        try:
            self.func(self.progress.emit)
            self.finished.emit(True, "")
        except Exception as exc:  # pragma: no cover - runtime
            self.finished.emit(False, str(exc))


class UpdatesView(QWidget):
    def __init__(self, service_manager, logger):
        super().__init__()
        self.logger = logger
        self.service_manager = service_manager
        self.workers: list[UpdateWorker] = []
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<h3>Updates & Patching</h3>"))
        layout.addWidget(
            QLabel(
                "Run system updates and refresh package cache. Actions execute with sudo and stream logs."
            )
        )

        buttons = QHBoxLayout()
        refresh_btn = QPushButton("apt-get update")
        refresh_btn.clicked.connect(partial(self._run_task, "update"))
        upgrade_btn = QPushButton("apt-get upgrade")
        upgrade_btn.clicked.connect(partial(self._run_task, "upgrade"))
        buttons.addWidget(refresh_btn)
        buttons.addWidget(upgrade_btn)
        buttons.addStretch(1)
        layout.addLayout(buttons)
        layout.addStretch(1)

    def _run_task(self, action: str) -> None:
        commands = {
            "update": ["sudo", "apt-get", "update"],
            "upgrade": ["sudo", "apt-get", "upgrade", "-y"],
        }
        cmd = commands[action]
        worker = UpdateWorker(lambda emit: self._run(cmd, emit))
        worker.progress.connect(self.logger.info)
        worker.finished.connect(partial(self._finished, action=action, worker=worker))
        self.workers.append(worker)
        worker.start()

    def _run(self, command: list[str], log) -> None:
        import subprocess

        self.logger.info("Running: %s", " ".join(command))
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        assert proc.stdout
        for line in proc.stdout:
            log(line.strip())
        proc.wait()
        if proc.returncode != 0:  # pragma: no cover - runtime
            raise subprocess.CalledProcessError(proc.returncode, command)

    def _finished(self, success: bool, error: str, action: str, worker: UpdateWorker) -> None:
        try:
            self.workers.remove(worker)
        except ValueError:
            pass
        if success:
            self.logger.info("%s completed", action)
        else:
            self.logger.error("%s failed: %s", action, error)
