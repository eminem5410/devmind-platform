"""
Utilidades para verificar el estado de Docker y contenedores.
"""

import shutil
import subprocess
from dataclasses import dataclass
from typing import Optional


@dataclass
class DockerStatus:
    """Estado de Docker en el sistema."""
    installed: bool
    running: bool
    version: Optional[str] = None
    compose_version: Optional[str] = None
    containers_running: int = 0
    containers_total: int = 0
    images_count: int = 0
    error: Optional[str] = None


def _run(cmd: list[str], timeout: int = 10) -> tuple[int, str]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return -1, ""


def check_docker() -> DockerStatus:
    """Verifica el estado completo de Docker."""
    if not shutil.which("docker"):
        return DockerStatus(installed=False, running=False)

    status = DockerStatus(installed=True, running=False)

    # Version
    code, out = _run(["docker", "--version"])
    if code == 0 and out:
        status.version = out.replace("Docker version ", "").split(",")[0].strip()
        status.running = True
    else:
        status.error = "Docker instalado pero el daemon no esta ejecutando"
        return status

    # Docker Compose
    for cmd_name in ["docker-compose", "docker"]:
        if cmd_name == "docker":
            code, out = _run(["docker", "compose", "version"])
        else:
            code, out = _run(["docker-compose", "--version"])
        if code == 0 and out:
            ver = out.split("version")[-1].strip().split(",")[0].strip().split()[0]
            status.compose_version = ver
            break

    # Contenedores
    code, out = _run(["docker", "ps", "-q"])
    if code == 0 and out:
        status.containers_running = len(out.splitlines())

    code, out = _run(["docker", "ps", "-aq"])
    if code == 0 and out:
        status.containers_total = len(out.splitlines())

    # Imagenes
    code, out = _run(["docker", "images", "-q"])
    if code == 0 and out:
        status.images_count = len(out.splitlines())

    return status
