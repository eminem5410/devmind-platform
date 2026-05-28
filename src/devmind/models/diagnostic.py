"""
Modelos de datos para diagnosticos del sistema DevMind.

Todos los modelos usan Pydantic v2 para validacion y serializacion.
Estos modelos son la base tanto para la salida Rich como --json.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ── Enums ──────────────────────────────────────────────────────────────────

class Severity(str, Enum):
    """Niveles de severidad para diagnosticos.

    INFO     — Todo bien, informativo.
    WARNING  — Funciona pero puede mejorar.
    ERROR    — Algo no funciona correctamente.
    CRITICAL — Impide el funcionamiento de una feature clave.
    """
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

    @property
    def color(self) -> str:
        """Color Rich asociado al nivel."""
        return {
            Severity.INFO: "cyan",
            Severity.WARNING: "yellow",
            Severity.ERROR: "red",
            Severity.CRITICAL: "bold red",
        }[self]

    @property
    def icon(self) -> str:
        """Icono para la terminal."""
        return {
            Severity.INFO: "[cyan]i[/cyan]",
            Severity.WARNING: "[yellow]![/yellow]",
            Severity.ERROR: "[red]x[/red]",
            Severity.CRITICAL: "[bold red]!![/bold red]",
        }[self]

    @property
    def weight(self) -> int:
        """Peso numerico para calculo de health score."""
        return {
            Severity.INFO: 0,
            Severity.WARNING: 1,
            Severity.ERROR: 2,
            Severity.CRITICAL: 3,
        }[self]


# ── Check individual ───────────────────────────────────────────────────────

class DiagnosticCheck(BaseModel):
    """Resultado individual de un check de diagnostico."""
    name: str = Field(description="Nombre legible del check")
    category: str = Field(description="Categoria: system, gpu, docker, ollama, tools")
    severity: Severity = Field(description="Nivel de severidad")
    status: str = Field(default="unknown", description="ok, missing, error, warning")
    value: Optional[str] = Field(default=None, description="Valor detectado")
    message: Optional[str] = Field(default=None, description="Mensaje descriptivo")


# ── Recomendacion ──────────────────────────────────────────────────────────

class Recommendation(BaseModel):
    """Recomendacion inteligente generada a partir del diagnostico."""
    severity: Severity = Field(description="Prioridad de la recomendacion")
    category: str = Field(description="Area relacionada")
    title: str = Field(description="Titulo corto")
    message: str = Field(description="Descripcion detallada")
    action: Optional[str] = Field(default=None, description="Accion sugerida en texto")
    command: Optional[str] = Field(default=None, description="Comando a ejecutar")
    repairable: bool = Field(
        default=False,
        description="Si devmind repair puede resolverlo automaticamente",
    )


# ── Datos del sistema ─────────────────────────────────────────────────────

class SystemData(BaseModel):
    """Datos basicos del sistema operativo y hardware."""
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


# ── Reporte completo ──────────────────────────────────────────────────────

class DiagnosticReport(BaseModel):
    """Reporte completo de diagnostico del sistema.

    Este modelo es la fuente de verdad para tanto la salida Rich
    como la salida --json. Toda la logica de recoleccion llena
    este modelo, y luego se renderiza segun el modo solicitado.
    """
    version: str = "0.4.0"
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    system: SystemData = Field(default_factory=SystemData)
    checks: list[DiagnosticCheck] = Field(default_factory=list)
    recommendations: list[Recommendation] = Field(default_factory=list)
    summary: dict = Field(default_factory=dict)

    def compute_summary(self) -> dict:
        """Calcula el resumen a partir de checks y recomendaciones."""
        total = len(self.checks)
        counts = {s: 0 for s in Severity}
        for check in self.checks:
            counts[check.severity] += 1

        # Health score: 100 si todo INFO, baja con cada issue
        weight_sum = sum(check.severity.weight for check in self.checks)
        max_weight = total * 3  # CRITICAL = 3
        health = max(0, round(100 * (1 - weight_sum / max_weight))) if max_weight > 0 else 100

        # Recomendaciones reparables
        repairable = sum(1 for r in self.recommendations if r.repairable)

        self.summary = {
            "total_checks": total,
            "info": counts[Severity.INFO],
            "warnings": counts[Severity.WARNING],
            "errors": counts[Severity.ERROR],
            "critical": counts[Severity.CRITICAL],
            "recommendations": len(self.recommendations),
            "repairable": repairable,
            "health_score": health,
            "health_label": _health_label(health),
        }
        return self.summary


def _health_label(score: int) -> str:
    """Retorna una etiqueta legible para el health score."""
    if score >= 90:
        return "Excelente"
    elif score >= 75:
        return "Bueno"
    elif score >= 50:
        return "Aceptable"
    elif score >= 25:
        return "Necesita atencion"
    else:
        return "Critico"
