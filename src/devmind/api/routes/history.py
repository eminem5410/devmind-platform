"""
Route: GET /api/history, /api/history/benchmarks, /api/history/doctors, /api/history/snapshots
Historial de actividad desde SQLite.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from devmind.db.database import get_db
from devmind.db.models import DoctorRunRecord, BenchmarkRunRecord, SnapshotRecord

router = APIRouter(tags=["history"])


@router.get("/api/history/doctors")
async def api_history_doctors(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Historial de diagnosticos desde SQLite."""
    records = (
        db.query(DoctorRunRecord)
        .order_by(DoctorRunRecord.id.desc())
        .limit(limit)
        .all()
    )
    return {
        "total": len(records),
        "entries": [
            {
                "id": r.id,
                "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                "health_score": r.health_score,
                "total_checks": r.total_checks,
                "warnings": r.warnings,
                "errors": r.errors,
                "critical": r.critical,
                "repairable": r.repairable,
            }
            for r in records
        ],
    }


@router.get("/api/history/benchmarks")
async def api_history_benchmarks(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Historial de benchmarks desde SQLite."""
    records = (
        db.query(BenchmarkRunRecord)
        .order_by(BenchmarkRunRecord.id.desc())
        .limit(limit)
        .all()
    )
    return {
        "total": len(records),
        "entries": [
            {
                "id": r.id,
                "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                "model": r.model,
                "tokens_per_sec": r.tokens_per_sec,
                "ttft_ms": r.ttft_ms,
                "total_tokens": r.total_tokens,
                "peak_ram_mb": r.peak_ram_mb,
                "total_time_ms": r.total_time_ms,
                "success": bool(r.success),
                "error": r.error,
            }
            for r in records
        ],
    }


@router.get("/api/history/snapshots")
async def api_history_snapshots(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Historial de snapshots desde SQLite."""
    records = (
        db.query(SnapshotRecord)
        .order_by(SnapshotRecord.id.desc())
        .limit(limit)
        .all()
    )
    return {
        "total": len(records),
        "entries": [
            {
                "id": r.id,
                "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                "hostname": r.hostname,
            }
            for r in records
        ],
    }


@router.get("/api/history")
async def api_history(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Historial completo: doctors + benchmarks + snapshots."""
    doctors = (
        db.query(DoctorRunRecord)
        .order_by(DoctorRunRecord.id.desc())
        .limit(limit)
        .all()
    )
    benchmarks = (
        db.query(BenchmarkRunRecord)
        .order_by(BenchmarkRunRecord.id.desc())
        .limit(limit)
        .all()
    )
    snapshots = (
        db.query(SnapshotRecord)
        .order_by(SnapshotRecord.id.desc())
        .limit(limit)
        .all()
    )

    return {
        "doctors": {
            "total": len(doctors),
            "entries": [
                {
                    "id": r.id,
                    "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                    "health_score": r.health_score,
                    "total_checks": r.total_checks,
                    "warnings": r.warnings,
                    "errors": r.errors,
                }
                for r in doctors
            ],
        },
        "benchmarks": {
            "total": len(benchmarks),
            "entries": [
                {
                    "id": r.id,
                    "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                    "model": r.model,
                    "tokens_per_sec": r.tokens_per_sec,
                    "success": bool(r.success),
                }
                for r in benchmarks
            ],
        },
        "snapshots": {
            "total": len(snapshots),
            "entries": [
                {
                    "id": r.id,
                    "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                    "hostname": r.hostname,
                }
                for r in snapshots
            ],
        },
    }
