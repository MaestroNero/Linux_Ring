import subprocess
import shutil
import os
import psutil
import logging

class SecurityAuditor:
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)

    def _log_error(self, msg):
        """Safe logging that handles None logger"""
        if self.logger:
            try:
                self.logger.error(msg)
            except:
                pass

    def scan_system(self):
        """
        Performs a system scan and returns a score (0-100) and a list of issues.
        """
        score = 100
        issues = []
        positive_notes = []

        # 1. Check Firewall (UFW)
        try:
            # Check if ufw is installed and active
            if shutil.which("ufw"):
                # Try without sudo first (if running as root)
                res = subprocess.run(["ufw", "status"], capture_output=True, text=True, timeout=5)
                if res.returncode != 0:
                    # Try with sudo
                    res = subprocess.run(["sudo", "-n", "ufw", "status"], capture_output=True, text=True, timeout=5)
                
                if "Status: active" in res.stdout:
                    positive_notes.append("✅ Firewall is active")
                else:
                    score -= 20
                    issues.append("🔥 Firewall (UFW) is inactive")
            else:
                score -= 20
                issues.append("⚠️ UFW is not installed")
        except subprocess.TimeoutExpired:
            issues.append("⏱️ Firewall check timed out")
        except Exception as e:
            self._log_error(f"Audit firewall failed: {e}")
            issues.append("❌ Could not verify firewall status")

        # 2. Check SSH Root Login
        try:
            sshd_config = "/etc/ssh/sshd_config"
            if os.path.exists(sshd_config):
                with open(sshd_config, "r") as f:
                    content = f.read()
                    if "PermitRootLogin yes" in content and "#PermitRootLogin yes" not in content:
                        score -= 25
                        issues.append("Root SSH login is currently allowed")
                    else:
                        positive_notes.append("Root SSH login disabled/restricted")
        except Exception as e:
            self._log_error(f"Audit SSH failed: {e}")

        # 3. Check for failed logins (simple check of /var/log/auth.log if readable)
        # Often requires root. Wrapper runs as root? "sudo" needed if not running as root.
        # We'll skip complex log parsing for stability, maybe just check if file exists and is huge?
        # Let's check open ports instead.

        # 3. Check Open Ports (Unnecessary listeners)
        try:
            conns = psutil.net_connections(kind='inet')
            listeners = [c for c in conns if c.status == 'LISTEN']
            listening_ports = [c.laddr.port for c in listeners]
            
            # Penalize known insecure ports if exposed
            unsafe_ports = [21, 23] # FTP, Telnet
            for p in unsafe_ports:
                if p in listening_ports:
                    score -= 15
                    issues.append(f"Insecure service listening on port {p}")
        except Exception as e:
            pass

        # 4. Check Updates (simulated/simple)
        # Real check: apt-get -s upgrade | grep "Inst" | wc -l
        # This can be slow.
        
        return score, issues, positive_notes
