import subprocess


class FirewallManager:
    def __init__(self, logger):
        self.logger = logger

    def _run(self, command: list[str]) -> subprocess.CompletedProcess:
        self.logger.info("Running: %s", " ".join(command))
        return subprocess.run(command, check=True, text=True, capture_output=True)

    def enable_firewall(self, log) -> None:
        log("Enabling ufw with deny-by-default policy")
        self._run(["sudo", "ufw", "default", "deny", "incoming"])
        self._run(["sudo", "ufw", "default", "allow", "outgoing"])
        self._run(["sudo", "ufw", "--force", "enable"])

    def allow_ports(self, ports: list[int], log) -> None:
        for port in ports:
            log(f"Allowing port {port}/tcp")
            self._run(["sudo", "ufw", "allow", f"{port}/tcp"])

    def close_ports(self, ports: list[int], log) -> None:
        for port in ports:
            log(f"Denying port {port}/tcp")
            self._run(["sudo", "ufw", "deny", f"{port}/tcp"])

    def close_all_except(self, allowed: list[int], log) -> None:
        log("Closing all ports except minimal allow list")
        self._run(["sudo", "ufw", "--force", "reset"])
        self.enable_firewall(log)
        self.allow_ports(allowed, log)
