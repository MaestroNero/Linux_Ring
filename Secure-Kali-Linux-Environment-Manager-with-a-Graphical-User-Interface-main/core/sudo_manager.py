import subprocess
import logging
from typing import Optional
from PySide6.QtCore import QObject, Qt, Signal, Slot, QEventLoop, QTimer
from PySide6.QtWidgets import QInputDialog, QLineEdit, QApplication

class SudoManager(QObject):
    """
    Manages privileged command execution by requesting and caching the sudo password.
    Thread-safe implementation using Signals for cross-thread GUI access.
    """
    # Signal to request password from main thread
    password_requested = Signal(str)  # Emits prompt message
    
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(SudoManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "initialized"):
            super().__init__()
            self.password: Optional[str] = None
            self.logger = logging.getLogger("secure_kali_manager")
            self.initialized = True
            self._pending_password = None
            
            # Connect signal to slot
            self.password_requested.connect(self._show_password_dialog, type=Qt.BlockingQueuedConnection)

    @Slot(str)
    def _show_password_dialog(self, prompt_msg: str):
        """
        Shows password dialog on main thread. Called via signal.
        """
        pwd, ok = QInputDialog.getText(
            None,
            "Privilege Escalation Required",
            prompt_msg,
            QLineEdit.Password
        )
        if ok and pwd:
            self._pending_password = pwd
        else:
            self._pending_password = None

    def get_password(self, force_prompt=False) -> Optional[str]:
        """
        Prompt the user for password. Thread-safe.
        """
        if self.password and not force_prompt:
            return self.password

        prompt_msg = "This action requires root privileges.\nPlease enter your password:"
        if force_prompt:
            prompt_msg = "Incorrect Password. Please try again:"

        # Emit signal and wait for response
        self._pending_password = None
        self.password_requested.emit(prompt_msg)
        
        # The signal is connected with BlockingQueuedConnection, so it executes synchronously
        # and _pending_password is already set when we get here
        
        if self._pending_password:
            self.password = self._pending_password
            return self.password
        
        return None
    
    def run_privileged(self, command: list[str]) -> subprocess.CompletedProcess:
        """
        Run a command with sudo, handling authentication retries using Fail-Fast strategy.
        """
        retries = 3
        while retries > 0:
            pwd = self.get_password(force_prompt=(retries < 3))
            if not pwd:
                raise PermissionError("User cancelled password prompt.")

            # **SECURITY**: Validate password FIRST before running actual command
            # Use 'sudo -S -v' to validate password without running any command
            validate_cmd = ["sudo", "-S", "-v", "-p", ""]
            self.logger.debug("Validating sudo password...")
            
            try:
                validate_result = subprocess.run(
                    validate_cmd,
                    input=f"{pwd}\n",
                    text=True,
                    capture_output=True,
                    timeout=5
                )
                
                # Check validation result
                if validate_result.returncode != 0:
                    self.logger.warning("Incorrect sudo password.")
                    self.password = None
                    retries -= 1
                    continue
                
                # Password is correct! Now run the actual command
                self.logger.info(f"Password validated. Running privileged: {' '.join(command)}")
                full_command = ["sudo", "-S", "-p", ""] + command
                
                result = subprocess.run(
                    full_command,
                    input=f"{pwd}\n",
                    text=True,
                    capture_output=True
                )
                
                # Command executed (password was correct)
                if result.returncode != 0:
                    raise subprocess.CalledProcessError(result.returncode, command, result.stdout, result.stderr)

                return result
                
            except subprocess.TimeoutExpired:
                self.logger.error("Password validation timed out.")
                self.password = None
                retries -= 1
                continue
            except subprocess.CalledProcessError as e:
                raise e

        raise PermissionError("Maximum password retries exceeded.")

    def run_stream_privileged(self, command: list[str], log_callback, env=None):
        """
        Run a privileged command and stream output.
        Uses password validation before executing to prevent unauthorized execution.
        """
        retries = 3
        while retries > 0:
            pwd = self.get_password(force_prompt=(retries < 3))
            if not pwd:
                log_callback("[error] Authentication cancelled.")
                return

            # **SECURITY**: Validate password FIRST
            validate_cmd = ["sudo", "-S", "-v", "-p", ""]
            log_callback("[auth] Validating credentials...")
            
            try:
                validate_result = subprocess.run(
                    validate_cmd,
                    input=f"{pwd}\n",
                    text=True,
                    capture_output=True,
                    timeout=5
                )
                
                if validate_result.returncode != 0:
                    log_callback("[error] Incorrect password.")
                    self.password = None
                    retries -= 1
                    continue
                
                # Password validated! Run actual command
                log_callback("[auth] Credentials validated. Starting operation...")
                full_command = ["sudo", "-S", "-p", ""] + command
                
                self.logger.info(f"Running stream: {' '.join(command)}")
                
                proc = subprocess.Popen(
                    full_command,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    env=env,
                    bufsize=1,
                    universal_newlines=True
                )
                
                # Write password
                if proc.stdin:
                    try:
                        proc.stdin.write(f"{pwd}\n")
                        proc.stdin.close()
                    except (BrokenPipeError, OSError):
                        pass

                # Stream output
                if proc.stdout:
                    for line in proc.stdout:
                        log_callback(line.strip())

                proc.wait()
                
                if proc.returncode != 0:
                    log_callback(f"[error] Command failed with exit code {proc.returncode}")
                
                return
                
            except subprocess.TimeoutExpired:
                log_callback("[error] Password validation timed out.")
                self.password = None
                retries -= 1
                continue
            except Exception as e:
                log_callback(f"[error] {str(e)}")
                raise

        log_callback("[error] Maximum password retries exceeded.")
        raise PermissionError("Maximum password retries exceeded.")
