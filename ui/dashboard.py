import platform
import shutil

from PySide6.QtWidgets import QLabel, QGridLayout, QGroupBox, QVBoxLayout, QWidget


class Dashboard(QWidget):
    def __init__(self, managers: dict):
        super().__init__()
        self.process_manager = managers.get("processes")
        self.service_manager = managers.get("services")

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<h2>Secure Kali Linux Environment Manager</h2>"))
        layout.addWidget(QLabel("Overview of system health and security posture."))

        grid = QGridLayout()
        layout.addLayout(grid)

        self.stats_box = QGroupBox("Host Overview")
        stats_layout = QGridLayout(self.stats_box)
        info = self._collect_host_info()
        for row, (key, value) in enumerate(info.items()):
            stats_layout.addWidget(QLabel(f"<b>{key}</b>"), row, 0)
            stats_layout.addWidget(QLabel(value), row, 1)

        self.service_box = QGroupBox("Critical Services")
        service_layout = QVBoxLayout(self.service_box)
        service_layout.addWidget(
            QLabel("Use the Services view to audit startup status and risk levels.")
        )

        grid.addWidget(self.stats_box, 0, 0)
        grid.addWidget(self.service_box, 0, 1)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        layout.addStretch(1)

    def _collect_host_info(self) -> dict:
        cpu_info = platform.processor() or "Unknown CPU"
        system = platform.system()
        release = platform.release()
        disk = shutil.disk_usage("/")
        disk_summary = f"{disk.used // (1024**3)}G used / {disk.total // (1024**3)}G"

        stats = {"OS": f"{system} {release}", "CPU": cpu_info, "Disk": disk_summary}
        if self.process_manager:
            metrics = self.process_manager.get_system_metrics()
            stats["CPU Load"] = f"{metrics['cpu']}%"
            stats["Memory"] = f"{metrics['memory_used']} / {metrics['memory_total']} GB"
        return stats
