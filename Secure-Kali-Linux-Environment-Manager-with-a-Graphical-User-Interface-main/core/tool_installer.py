import logging
import os
import subprocess
import yaml
from typing import Callable, Any
from core.sudo_manager import SudoManager


class ToolInstaller:
    """
    Manages the installation, update, and removal of security tools using system package managers.
    
    This class handles the execution of privileged commands (via sudo) and streams the output
    back to the user interface via a callback function.
    """

    def __init__(self, logger: logging.Logger):
        """
        Initialize the ToolInstaller.

        Args:
            logger: Application logger instance for backend logging.
        """
        self.logger = logger
        self.env = os.environ.copy()
        # Ensure non-interactive mode for apt operations to prevent hanging on prompts
        self.env.setdefault("DEBIAN_FRONTEND", "noninteractive")
        self.sudo_manager = SudoManager()

    def load_catalog(self, path: str) -> dict[str, Any]:
        """
        Load tool entries from a YAML catalog file.
        """
        try:
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.error(f"Failed to load tools catalog: {e}")
            return {"categories": []}

    def install_tool(self, tool: dict[str, Any], log_callback: Callable[[str], None]) -> None:
        """
        Install a tool using apt-get.

        Args:
            tool: Dictionary containing tool metadata (must include 'package' key).
            log_callback: Function to call with output lines for UI display.
        """
        package = tool["package"]
        log_callback(f"[install] Updating apt cache for {package}")
        
        self.sudo_manager.run_stream_privileged(
            ["apt-get", "update"], log_callback, env=self.env
        )
        
        log_callback(f"[install] Installing {package}")
        
        self.sudo_manager.run_stream_privileged(
            ["apt-get", "install", "-y", package], log_callback, env=self.env
        )
        log_callback(f"[install] {package} process finished.")

    def update_tool(self, tool: dict[str, Any], log_callback: Callable[[str], None]) -> None:
        """
        Update an installed tool.

        Args:
            tool: Dictionary containing tool metadata.
            log_callback: Function to call with output lines for UI display.
        """
        package = tool["package"]
        log_callback(f"[update] Updating {package}")
        
        self.sudo_manager.run_stream_privileged(
            ["apt-get", "install", "--only-upgrade", "-y", package], log_callback, env=self.env
        )
        log_callback(f"[update] {package} process finished.")

    def remove_tool(self, tool: dict[str, Any], log_callback: Callable[[str], None]) -> None:
        """
        Remove a tool from the system.

        Args:
            tool: Dictionary containing tool metadata.
            log_callback: Function to call with output lines for UI display.
        """
        package = tool["package"]
        log_callback(f"[remove] Removing {package}")
        
        self.sudo_manager.run_stream_privileged(
            ["apt-get", "purge", "-y", package], log_callback, env=self.env
        )
        log_callback(f"[remove] {package} process finished.")


