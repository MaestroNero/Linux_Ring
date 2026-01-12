import logging
import subprocess
from typing import Any
from core.sudo_manager import SudoManager


class UserManager:
    """
    Manages system users, including listing, adding, removing, and locking accounts.
    """

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.sudo_manager = SudoManager()

    def list_users(self) -> list[dict[str, Any]]:
        """
        List all users on the system by parsing /etc/passwd (via getent).

        Returns:
            List of dictionaries containing user details.
        """
        try:
            result = subprocess.run(
                ["getent", "passwd"], check=True, text=True, capture_output=True
            )
            users = []
            for line in result.stdout.splitlines():
                parts = line.split(":")
                if len(parts) < 7:
                    continue
                username = parts[0]
                uid_int = int(parts[2])
                shell = parts[6]
                status = "System" if uid_int < 1000 else "Active"
                
                # Determine role based on group membership or UID
                role = "Admin" if uid_int == 0 else "User"
                if uid_int == 0:
                    role = "Root"
                elif self._is_admin(username):
                    role = "Admin (sudo)"

                users.append(
                    {
                        "username": username,
                        "uid": uid_int,
                        "shell": shell,
                        "status": status,
                        "role": role,
                    }
                )
            return users
        except subprocess.CalledProcessError as exc:
            self.logger.error("Failed to list users: %s", exc)
            return []

    def _is_admin(self, username: str) -> bool:
        """Check if user is in sudo group."""
        try:
            # This is a simple check, handling varied group names (sudo vs wheel) is ideal but stick to sudo for Kali
            cmd = ["groups", username]
            res = subprocess.run(cmd, capture_output=True, text=True)
            return "sudo" in res.stdout
        except Exception:
            return False

    def add_user(self, username: str, shell: str = "/bin/bash") -> None:
        """
        Add a new user to the system.

        Args:
            username: Name of the user.
            shell: Login shell.
        """
        self.sudo_manager.run_privileged(["useradd", "-m", "-s", shell, username])

    def remove_user(self, username: str) -> None:
        """
        Remove a user and their home directory.
        """
        self.sudo_manager.run_privileged(["userdel", "-r", username])

    def lock_user(self, username: str) -> None:
        """
        Lock a user account.
        """
        self.sudo_manager.run_privileged(["usermod", "-L", username])

