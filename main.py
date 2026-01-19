import sys
import os
import signal
import logging
import datetime

# Silence noisy Wayland warnings before QApplication initializes
os.environ["QT_LOGGING_RULES"] = "qt.qpa.wayland.textinput=false"

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon, QFontDatabase
from PySide6.QtCore import QObject, Signal

from ui.main_window import MainWindow
from core.process_manager import ProcessManager
from core.service_manager import ServiceManager
from core.user_manager import UserManager
from core.tool_installer import ToolInstaller
from core.firewall_manager import FirewallManager
from core.profile_manager import ProfileManager
from core.sudo_manager import SudoManager  # New Graphical Sudo Manager


class LogEmitter(QObject):
    message = Signal(str)


class SignalHandler(logging.Handler):
    def __init__(self, emitter):
        super().__init__()
        self.emitter = emitter

    def emit(self, record):
        msg = self.format(record)
        self.emitter.message.emit(msg)


def setup_logging():
    logger = logging.getLogger("MaestroManager")
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # 1. Console Handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # 2. File Handler (New) - Rotating
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(log_dir, f"session_{date_str}.log")
    
    # 5 MB max size, keep last 3 backups
    from logging.handlers import RotatingFileHandler
    fh = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # 3. GUI Signal Handler
    emitter = LogEmitter()
    sh = SignalHandler(emitter)
    sh.setFormatter(formatter)
    logger.addHandler(sh)

    return logger, emitter


def main():
    # Handle Ctrl+C
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QApplication(sys.argv)
    
    # Load fonts if needed
    # QFontDatabase.addApplicationFont("assets/fonts/MyFont.ttf")

    # Load Styles
    try:
        with open("assets/styles.qss", "r") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        print("Warning: styles.qss not found, using default look.")

    logger, emitter = setup_logging()
    logger.info("Starting Linux Ring By Maestro Nero...")

    # Initialize Core Managers
    logger.info("Initializing Sudo Manager...")
    sudo_manager = SudoManager() # Singleton-like usage
    
    # --- STARTUP AUTHENTICATION ---
    # Ask for root password immediately at startup
    logger.info("Requesting root privileges for session...")
    
    authenticated = False
    max_retries = 3
    
    for attempt in range(max_retries):
        # Force prompt on retry
        should_force = (attempt > 0)
        pwd = sudo_manager.get_password(force_prompt=should_force)
        
        if not pwd:
            break # User cancelled
            
        if sudo_manager.validate_credentials():
            authenticated = True
            logger.info("Root privileges acquired and validated.")
            break
        else:
            logger.warning(f"Invalid password attempt {attempt + 1}/{max_retries}")
            sudo_manager.clear_password_cache()
            
    if not authenticated:
        logger.warning("Root authentication failed or cancelled. Some features may not work.")
    # ------------------------------

    # Check privileges (optional, since we now handle sudo graphically)
    if os.geteuid() != 0:
        logger.info("Running as non-root user. Privileged operations will prompt for password.")

    # Instantiate managers individually
    firewall_mgr = FirewallManager(logger)
    service_mgr = ServiceManager(logger)
    user_mgr = UserManager(logger)
    process_mgr = ProcessManager(logger)
    tool_installer = ToolInstaller(logger)
    
    # ProfileManager needs references to others
    profile_mgr = ProfileManager(logger, user_mgr, service_mgr, firewall_mgr, tool_installer)

    managers = {
        "processes": process_mgr,
        "services": service_mgr,
        "users": user_mgr,
        "tools": tool_installer,
        "firewall": firewall_mgr,
        "profiles": profile_mgr, 
    }



    window = MainWindow(managers, emitter, logger)
    emitter.message.connect(window.append_log)
    window.show()

    logger.info("Secure Kali Linux Environment Manager started.")
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
