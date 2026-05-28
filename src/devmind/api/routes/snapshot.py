"""
Route: GET /api/snapshot
Ejecuta un snapshot del sistema y retorna el reporte como JSON.
Tambien guarda el resultado en SQLite para historial.
"""

from __future__ import annotations

import json
import time

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from devmind.commands.snapshot import _collect_snapshot
from devmind.utils.logging import logger
from devmind.db.database import get_db
from devmind.db.models import SnapshotRecord

router = APIRouter(tags=["snapshot"])


@router.get("/api/snapshot")
async def api_snapshot(db: Session = Depends(get_db)):
    """Ejecuta snapshot del sistema y retorna el reporte."""
    start_time = time.time()

    # 1. Recolectar datos
    report = _collect_snapshot()

    # 2. Guardar en DB
    record = SnapshotRecord(
        hostname=report.hostname,
        report_json=report.model_dump_json(indent=2),
    )
    db.add(record)
    db.commit()

    # 3. Log
    duration = time.time() - start_time
    logger.snapshot_created(
        filepath="api://snapshot",
        format="api",
        size_bytes=len(record.report_json),
    )
    logger.command_end("api_snapshot", duration)

    return report.model_dump(mode="json")
