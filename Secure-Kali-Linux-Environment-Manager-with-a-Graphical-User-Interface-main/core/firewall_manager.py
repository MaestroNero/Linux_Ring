import logging
import subprocess
from typing import Callable
from core.sudo_manager import SudoManager


class FirewallManager:
    """
    Manages system firewall using ufw (Uncomplicated Firewall).
    """

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.sudo_manager = SudoManager()

    def enable_firewall(self, log_callback: Callable[[str], None]) -> None:
        """
        Enable ufw with default deny incoming / allow outgoing policy.
        """
        log_callback("Enabling ufw with deny-by-default policy")
        self.sudo_manager.run_privileged(["ufw", "default", "deny", "incoming"])
        self.sudo_manager.run_privileged(["ufw", "default", "allow", "outgoing"])
        self.sudo_manager.run_privileged(["ufw", "--force", "enable"])
        log_callback("Firewall enabled successfully.")

    def allow_ports(self, ports: list[int], log_callback: Callable[[str], None]) -> None:
        """
        Allow specific TCP ports.
        """
        for port in ports:
            log_callback(f"Allowing port {port}/tcp")
            self.sudo_manager.run_privileged(["ufw", "allow", f"{port}/tcp"])

    def close_ports(self, ports: list[int], log_callback: Callable[[str], None]) -> None:
        """
        Deny specific TCP ports.
        """
        for port in ports:
            log_callback(f"Denying port {port}/tcp")
            self.sudo_manager.run_privileged(["ufw", "deny", f"{port}/tcp"])

    def close_all_except(self, allowed: list[int], log_callback: Callable[[str], None]) -> None:
        """
        Reset firewall and allow only specified ports.
        """
        log_callback("Closing all ports except minimal allow list")
        self.sudo_manager.run_privileged(["ufw", "--force", "reset"])
        self.enable_firewall(log_callback)
        self.allow_ports(allowed, log_callback)

