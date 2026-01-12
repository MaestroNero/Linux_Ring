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
        proc = psutil.Process(pid)
        self.logger.info("Terminating PID %s", pid)
        proc.terminate()

    def get_system_metrics(self) -> dict:
        cpu = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        total_gb = round(mem.total / (1024**3), 1)
        used_gb = round(mem.used / (1024**3), 1)
        return {"cpu": cpu, "memory_used": used_gb, "memory_total": total_gb}
