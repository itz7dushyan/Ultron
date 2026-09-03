import psutil
import time
from typing import Dict, Any, List
from shared_state.state_manager import state_manager

class SystemTelemetry:
    """Monitors system performance and hardware telemetry for Ultron."""

    def get_system_vitals(self) -> Dict[str, Any]:
        """Collects CPU, RAM, Disk, Battery, and Uptime status."""
        cpu = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("C:")
        battery = psutil.sensors_battery()
        boot_time = psutil.boot_time()
        uptime_seconds = int(time.time() - boot_time)
        uptime_hours = round(uptime_seconds / 3600, 1)

        vitals = {
            "cpu_percent": cpu,
            "memory_percent": mem.percent,
            "memory_used_gb": round(mem.used / (1024**3), 1),
            "memory_total_gb": round(mem.total / (1024**3), 1),
            "disk_percent": disk.percent,
            "disk_free_gb": round(disk.free / (1024**3), 1),
            "battery_percent": battery.percent if battery else None,
            "battery_plugged": battery.power_plugged if battery else True,
            "uptime_hours": uptime_hours
        }

        state_manager.record_action(
            agent_name="SystemTelemetry",
            action="QUERY_VITALS",
            target="Windows 11 System",
            details=vitals,
            status="success"
        )
        return vitals

    def get_top_processes(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Returns top processes ordered by CPU and memory usage."""
        procs = []
        for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                info = p.info
                if info['name'] and info['name'] not in ('System Idle Process', 'System'):
                    procs.append({
                        "name": info['name'],
                        "pid": info['pid'],
                        "cpu": round(info['cpu_percent'] or 0.0, 1),
                        "memory": round(info['memory_percent'] or 0.0, 1)
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        procs.sort(key=lambda x: (x['memory'], x['cpu']), reverse=True)
        return procs[:limit]

    def format_speech_summary(self) -> str:
        """Returns a natural, concise spoken summary of system health."""
        v = self.get_system_vitals()
        batt_str = f", battery is at {v['battery_percent']}%" if v['battery_percent'] is not None else ""
        return (
            f"All systems are green. CPU is at {v['cpu_percent']}%, "
            f"memory is using {v['memory_used_gb']} of {v['memory_total_gb']} gigabytes{batt_str}."
        )

system_telemetry = SystemTelemetry()
