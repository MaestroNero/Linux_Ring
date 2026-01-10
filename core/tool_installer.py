import os
import subprocess


class ToolInstaller:
    def __init__(self, logger):
        self.logger = logger
        self.env = os.environ.copy()
        self.env.setdefault("DEBIAN_FRONTEND", "noninteractive")

    def install_tool(self, tool: dict, log) -> None:
        package = tool["package"]
        log(f"[install] Updating apt cache for {package}")
        self._run_stream(["sudo", "apt-get", "update"], log)
        log(f"[install] Installing {package}")
        self._run_stream(["sudo", "apt-get", "install", "-y", package], log)
        log(f"[install] {package} installed")

    def update_tool(self, tool: dict, log) -> None:
        package = tool["package"]
        log(f"[update] Updating {package}")
        self._run_stream(["sudo", "apt-get", "install", "--only-upgrade", "-y", package], log)
        log(f"[update] {package} updated")

    def remove_tool(self, tool: dict, log) -> None:
        package = tool["package"]
        log(f"[remove] Removing {package}")
        self._run_stream(["sudo", "apt-get", "purge", "-y", package], log)
        log(f"[remove] {package} removed")

    def _run_stream(self, command: list[str], log) -> None:
        self.logger.info("Running: %s", " ".join(command))
        proc = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=self.env
        )
        assert proc.stdout
        for line in proc.stdout:
            log(line.strip())
        proc.wait()
        if proc.returncode != 0:  # pragma: no cover - runtime
            raise subprocess.CalledProcessError(proc.returncode, command)
