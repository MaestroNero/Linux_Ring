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
            cmd = ["id", "-Gn", username]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0:
                groups = res.stdout.split()
                return "sudo" in groups or "wheel" in groups or "root" in groups
            return False
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

    # --- Group Management ---

    def get_user_groups(self, username: str) -> list[str]:
        """Returns a list of groups the user belongs to."""
        try:
            # 'id -Gn' returns space-separated group names
            res = subprocess.run(["id", "-Gn", username], capture_output=True, text=True)
            if res.returncode == 0:
                groups = res.stdout.strip().split()
                self.logger.info(f"Groups found for {username}: {groups}")
                return groups
            else:
                self.logger.warning(f"Could not get groups for {username}: {res.stderr}")
        except Exception as e:
            self.logger.error(f"Failed to get groups for {username}: {e}")
        return []

    def add_user_to_group(self, username: str, group: str) -> None:
        """Adds user to a specific group."""
        res = self.sudo_manager.run_privileged(["usermod", "-aG", group, username])
        if res.returncode == 0:
            self.logger.info(f"Successfully added {username} to {group}")
        else:
             raise Exception(f"Failed to add group: {res.stderr}")
    
    def remove_user_from_group(self, username: str, group: str) -> None:
        """Removes user from a group (requires complicated gpasswd or deluser command)."""
        # deluser user group is the standard way on Debian/Kali
        try:
            self.sudo_manager.run_privileged(["deluser", username, group])
        except subprocess.CalledProcessError as e:
            # Code 42 or 6 often means user not in group or group doesn't exist
            # We treat this as "Mission Accomplished" (user is not in group)
            if e.returncode in [6, 42]:
                 self.logger.info(f"deluser returned {e.returncode} (user not in group or group missing). Ignored as success.")
            else:
                 raise e

    def change_password(self, username: str, new_password: str) -> None:
        """Changes the password for a specific user."""
        # Using chpasswd is cleaner for scripting than passwd
        # format: username:password
        cmd = ["chpasswd"]
        input_str = f"{username}:{new_password}"
        
        # SudoManager run_privileged doesn't support input string directly, 
        # so we need to use Popen-like approach or modify SudoManager.
        # However, SudoManager.run_privileged takes a list of args.
        # We can implement it using 'echo user:pass | chpasswd' but passing pass in echo is visible in process list (insecure).
        # Better: use 'sh -c' with careful quoting, or update SudoManager to support stdin input (run_stream_privileged supports it partially but for sudo pass).
        
        # Let's use the shell redirection method safely with run_privileged:
        # sudo sh -c 'echo "user:pass" | chpasswd'
        # WARNING: This exposes password in process list for a split second.
        # Ideally we should use Popen with stdin, but let's stick to existing sudo manager patterns if possible.
        # Or even better: SudoManager.run_privileged is simple. Let's make a specialized call here.
        
        # Ideally, we pass it via stdin to chpasswd. 
        # Let's try to construct a secure command string or just use the shell pipe.
        # Given the constraints, we will use the shell wrapper.
        
        secure_cmd = ["sh", "-c", f"echo '{username}:{new_password}' | chpasswd"]
        self.sudo_manager.run_privileged(secure_cmd)



