import subprocess


class ProfileManager:
    def __init__(self, logger, user_manager, service_manager, firewall_manager, tool_installer):
        self.logger = logger
        self.user_manager = user_manager
        self.service_manager = service_manager
        self.firewall_manager = firewall_manager
        self.tool_installer = tool_installer
        self.profiles = self._build_profiles()

    def _build_profiles(self) -> list[dict]:
        return [
            {
                "id": "student",
                "name": "Student Secure Environment",
                "summary": "Lock down SSH, disable noisy services, enable firewall, and keep educational tools.",
                "actions": [
                    {"category": "SSH", "description": "Disable root SSH login"},
                    {"category": "Services", "description": "Stop and disable non-essential daemons"},
                    {"category": "Firewall", "description": "Close unused ports and enforce ufw"},
                    {"category": "Packages", "description": "Install educational tooling only"},
                ],
                "apply": self._apply_student,
            },
            {
                "id": "pentest",
                "name": "Pentesting Lab Environment",
                "summary": "Enable databases, allow lab ports, and install pentest tooling.",
                "actions": [
                    {"category": "Services", "description": "Enable PostgreSQL and supporting services"},
                    {"category": "Firewall", "description": "Allow lab ports, restrict external exposure"},
                    {"category": "Packages", "description": "Install pentesting utilities"},
                ],
                "apply": self._apply_pentest,
            },
            {
                "id": "hardened",
                "name": "Hardened Secure Environment",
                "summary": "Tighten accounts, stop unused services, strict firewall rules, harden file permissions.",
                "actions": [
                    {"category": "Accounts", "description": "Lock non-essential users"},
                    {"category": "Services", "description": "Stop and disable weak services"},
                    {"category": "Firewall", "description": "Allow SSH only, deny all else"},
                    {"category": "Permissions", "description": "Tighten sensitive file permissions"},
                ],
                "apply": self._apply_hardened,
            },
        ]

    def list_profiles(self) -> list[dict]:
        return self.profiles

    def apply_profile(self, profile_id: str, log) -> None:
        profile = next((p for p in self.profiles if p["id"] == profile_id), None)
        if not profile:
            raise ValueError(f"Unknown profile {profile_id}")
        log(f"Applying profile: {profile['name']}")
        profile["apply"](log)
        log(f"Profile {profile['name']} applied")

    # Profile implementations -------------------------------------------------
    def _apply_student(self, log) -> None:
        self._disable_root_ssh(log)
        self._disable_services(["apache2.service", "avahi-daemon.service", "cups.service"], log)
        self.firewall_manager.enable_firewall(log)
        self.firewall_manager.close_ports([21, 23, 25, 111], log)
        self._install_packages(["wireshark", "nmap"], log)

    def _apply_pentest(self, log) -> None:
        self._enable_services(["postgresql.service"], log)
        self.firewall_manager.enable_firewall(log)
        self.firewall_manager.allow_ports([22, 80, 443, 5432], log)
        self._install_packages(["metasploit-framework", "sqlmap", "john"], log)

    def _apply_hardened(self, log) -> None:
        self._lock_users(["guest", "test"], log)
        self._disable_services(["apache2.service", "cups.service", "avahi-daemon.service"], log)
        self.firewall_manager.enable_firewall(log)
        self.firewall_manager.allow_ports([22], log)
        self.firewall_manager.close_all_except([22], log)
        self._harden_permissions(log)

    # Helpers -----------------------------------------------------------------
    def _install_packages(self, packages: list[str], log) -> None:
        if not packages:
            return
        log(f"Installing packages: {', '.join(packages)}")
        cmd = ["sudo", "apt-get", "install", "-y"] + packages
        self._run(cmd, log)

    def _disable_root_ssh(self, log) -> None:
        log("Disabling root SSH login")
        cmd = [
            "sudo",
            "bash",
            "-c",
            "echo 'PermitRootLogin no' > /etc/ssh/sshd_config.d/secure-kali.conf",
        ]
        self._run(cmd, log)
        self._run(["sudo", "systemctl", "restart", "ssh"], log)

    def _disable_services(self, services: list[str], log) -> None:
        for svc in services:
            log(f"Stopping {svc}")
            try:
                self.service_manager.stop_service(svc)
            except Exception:
                pass
            self._run(["sudo", "systemctl", "disable", svc], log)

    def _enable_services(self, services: list[str], log) -> None:
        for svc in services:
            log(f"Enabling {svc}")
            self._run(["sudo", "systemctl", "enable", "--now", svc], log)

    def _lock_users(self, users: list[str], log) -> None:
        for user in users:
            log(f"Locking user {user}")
            try:
                self.user_manager.lock_user(user)
            except Exception:
                self._run(["sudo", "passwd", "-l", user], log)

    def _harden_permissions(self, log) -> None:
        sensitive = ["/etc/ssh", "/etc/hosts.allow", "/etc/hosts.deny"]
        for path in sensitive:
            log(f"Hardening permissions for {path}")
            self._run(["sudo", "chmod", "-R", "go-rwx", path], log)

    def _run(self, command: list[str], log) -> None:
        self.logger.info("Running: %s", " ".join(command))
        result = subprocess.run(command, text=True, capture_output=True)
        if result.stdout:
            log(result.stdout.strip())
        if result.stderr:
            log(result.stderr.strip())
        if result.returncode != 0:  # pragma: no cover - runtime
            raise subprocess.CalledProcessError(result.returncode, command, result.stdout, result.stderr)
