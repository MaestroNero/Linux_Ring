import shutil
import subprocess
import os
import yaml
import logging

class ToolInstaller:
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger("ToolInstaller")
        self.base_dir = "/opt/linux_ring_tools"
        self._sudo_password = None  # Will be set before operations
        if not os.path.exists(self.base_dir):
            try:
                os.makedirs(self.base_dir, exist_ok=True)
            except OSError:
                pass 

    def load_catalog(self, path: str) -> dict:
        with open(path, "r") as f:
            return yaml.safe_load(f)

    def install_tool(self, tool: dict, progress_callback=None):
        if progress_callback: progress_callback(f"Starting installation of {tool['name']}...")
        
        install_type = tool.get("type", "apt")
        package = tool.get("package")
        
        if install_type == "apt":
            self._install_apt(package, progress_callback)
        elif install_type == "git":
            self._install_git(package, tool.get("url"), progress_callback)

    def update_tool(self, tool: dict, progress_callback=None):
        """
        Smart update: checks origin, handles re-cloning if repo changed.
        """
        if progress_callback: progress_callback(f"Checking updates for {tool['name']}...")
        
        install_type = tool.get("type", "apt")
        
        if install_type == "apt":
            self._install_apt(tool["package"], progress_callback)
            
        elif install_type == "git":
            target_dir = os.path.join(self.base_dir, tool["package"])
            repo_url = tool.get("url")
            
            if os.path.exists(os.path.join(target_dir, ".git")):
                try:
                    res = subprocess.run(
                        ["git", "remote", "get-url", "origin"], 
                        cwd=target_dir, capture_output=True, text=True
                    )
                    current_remote = res.stdout.strip()
                    
                    if current_remote and repo_url and current_remote != repo_url:
                        if progress_callback: progress_callback(f"Repo URL changed! Migration needed...")
                        self.logger.warning(f"Remote mismatch for {tool['name']}. Old: {current_remote}, New: {repo_url}")
                        
                        backup_path = f"{target_dir}_backup"
                        if os.path.exists(backup_path): shutil.rmtree(backup_path)
                        shutil.move(target_dir, backup_path)
                        
                        self._install_git(tool["package"], repo_url, progress_callback)
                        if progress_callback: progress_callback("Migration complete. Old version backed up.")
                    else:
                        if progress_callback: progress_callback("Pulling latest changes from git...")
                        subprocess.run(["git", "pull"], cwd=target_dir, check=True)
                        
                except Exception as e:
                    self.logger.error(f"Git update failed: {e}")
                    raise
            else:
                self._install_git(tool["package"], repo_url, progress_callback)

    def _is_root(self):
        """Check if running as root"""
        return os.geteuid() == 0
    
    def _run_sudo_cmd(self, cmd: list, progress_callback=None) -> bool:
        """Run command with sudo, using cached password if available"""
        if self._is_root():
            full_cmd = cmd
        elif self._sudo_password:
            full_cmd = ["sudo", "-S"] + cmd
        else:
            full_cmd = ["sudo"] + cmd
        
        if progress_callback:
            progress_callback(f"Running: {' '.join(cmd)}")
        
        proc = subprocess.Popen(
            full_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        
        # Send password if we have one
        if self._sudo_password and not self._is_root():
            proc.stdin.write(self._sudo_password + "\n")
            proc.stdin.flush()
        
        for line in proc.stdout:
            line = line.strip()
            if line and "password" not in line.lower() and "[sudo]" not in line:
                if progress_callback:
                    progress_callback(line)
        
        proc.wait()
        return proc.returncode == 0
    
    def remove_tool(self, tool: dict, progress_callback=None):
        if progress_callback: progress_callback(f"Removing {tool['name']}...")
        install_type = tool.get("type", "apt")
        
        if install_type == "apt":
            if not self._run_sudo_cmd(["apt-get", "remove", "-y", tool["package"]], progress_callback):
                raise Exception(f"Failed to remove {tool['package']}")
        elif install_type == "git":
            target_dir = os.path.join(self.base_dir, tool["package"])
            if os.path.exists(target_dir):
                shutil.rmtree(target_dir)

    def _install_apt(self, package, progress_callback):
        if progress_callback: progress_callback(f"Installing {package}...")
        if not self._run_sudo_cmd(["apt-get", "install", "-y", package], progress_callback):
            raise Exception("Apt install failed")

    def _install_git(self, dirname, url, progress_callback):
        target = os.path.join(self.base_dir, dirname)
        if os.path.exists(target):
            if progress_callback: progress_callback("Directory exists, pulling changes...")
            subprocess.run(["git", "pull"], cwd=target, check=True)
        else:
            if progress_callback: progress_callback(f"Cloning {url}...")
            if not self._run_sudo_cmd(["git", "clone", url, target], progress_callback):
                raise Exception("Git clone failed")
            
            req_file = os.path.join(target, "requirements.txt")
            if os.path.exists(req_file):
                if progress_callback: progress_callback("Installing python dependencies...")
                self._run_sudo_cmd(["pip3", "install", "-r", req_file], progress_callback)
