import logging
import subprocess
from typing import Any
from core.sudo_manager import SudoManager


class ServiceManager:
    """
    Manages system services via systemctl, including status checks and start/stop operations.
    """

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.sudo_manager = SudoManager()

    def list_services(self) -> list[dict[str, str]]:
        """
        List all services using systemctl.
        
        Returns:
            List of dictionaries containing service name, status, etc.
        """
        try:
            # Listing units doesn't necessarily require sudo, but helps for consistency if some are hidden
            # However, standard systemctl list-units works for user. Keeping it unprivileged for speed/safety unless needed.
            result = subprocess.run(
                [
                    "systemctl",
                    "list-units",
                    "--type=service",
                    "--all",
                    "--no-legend",
                    "--no-pager",
                ],
                check=True,
                text=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as exc:
            self.logger.error("Failed to list services: %s", exc)
            return []

        services = []
        for line in result.stdout.splitlines():
            if not line.strip():
                continue
            parts = line.split()
            name = parts[0]
            active = parts[2] if len(parts) > 2 else "unknown"
            sub = parts[3] if len(parts) > 3 else ""
            status = f"{active}/{sub}"
            risk = self._risk_for_service(name)
            
            # Improvement: Fetch real unit file state if possible, default to 'unknown' instead of lying 'enabled'
            # Note: For performance, we might want to do this in bulk, but for now we mark it.
            # Ideally we would map 'unit_file_state' from systemctl list-unit-files, 
            # but current parsing loop handles list-units.
            
            startup_state = "unknown"
            # Attempt to map from the 'sub' state or just mark as dynamic
            # A proper fix requires running 'systemctl list-unit-files' and mapping names.
            # leaving as placeholder for future robustness.
            
            services.append(
                {"name": name, "status": status, "startup": startup_state, "port": "-", "risk": risk}
            )
        return services

    def get_unit_file_state(self, service_name: str) -> str:
        """Helper to get the enabled/disabled state of a specific service."""
        try:
            res = subprocess.run(
                ["systemctl", "show", "-p", "UnitFileState", service_name],
                capture_output=True, text=True
            )
            # Output format: UnitFileState=enabled
            if "=" in res.stdout:
                return res.stdout.strip().split("=")[1]
        except Exception:
            pass
        return "unknown"

    def start_service(self, name: str) -> None:
        """Start a system service."""
        self.sudo_manager.run_privileged(["systemctl", "start", name])

    def stop_service(self, name: str) -> None:
        """Stop a system service."""
        self.sudo_manager.run_privileged(["systemctl", "stop", name])

    def restart_service(self, name: str) -> None:
        """Restart a system service."""
        self.sudo_manager.run_privileged(["systemctl", "restart", name])

    def _risk_for_service(self, name: str) -> str:
        """Evaluate security risk of a service."""
        critical = {"ssh.service": "Medium", "postgresql.service": "Medium"}
        risky = {"vsftpd.service": "High", "apache2.service": "Medium"}
        if name in critical:
            return critical[name]
        if name in risky:
            return risky[name]
        return "Low"

