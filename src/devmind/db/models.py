"""
Modelos SQLAlchemy ORM para DevMind.

Tablas:
  - doctor_runs: Historial de diagnosticos del sistema
  - benchmark_runs: Historial de benchmarks de Ollama
  - snapshots: Historial de snapshots del sistema
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Session


# ── Base ────────────────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    """Base declarativa para todos los modelos ORM."""
    pass


# ── DoctorRun ───────────────────────────────────────────────────────────────

class DoctorRunRecord(Base):
    """Registro de un diagnostico ejecutado."""
    __tablename__ = "doctor_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    health_score = Column(Integer, nullable=False)
    total_checks = Column(Integer, nullable=False)
    warnings = Column(Integer, default=0)
    errors = Column(Integer, default=0)
    critical = Column(Integer, default=0)
    repairable = Column(Integer, default=0)
    report_json = Column(Text, nullable=False)  # Reporte completo serializado


# ── BenchmarkRun ────────────────────────────────────────────────────────────

class BenchmarkRunRecord(Base):
    """Registro de un benchmark ejecutado."""
    __tablename__ = "benchmark_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    model = Column(String(100), nullable=False)
    tokens_per_sec = Column(Float, nullable=False)
    ttft_ms = Column(Float, nullable=False)
    total_tokens = Column(Integer, default=0)
    peak_ram_mb = Column(Float, default=0.0)
    total_time_ms = Column(Float, default=0.0)
    success = Column(Integer, default=1)  # SQLite no tiene boolean nativo
    error = Column(Text, nullable=True)


# ── SnapshotRecord ──────────────────────────────────────────────────────────

class SnapshotRecord(Base):
    """Registro de un snapshot del sistema."""
    __tablename__ = "snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    hostname = Column(String(100), default="")
    report_json = Column(Text, nullable=False)  # Snapshot completo serializado
