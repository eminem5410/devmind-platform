"""
Logger estructurado JSON para DevMind.

Todos los eventos de DevMind se registran en JSON para:
- Debugging de issues reportados
- Rollback (reproducir secuencia de operaciones)
- Telemetry y analisis de uso
- Audit trail de reparaciones

Los logs se guardan en ~/.devmind/logs/devmind.log
Rotacion automatica cuando el archivo supera 5MB.
"""

from __future__ import annotations

import json
import os
import platform
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# Directorio de logs
DEVMIND_HOME = Path.home() / ".devmind"
LOGS_DIR = DEVMIND_HOME / "logs"
LOG_FILE = LOGS_DIR / "devmind.log"
MAX_LOG_SIZE = 5 * 1024 * 1024  # 5MB


def _ensure_log_dir() -> None:
    """Asegura que el directorio de logs existe."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)


def _rotate_log() -> None:
    """Rota el log actual si supera el tamano maximo."""
    if not LOG_FILE.exists():
        return
    if LOG_FILE.stat().st_size > MAX_LOG_SIZE:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        rotated = LOG_FILE.parent / f"devmind_{timestamp}.log"
        LOG_FILE.rename(rotated)
        # Mantener solo los ultimos 5 logs rotados
        rotated_files = sorted(LOG_FILE.parent.glob("devmind_*.log"))
        for old in rotated_files[:-5]:
            old.unlink()


def get_session_id() -> str:
    """Retorna o genera un session ID unico."""
    sid_file = DEVMIND_HOME / ".session_id"
    if sid_file.exists():
        return sid_file.read_text().strip()
    sid = uuid.uuid4().hex[:12]
    DEVMIND_HOME.mkdir(parents=True, exist_ok=True)
    sid_file.write_text(sid)
    return sid


class DevMindLogger:
    """Logger estructurado que escribe eventos JSON al archivo de log.

    Cada entrada tiene la estructura:
    {
        "timestamp": "2024-01-15T10:30:00Z",
        "session_id": "a1b2c3d4e5f6",
        "event": "command_start",
        "command": "doctor",
        "data": { ... }
    }

    Eventos:
        command_start    — Un comando de DevMind inicio
        command_end      — Un comando de DevMind finalizo
        command_error    — Un comando fallo con error
        doctor_run       — Diagnostico ejecutado (resumen)
        repair_action    — Una reparacion fue ejecutada
        snapshot_created — Un snapshot fue creado
        benchmark_run    — Un benchmark fue ejecutado (resultados)
        model_download   — Un modelo fue descargado
    """

    def __init__(self):
        _ensure_log_dir()
        self._session_id = get_session_id()
        self._hostname = platform.node()

    def _write(self, event: str, data: Optional[dict] = None, level: str = "INFO") -> None:
        """Escribe una entrada de log estructurada."""
        _rotate_log()

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": self._session_id,
            "hostname": self._hostname,
            "event": event,
            "level": level,
        }
        if data:
            entry["data"] = data

        try:
            with open(LOG_FILE, "a") as f:
                f.write(json.dumps(entry, default=str) + "\n")
        except (IOError, PermissionError):
            pass  # Silent fail — los logs no deben romper el flujo

    def command_start(self, command: str, args: Optional[dict] = None) -> None:
        """Registra el inicio de un comando."""
        self._write("command_start", {
            "command": command,
            "args": args or {},
        })

    def command_end(self, command: str, duration_s: float, success: bool = True) -> None:
        """Registra el fin de un comando."""
        self._write(
            "command_end" if success else "command_error",
            {
                "command": command,
                "duration_s": round(duration_s, 2),
            },
            level="INFO" if success else "ERROR",
        )

    def doctor_run(self, health_score: int, total_checks: int, warnings: int,
                   errors: int, repairable: int) -> None:
        """Registra un diagnostico ejecutado."""
        self._write("doctor_run", {
            "health_score": health_score,
            "total_checks": total_checks,
            "warnings": warnings,
            "errors": errors,
            "repairable": repairable,
        })

    def repair_action(self, target: str, action: str, success: bool,
                      detail: Optional[str] = None) -> None:
        """Registra una accion de reparacion."""
        self._write("repair_action", {
            "target": target,
            "action": action,
            "success": success,
            "detail": detail,
        }, level="INFO" if success else "WARNING")

    def snapshot_created(self, filepath: str, format: str, size_bytes: int) -> None:
        """Registra la creacion de un snapshot."""
        self._write("snapshot_created", {
            "filepath": filepath,
            "format": format,
            "size_bytes": size_bytes,
        })

    def benchmark_run(self, model: str, tokens_per_sec: float, total_tokens: int,
                      ttft_ms: float, peak_ram_mb: float, prompt: str,
                      duration_s: float) -> None:
        """Registra un benchmark ejecutado."""
        self._write("benchmark_run", {
            "model": model,
            "tokens_per_sec": round(tokens_per_sec, 2),
            "total_tokens": total_tokens,
            "ttft_ms": round(ttft_ms, 2),
            "peak_ram_mb": round(peak_ram_mb, 1),
            "prompt_length": len(prompt),
            "duration_s": round(duration_s, 2),
        })

    def model_download(self, model: str, success: bool, duration_s: Optional[float] = None) -> None:
        """Registra una descarga de modelo."""
        self._write("model_download", {
            "model": model,
            "success": success,
            "duration_s": round(duration_s, 2) if duration_s else None,
        }, level="INFO" if success else "ERROR")


# Singleton global
logger = DevMindLogger()
