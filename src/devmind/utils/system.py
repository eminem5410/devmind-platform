"""Utilidades para diagnostico general del sistema operativo.
Soporta Linux y Windows via psutil como fallback.
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
    platform_name: str = ""  # "Ubuntu 22.04", "Windows 10", etc
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
    """Obtiene informacion completa del sistema (cross-platform)."""
    info = SystemInfo()

    # OS basics (cross-platform)
    info.os_name = platform.system()
    info.os_version = platform.version()
    info.kernel = platform.release()
    info.arch = platform.machine()
    info.python_version = platform.python_version()

    # Platform details
    try:
        from devmind.utils.platform import detect_platform
        pinfo = detect_platform()
        info.platform_name = pinfo.display
    except Exception:
        info.platform_name = f"{info.os_name} {info.arch}"

    # CPU cores (cross-platform via os)
    info.cpu_cores = os.cpu_count() or 0

    # CPU name
    cpu_name = _detect_cpu_name()
    info.cpu_name = cpu_name

    # RAM
    ram_total, ram_used = _detect_ram()
    info.ram_total_gb = round(ram_total, 1) if ram_total else None
    info.ram_used_gb = round(ram_used, 1) if ram_used else None

    # Disk
    info.disk_free_gb = _detect_disk_free()

    # Tools
    info.docker_installed = shutil.which("docker") is not None
    info.git_installed = shutil.which("git") is not None
    info.pip_installed = shutil.which("pip") is not None or shutil.which("pip3") is not None
    info.venv_installed = shutil.which("python3") is not None or shutil.which("python") is not None

    return info


def _detect_cpu_name() -> Optional[str]:
    """Detect CPU model name (Linux /proc/cpuinfo -> psutil -> platform.processor)."""
    system = platform.system()

    # Linux: /proc/cpuinfo (most reliable on Linux)
    if system == "Linux":
        try:
            with open("/proc/cpuinfo", "r") as f:
                for line in f:
                    if line.startswith("model name"):
                        return line.split(":", 1)[1].strip()
        except (FileNotFoundError, PermissionError):
            pass

    # Windows/macOS: platform.processor or WMI
    name = platform.processor()
    if name:
        return name.strip()

    # Fallback: psutil
    try:
        import psutil
        freq = psutil.cpu_freq()
        if freq:
            return f"{psutil.cpu_count(logical=True)} cores @ {freq.max:.0f} MHz"
    except Exception:
        pass

    return None


def _detect_ram() -> tuple[Optional[float], Optional[float]]:
    """Detect RAM total and used in GB (cross-platform)."""
    system = platform.system()

    # Linux: /proc/meminfo (most detailed)
    if system == "Linux":
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
            if total_kb > 0:
                return (
                    total_kb / (1024 * 1024),
                    (total_kb - available_kb) / (1024 * 1024),
                )
        except (FileNotFoundError, PermissionError):
            pass

    # Cross-platform fallback: psutil
    try:
        import psutil
        mem = psutil.virtual_memory()
        return (
            mem.total / (1024 ** 3),
            (mem.total - mem.available) / (1024 ** 3),
        )
    except Exception:
        pass

    return None, None


def _detect_disk_free() -> Optional[float]:
    """Detect free disk space in GB (cross-platform)."""
    try:
        home = os.path.expanduser("~")
        stat = shutil.disk_usage(home)
        return round(stat.free / (1024 ** 3), 1)
    except Exception:
        pass
    return None
