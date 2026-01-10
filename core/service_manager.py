import subprocess


class ServiceManager:
    def __init__(self, logger):
        self.logger = logger

    def _run(self, command: list[str]) -> subprocess.CompletedProcess:
        self.logger.info("Running: %s", " ".join(command))
        return subprocess.run(command, check=True, text=True, capture_output=True)

    def list_services(self) -> list[dict]:
        try:
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
        except subprocess.CalledProcessError as exc:  # pragma: no cover - runtime
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
            services.append(
                {"name": name, "status": status, "startup": "enabled", "port": "-", "risk": risk}
            )
        return services

    def start_service(self, name: str) -> None:
        self._run(["sudo", "systemctl", "start", name])

    def stop_service(self, name: str) -> None:
        self._run(["sudo", "systemctl", "stop", name])

    def restart_service(self, name: str) -> None:
        self._run(["sudo", "systemctl", "restart", name])

    def _risk_for_service(self, name: str) -> str:
        critical = {"ssh.service": "Medium", "postgresql.service": "Medium"}
        risky = {"vsftpd.service": "High", "apache2.service": "Medium"}
        if name in critical:
            return critical[name]
        if name in risky:
            return risky[name]
        return "Low"
