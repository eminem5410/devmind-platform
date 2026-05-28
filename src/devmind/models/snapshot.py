"""
Modelo Pydantic para snapshot del sistema DevMind.

Un snapshot captura el estado completo del sistema en un momento dado:
- Datos de hardware (CPU, RAM, GPU, disco)
- Software instalado (Docker, Ollama, Python, herramientas)
- Modelos Ollama disponibles
- Contenedores Docker activos
- Configuracion de red basica

Sirve para:
- Compartir estado del sistema (debugging, foros, issues)
- Snapshots comparables (antes/despues de cambios)
- Reproducibilidad de issues
- Audit trail del ambiente
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


class SnapshotHardware(BaseModel):
    """Hardware detectado en el snapshot."""
    cpu_name: Optional[str] = None
    cpu_cores: int = 0
    ram_total_gb: Optional[float] = None
    ram_used_gb: Optional[float] = None
    ram_usage_pct: Optional[float] = None
    disk_total_gb: Optional[float] = None
    disk_free_gb: Optional[float] = None
    disk_usage_pct: Optional[float] = None
    gpu: Optional[list[dict]] = Field(default=None, description="Lista de GPUs detectadas")


class SnapshotSoftware(BaseModel):
    """Software y herramientas detectadas."""
    os_name: str = ""
    os_version: str = ""
    kernel: str = ""
    arch: str = ""
    python_version: str = ""
    git_version: Optional[str] = None
    pip_version: Optional[str] = None
    docker_version: Optional[str] = None
    docker_compose_version: Optional[str] = None
    docker_running: bool = False
    docker_containers_running: int = 0
    docker_images_count: int = 0
    ollama_version: Optional[str] = None
    ollama_running: bool = False
    ollama_models: list[str] = Field(default_factory=list)


class SnapshotNetwork(BaseModel):
    """Configuracion de red basica."""
    hostname: str = ""
    ip_local: Optional[str] = None


class SnapshotReport(BaseModel):
    """Reporte completo de snapshot del sistema.

    Este modelo es serializable a JSON y YAML.
    Incluye metadata del snapshot para trazabilidad.
    """
    version: str = "0.3.0"
    snapshot_type: str = "full"
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
    )
    hostname: str = ""
    hardware: SnapshotHardware = Field(default_factory=SnapshotHardware)
    software: SnapshotSoftware = Field(default_factory=SnapshotSoftware)
    network: SnapshotNetwork = Field(default_factory=SnapshotNetwork)

    class Config:
        json_schema_extra = {
            "example": {
                "version": "0.3.0",
                "snapshot_type": "full",
                "hostname": "dev-workstation",
                "hardware": {
                    "cpu_name": "Intel i5-7400",
                    "cpu_cores": 4,
                    "ram_total_gb": 7.1,
                    "ram_used_gb": 4.2,
                },
                "software": {
                    "os_name": "Linux",
                    "python_version": "3.14.4",
                    "ollama_version": "0.24.0",
                },
            }
        }
