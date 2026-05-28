"""
Route: POST /api/benchmark/ollama
Ejecuta un benchmark de un modelo Ollama y retorna el resultado.
Guarda cada resultado en SQLite para historial.
"""

from __future__ import annotations

import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from devmind.commands.benchmark import (
    _run_single_benchmark,
    _get_ollama_ram,
    DEFAULT_PROMPTS,
)
from devmind.models.benchmark import BenchmarkReport
from devmind.utils.logging import logger
from devmind.utils.ollama import check_ollama
from devmind.utils.system import get_system_info
from devmind.db.database import get_db
from devmind.db.models import BenchmarkRunRecord

router = APIRouter(tags=["benchmark"])


class BenchmarkRequest(BaseModel):
    """Request body para benchmark."""
    model: Optional[str] = None
    prompt: Optional[str] = None
    runs: int = 1


@router.post("/api/benchmark/ollama")
async def api_benchmark_ollama(
    req: BenchmarkRequest,
    db: Session = Depends(get_db),
):
    """Ejecuta benchmark de Ollama y retorna resultados."""
    start_time = time.time()

    # 1. Verificar Ollama
    ollama_status = check_ollama()
    if not ollama_status.installed:
        raise HTTPException(status_code=503, detail="Ollama no esta instalado")
    if not ollama_status.running:
        raise HTTPException(status_code=503, detail="Ollama no esta ejecutando")

    # 2. Seleccionar modelo
    model = req.model
    if model and model not in ollama_status.models:
        raise HTTPException(
            status_code=404,
            detail=f"Modelo '{model}' no encontrado. Disponibles: {', '.join(ollama_status.models) or 'Ninguno'}",
        )
    if not model:
        if ollama_status.models:
            model = ollama_status.models[0]
        else:
            raise HTTPException(status_code=404, detail="No hay modelos descargados")

    # 3. Seleccionar prompts
    prompts = [req.prompt] if req.prompt else DEFAULT_PROMPTS[:req.runs]

    # 4. Ejecutar benchmarks
    from devmind.commands.benchmark import BenchmarkResult
    results = []

    for run_idx in range(req.runs):
        run_prompt = prompts[run_idx % len(prompts)]
        result = _run_single_benchmark(model, run_prompt)
        results.append(result)

        # Guardar en DB
        record = BenchmarkRunRecord(
            model=result.model,
            tokens_per_sec=result.tokens_per_sec,
            ttft_ms=result.ttft_ms,
            total_tokens=result.total_tokens,
            peak_ram_mb=result.peak_ram_mb,
            total_time_ms=result.total_time_ms,
            success=1 if result.success else 0,
            error=result.error,
        )
        db.add(record)
        db.commit()

        # Log
        if result.success:
            logger.benchmark_run(
                model=result.model,
                tokens_per_sec=result.tokens_per_sec,
                total_tokens=result.total_tokens,
                ttft_ms=result.ttft_ms,
                peak_ram_mb=result.peak_ram_mb,
                prompt=run_prompt,
                duration_s=result.total_time_ms / 1000,
            )

    # 5. Construir reporte
    sys_info = get_system_info()
    hw_summary = (
        f"{sys_info.cpu_name or '?'} ({sys_info.cpu_cores}c), "
        f"{sys_info.ram_total_gb or '?'} GB RAM"
    )

    report = BenchmarkReport(
        hostname=sys_info.cpu_name or "unknown",
        hardware_summary=hw_summary,
        results=results,
    )
    report.compute_summary()

    duration = time.time() - start_time
    logger.command_end("api_benchmark", duration)

    return report.model_dump(mode="json")
