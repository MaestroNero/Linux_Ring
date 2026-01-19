import psutil


class ProcessManager:
    def __init__(self, logger):
        self.logger = logger

    def list_processes(self, limit: int = 50) -> list[dict]:
        processes = []
        for proc in psutil.process_iter(attrs=["pid", "name", "username", "cpu_percent", "memory_percent", "status"]):
            info = proc.info
            processes.append(
                {
                    "pid": info.get("pid"),
                    "name": info.get("name") or "",
                    "user": info.get("username") or "",
                    "cpu": info.get("cpu_percent") or 0.0,
                    "memory": info.get("memory_percent") or 0.0,
                    "status": info.get("status") or "",
                }
            )
        processes.sort(key=lambda p: p["cpu"], reverse=True)
        return processes[:limit]

    def terminate_process(self, pid: int) -> None:
        try:
            proc = psutil.Process(pid)
            self.logger.info("Terminating PID %s...", pid)
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except psutil.TimeoutExpired:
                self.logger.warning("PID %s did not terminate gracefully, killing...", pid)
                proc.kill()
        except psutil.NoSuchProcess:
            self.logger.warning("Failed to terminate: PID %s does not exist.", pid)
        except psutil.AccessDenied:
            self.logger.error("Failed to terminate: Access denied for PID %s.", pid)
        except Exception as e:
            self.logger.error("Error terminating PID %s: %s", pid, str(e))

    def get_system_metrics(self) -> dict:
        cpu = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        total_gb = round(mem.total / (1024**3), 1)
        used_gb = round(mem.used / (1024**3), 1)
        return {"cpu": cpu, "memory_used": used_gb, "memory_total": total_gb}
