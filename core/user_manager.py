import subprocess


class UserManager:
    def __init__(self, logger):
        self.logger = logger

    def _run(self, command: list[str]) -> subprocess.CompletedProcess:
        self.logger.info("Running: %s", " ".join(command))
        return subprocess.run(command, check=True, text=True, capture_output=True)

    def list_users(self) -> list[dict]:
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
                users.append(
                    {
                        "username": username,
                        "uid": uid_int,
                        "shell": shell,
                        "status": status,
                        "role": "Admin" if uid_int == 0 else "User",
                    }
                )
            return users
        except subprocess.CalledProcessError as exc:  # pragma: no cover - runtime
            self.logger.error("Failed to list users: %s", exc)
            return []

    def add_user(self, username: str, shell: str = "/bin/bash") -> None:
        self._run(["sudo", "useradd", "-m", "-s", shell, username])

    def remove_user(self, username: str) -> None:
        self._run(["sudo", "userdel", "-r", username])

    def lock_user(self, username: str) -> None:
        self._run(["sudo", "usermod", "-L", username])
