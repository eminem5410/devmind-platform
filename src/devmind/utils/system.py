"""
Utilidades para diagnostico general del sistema operativo.
"""

import os
import platform
import shutil
import subprocess
from dataclasses import dataclass
from typing import Optional


@dataclass
class SystemInfo:
    """Informacion general del sistema."""
    os_name: str = ""
    os_version: str = ""
    kernel: str = ""
    arch: str = ""
    python_version: str = ""
    ram_total_gb: Optional[float] = None
    ram_used_gb: Optional[float] = None
    cpu_name: Optional[str] = None
    cpu_cores: int = 0
    disk_free_gb: Optional[float] = None
    docker_installed: bool = False
    git_installed: bool = False
    pip_installed: bool = False
    venv_installed: bool = False


def _run(cmd: list[str], timeout: int = 10) -> tuple[int, str]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return -1, ""


def get_system_info() -> SystemInfo:
    """Obtiene informacion completa del sistema."""
    info = SystemInfo()

    # OS
    info.os_name = platform.system()
    info.os_version = platform.version()
    info.kernel = platform.release()
    info.arch = platform.machine()

    # Python
    info.python_version = platform.python_version()

    # RAM (desde /proc/meminfo en Linux)
    try:
        with open("/proc/meminfo", "r") as f:
            meminfo = {}
            for line in f:
                parts = line.split()
                if len(parts) >= 2:
                    key = parts[0].rstrip(":")
                    meminfo[key] = int(parts[1])
            total_kb = meminfo.get("MemTotal", 0)
            available_kb = meminfo.get("MemAvailable", meminfo.get("MemFree", 0))
            info.ram_total_gb = round(total_kb / (1024 * 1024), 1)
            info.ram_used_gb = round((total_kb - available_kb) / (1024 * 1024), 1)
    except (FileNotFoundError, PermissionError):
        pass

    # CPU
    try:
        with open("/proc/cpuinfo", "r") as f:
            lines = f.readlines()
        info.cpu_cores = os.cpu_count() or 0
        for line in lines:
            if line.startswith("model name"):
                info.cpu_name = line.split(":", 1)[1].strip()
                break
    except (FileNotFoundError, PermissionError):
        pass

    # Disco (directorio actual)
    try:
        stat = shutil.disk_usage("/home")
        info.disk_free_gb = round(stat.free / (1024 ** 3), 1)
    except Exception:
        pass

    # Herramientas clave
    info.docker_installed = shutil.which("docker") is not None
    info.git_installed = shutil.which("git") is not None
    info.pip_installed = shutil.which("pip") is not None or shutil.which("pip3") is not None
    info.venv_installed = shutil.which("python3 -m venv".split()[0]) is not None

    return info
