"""
Utilidades para verificar el estado de Ollama y modelos locales.
"""

import shutil
import subprocess
from dataclasses import dataclass
from typing import Optional


@dataclass
class OllamaStatus:
    """Estado de Ollama en el sistema."""
    installed: bool
    running: bool
    version: Optional[str] = None
    models: list[str] = None
    error: Optional[str] = None

    def __post_init__(self):
        if self.models is None:
            self.models = []


def _run(cmd: list[str], timeout: int = 10) -> tuple[int, str]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return -1, ""


def check_ollama() -> OllamaStatus:
    """Verifica el estado completo de Ollama."""
    if not shutil.which("ollama"):
        return OllamaStatus(installed=False, running=False)

    status = OllamaStatus(installed=True, running=False)

    # Version
    code, out = _run(["ollama", "--version"])
    if code == 0 and out:
        # "ollama version is 0.24.0" -> "0.24.0"
        parts = out.strip().split()
        if len(parts) >= 3 and "version" in out.lower():
            status.version = parts[-1]
        else:
            status.version = out.strip()

    # Verificar si el servidor responde
    code, out = _run(["ollama", "list"])
    if code == 0:
        status.running = True
        for line in out.splitlines():
            parts = line.split()
            if parts and parts[0].upper() != "NAME" and "/" in parts[0]:
                status.models.append(parts[0])
            elif parts and parts[0].upper() != "NAME" and not parts[0].isupper():
                status.models.append(parts[0])
    else:
        status.error = "Ollama instalado pero el servidor no responde (ejecuta 'ollama serve')"

    return status
