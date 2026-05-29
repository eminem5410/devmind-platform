"""
Utilidades de deteccion y monitoreo de hardware GPU.
Soporta Linux y Windows.
"""

import os
import platform
import shutil
import subprocess
from dataclasses import dataclass
from typing import Optional


@dataclass
class GPUInfo:
    """Informacion de una GPU detectada."""
    vendor: str
    name: str
    driver_version: Optional[str] = None
    cuda_version: Optional[str] = None
    vram_total_mb: Optional[int] = None
    vram_used_mb: Optional[int] = None
    temperature_c: Optional[int] = None
    utilization_pct: Optional[int] = None

    @property
    def vendor_icon(self) -> str:
        icons = {"nvidia": "[green]NVIDIA[/green]", "amd": "[red]AMD[/red]", "intel": "[blue]Intel[/blue]"}
        return icons.get(self.vendor.lower(), f"[dim]{self.vendor}[/dim]")

    @property
    def vram_display(self) -> str:
        if self.vram_total_mb is None:
            return "[dim]N/A[/dim]"
        used = f"{self.vram_used_mb} MB" if self.vram_used_mb else "?"
        total = f"{self.vram_total_mb} MB"
        return f"{used} / {total}"

    @property
    def temp_display(self) -> str:
        if self.temperature_c is None:
            return "[dim]N/A[/dim]"
        t = self.temperature_c
        color = "green" if t < 60 else "yellow" if t < 80 else "red"
        return f"[{color}]{t} C[/{color}]"


def _run_cmd(cmd: list[str], timeout: int = 10) -> tuple[int, str]:
    """Ejecuta un comando y retorna (returncode, stdout)."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.returncode, result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return -1, ""


def detect_nvidia_gpu() -> list[GPUInfo]:
    """Detecta GPUs NVIDIA usando nvidia-smi (funciona en Linux y Windows)."""
    gpus = []
    if not shutil.which("nvidia-smi"):
        return gpus

    code, output = _run_cmd(
        ["nvidia-smi",
         "--query-gpu=name,driver_version,memory.total,memory.used,temperature.gpu,utilization.gpu",
         "--format=csv,noheader,nounits"]
    )
    if code != 0:
        return gpus

    for line in output.splitlines():
        if not line.strip():
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 6:
            continue
        gpus.append(GPUInfo(
            vendor="NVIDIA",
            name=parts[0],
            driver_version=parts[1],
            vram_total_mb=int(parts[2]) if parts[2].isdigit() else None,
            vram_used_mb=int(parts[3]) if parts[3].isdigit() else None,
            temperature_c=int(parts[4]) if parts[4].isdigit() else None,
            utilization_pct=int(parts[5]) if parts[5].isdigit() else None,
        ))

    if gpus:
        for gpu in gpus:
            gpu.cuda_version = "detectada (nvidia-smi OK)"

    return gpus


def detect_cuda_toolkit() -> Optional[str]:
    """Detecta CUDA Toolkit version (Linux + Windows)."""
    # nvcc funciona en ambas plataformas
    code, output = _run_cmd(["nvcc", "--version"])
    if code == 0 and "release" in output.lower():
        for part in output.split():
            if part.replace(".", "").isdigit():
                return part

    system = platform.system()

    if system == "Linux":
        # Linux: ldconfig
        code, output = _run_cmd(["ldconfig", "-p"])
        if code == 0 and "libcudart" in output.lower():
            for line in output.splitlines():
                if "libcudart" in line.lower():
                    for part in line.split():
                        if part.startswith("libcudart.so."):
                            ver = part.split("libcudart.so.")[1]
                            if ver:
                                return ver

    elif system == "Windows":
        # Windows: CUDA_PATH environment variable
        cuda_path = os.environ.get("CUDA_PATH", "")
        if cuda_path:
            # Extract version from path like "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.0"
            parts = cuda_path.split("\\")
            for part in reversed(parts):
                if part.startswith("v"):
                    ver = part[1:]
                    if ver.replace(".", "").isdigit():
                        return ver

        # Fallback: check nvcc in CUDA_PATH\bin
        if cuda_path:
            nvcc_path = os.path.join(cuda_path, "bin", "nvcc.exe")
            if os.path.exists(nvcc_path):
                code, output = _run_cmd([nvcc_path, "--version"])
                if code == 0 and "release" in output.lower():
                    for part in output.split():
                        if part.replace(".", "").isdigit():
                            return part

    return None


def detect_vulkan() -> Optional[str]:
    """Detecta si Vulkan esta disponible (Linux + Windows)."""
    # vulkaninfo funciona en ambas plataformas si esta instalado
    code, output = _run_cmd(["vulkaninfo", "--summary"])
    if code == 0:
        for line in output.splitlines():
            if "GPU id" in line or "deviceName" in line:
                return line.strip()

    system = platform.system()

    if system == "Linux":
        # Linux: ldconfig fallback
        code, output = _run_cmd(["ldconfig", "-p"])
        if code == 0 and "libvulkan" in output.lower():
            return "libvulkan detectada"

    elif system == "Windows":
        # Windows: Vulkan loader DLL
        vulkan_paths = [
            os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32", "vulkan-1.dll"),
        ]
        for vp in vulkan_paths:
            if os.path.exists(vp):
                return "vulkan-1.dll detectada"
        # WSL: usar libvulkan.so
        if "microsoft" in open("/proc/version", "r").read().lower() if os.path.exists("/proc/version") else "":
            return "Vulkan via WSL"

    return None


def detect_all_gpus() -> list[GPUInfo]:
    """Detecta todas las GPUs disponibles en el sistema."""
    gpus = detect_nvidia_gpu()
    if not gpus:
        # AMD: rocm-smi (Linux) o directo
        if shutil.which("rocm-smi"):
            code, output = _run_cmd(["rocm-smi", "--showproductname"])
            if code == 0:
                gpus.append(GPUInfo(vendor="AMD", name=output.strip()))
    return gpus
