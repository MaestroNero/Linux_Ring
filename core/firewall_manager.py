import logging
import os
import subprocess
import shutil
from typing import Callable
from core.sudo_manager import SudoManager


class FirewallManager:
    """
    Manages system firewall using ufw (Uncomplicated Firewall).
    """

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.sudo_manager = SudoManager()
        self.ufw_available = self._check_ufw_installed()

    def _is_root(self):
        """Check if running as root"""
        return os.geteuid() == 0

    def _check_ufw_installed(self) -> bool:
        """Checks if ufw is installed and logs a warning if not."""
        if not shutil.which("ufw"):
            self.logger.warning("UFW is not installed or not in PATH. Firewall operations will fail.")
            return False
        return True

    def get_status(self) -> str:
        """Get current firewall status"""
        if not self.ufw_available:
            return "UFW not installed"
        try:
            if self._is_root():
                result = subprocess.run(["ufw", "status"], capture_output=True, text=True)
            else:
                result = subprocess.run(["sudo", "ufw", "status"], capture_output=True, text=True)
            return result.stdout.strip()
        except Exception as e:
            self.logger.error(f"Failed to get firewall status: {e}")
            return "Error getting status"

    def is_active(self) -> bool:
        """Check if firewall is active"""
        status = self.get_status()
        return "Status: active" in status

    def enable(self, log_callback: Callable[[str], None] = None) -> bool:
        """Enable the firewall"""
        if not self.ufw_available:
            return False
        try:
            if log_callback:
                log_callback("Enabling firewall...")
            if self._is_root():
                subprocess.run(["ufw", "--force", "enable"], check=True)
            else:
                self.sudo_manager.run_privileged(["ufw", "--force", "enable"])
            if log_callback:
                log_callback("Firewall enabled successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to enable firewall: {e}")
            return False

    def disable(self, log_callback: Callable[[str], None] = None) -> bool:
        """Disable the firewall"""
        if not self.ufw_available:
            return False
        try:
            if log_callback:
                log_callback("Disabling firewall...")
            if self._is_root():
                subprocess.run(["ufw", "disable"], check=True)
            else:
                self.sudo_manager.run_privileged(["ufw", "disable"])
            if log_callback:
                log_callback("Firewall disabled")
            return True
        except Exception as e:
            self.logger.error(f"Failed to disable firewall: {e}")
            return False

    def enable_firewall(self, log_callback: Callable[[str], None]) -> None:
        """
        Enable ufw with default deny incoming / allow outgoing policy.
        """
        if not self.ufw_available:
            log_callback("UFW is not installed")
            return
        log_callback("Enabling ufw with deny-by-default policy")
        if self._is_root():
            subprocess.run(["ufw", "default", "deny", "incoming"], check=True)
            subprocess.run(["ufw", "default", "allow", "outgoing"], check=True)
            subprocess.run(["ufw", "--force", "enable"], check=True)
        else:
            self.sudo_manager.run_privileged(["ufw", "default", "deny", "incoming"])
            self.sudo_manager.run_privileged(["ufw", "default", "allow", "outgoing"])
            self.sudo_manager.run_privileged(["ufw", "--force", "enable"])
        log_callback("Firewall enabled successfully.")

    def allow_ports(self, ports: list[int], log_callback: Callable[[str], None]) -> None:
        """
        Allow specific TCP ports.
        """
        if not self.ufw_available:
            return
        for port in ports:
            log_callback(f"Allowing port {port}/tcp")
            if self._is_root():
                subprocess.run(["ufw", "allow", f"{port}/tcp"], check=True)
            else:
                self.sudo_manager.run_privileged(["ufw", "allow", f"{port}/tcp"])

    def close_ports(self, ports: list[int], log_callback: Callable[[str], None]) -> None:
        """
        Deny specific TCP ports.
        """
        if not self.ufw_available:
            return
        for port in ports:
            log_callback(f"Denying port {port}/tcp")
            if self._is_root():
                subprocess.run(["ufw", "deny", f"{port}/tcp"], check=True)
            else:
                self.sudo_manager.run_privileged(["ufw", "deny", f"{port}/tcp"])

    def close_all_except(self, allowed: list[int], log_callback: Callable[[str], None]) -> None:
        """
        Reset firewall and allow only specified ports.
        """
        if not self.ufw_available:
            return
        log_callback("Closing all ports except minimal allow list")
        if self._is_root():
            subprocess.run(["ufw", "--force", "reset"], check=True)
        else:
            self.sudo_manager.run_privileged(["ufw", "--force", "reset"])
        self.enable_firewall(log_callback)
        self.allow_ports(allowed, log_callback)

