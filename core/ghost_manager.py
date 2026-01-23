import subprocess
import re
import logging

class GhostManager:
    def __init__(self, logger):
        self.logger = logger
        self.is_ghost_active = False

    def get_interfaces(self):
        """Get list of network interfaces excluding loopback."""
        interfaces = []
        try:
            res = subprocess.run(["ip", "-o", "link", "show"], capture_output=True, text=True)
            for line in res.stdout.splitlines():
                # Format: 1: lo: <LOOPBACK,...>
                parts = line.split(": ")
                if len(parts) >= 2:
                    ifname = parts[1].split("@")[0] # handle vlan/virt pairs
                    if ifname != "lo":
                        interfaces.append(ifname)
        except Exception as e:
            self.logger.error(f"Failed to list interfaces: {e}")
        return interfaces

    def enable_ghost_mode(self, interface: str):
        """
        1. Down interface
        2. Macchanger random
        3. Up interface
        """
        try:
            self.logger.info(f"Enabling Ghost Mode on {interface}")
            subprocess.run(["sudo", "ip", "link", "set", "dev", interface, "down"], check=True)
            
            # Use macchanger if available, else manual (harder properly)
            # Assuming macchanger is standard in this context (Kali-tool manager)
            subprocess.run(["sudo", "macchanger", "-r", interface], check=True)
            
            subprocess.run(["sudo", "ip", "link", "set", "dev", interface, "up"], check=True)
            self.is_ghost_active = True
            return True, "Ghost Mode Enabled: MAC Address Spoofed"
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Ghost mode failed: {e}")
            return False, f"Failed to enable Ghost Mode: {e}"
        except FileNotFoundError:
             return False, "macchanger tool not found. Please install it."

    def disable_ghost_mode(self, interface: str):
        """
        Reset MAC to permanent
        """
        try:
            self.logger.info(f"Disabling Ghost Mode on {interface}")
            subprocess.run(["sudo", "ip", "link", "set", "dev", interface, "down"], check=True)
            subprocess.run(["sudo", "macchanger", "-p", interface], check=True)
            subprocess.run(["sudo", "ip", "link", "set", "dev", interface, "up"], check=True)
            self.is_ghost_active = False
            return True, "Ghost Mode Disabled: MAC Restored"
        except Exception as e:
            return False, str(e)
