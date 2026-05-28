"""
Route: GET /api/doctor
Ejecuta un diagnostico completo del sistema y retorna el reporte como JSON.
Tambien guarda el resultado en SQLite para historial.
"""

from __future__ import annotations

import json
import time

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from devmind.commands.doctor import _collect_system_data, _collect_checks
from devmind.models.diagnostic import DiagnosticReport
from devmind.utils.recommendations import generate_recommendations
from devmind.utils.logging import logger
from devmind.db.database import get_db
from devmind.db.models import DoctorRunRecord

router = APIRouter(tags=["doctor"])


@router.get("/api/doctor")
async def api_doctor(db: Session = Depends(get_db)):
    """Ejecuta diagnostico completo y retorna el reporte."""
    start_time = time.time()

    # 1. Recolectar datos
    system = _collect_system_data()
    checks = _collect_checks(system)

    # 2. Construir reporte
    report = DiagnosticReport(system=system, checks=checks)
    report.recommendations = generate_recommendations(report)
    report.compute_summary()

    # 3. Guardar en DB
    record = DoctorRunRecord(
        health_score=report.summary.get("health_score", 0),
        total_checks=report.summary.get("total_checks", 0),
        warnings=report.summary.get("warnings", 0),
        errors=report.summary.get("errors", 0),
        critical=report.summary.get("critical", 0),
        repairable=report.summary.get("repairable", 0),
        report_json=report.model_dump_json(indent=2),
    )
    db.add(record)
    db.commit()

    # 4. Log
    duration = time.time() - start_time
    logger.doctor_run(
        health_score=record.health_score,
        total_checks=record.total_checks,
        warnings=record.warnings,
        errors=record.errors,
        repairable=record.repairable,
    )
    logger.command_end("api_doctor", duration)

    return report.model_dump(mode="json")
