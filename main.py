import logging
import os
import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from PySide6.QtCore import QObject, Signal

from ui.main_window import MainWindow
from core.user_manager import UserManager
from core.service_manager import ServiceManager
from core.tool_installer import ToolInstaller
from core.profile_manager import ProfileManager
from core.process_manager import ProcessManager
from core.firewall_manager import FirewallManager


class LogEmitter(QObject):
    """Qt signal bridge for Python logging."""

    message = Signal(str)


class QtLogHandler(logging.Handler):
    """Logging handler that forwards messages to Qt UI."""

    def __init__(self, emitter: LogEmitter):
        super().__init__()
        self.emitter = emitter

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            self.emitter.message.emit(msg)
        except Exception:  # pragma: no cover - defensive
            self.handleError(record)


def setup_logging(emitter: LogEmitter) -> logging.Logger:
    os.makedirs("logs", exist_ok=True)
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

    logger = logging.getLogger("secure_kali_manager")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    # File sink
    file_handler = logging.FileHandler("logs/app.log")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Qt sink
    qt_handler = QtLogHandler(emitter)
    qt_handler.setFormatter(formatter)
    logger.addHandler(qt_handler)

    return logger


def load_stylesheet(app: QApplication) -> None:
    style_path = os.path.join("assets", "styles.qss")
    if not os.path.exists(style_path):
        return
    try:
        with open(style_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    except Exception as exc:  # pragma: no cover - defensive
        print(f"Could not load stylesheet: {exc}")


def build_managers(logger: logging.Logger) -> dict:
    firewall = FirewallManager(logger)
    service_mgr = ServiceManager(logger)
    user_mgr = UserManager(logger)
    process_mgr = ProcessManager(logger)
    tool_installer = ToolInstaller(logger)
    profile_mgr = ProfileManager(logger, user_mgr, service_mgr, firewall, tool_installer)

    return {
        "users": user_mgr,
        "services": service_mgr,
        "tools": tool_installer,
        "profiles": profile_mgr,
        "processes": process_mgr,
        "firewall": firewall,
    }


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Secure Kali Manager")
    app.setApplicationDisplayName("Secure Kali Manager")
    app.setWindowIcon(QIcon())

    emitter = LogEmitter()
    logger = setup_logging(emitter)
    managers = build_managers(logger)

    load_stylesheet(app)

    window = MainWindow(managers, emitter, logger)
    emitter.message.connect(window.append_log)
    window.show()

    logger.info("Secure Kali Linux Environment Manager started.")
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
