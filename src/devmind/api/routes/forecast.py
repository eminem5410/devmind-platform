"""API routes: forecast and optimize."""

from __future__ import annotations
from fastapi import APIRouter, Query
from typing import Optional
from devmind.services.forecast import run_forecast
from devmind.services.optimize import _compute_recommendations

router = APIRouter()


@router.get("/api/forecast")
def forecast_endpoint(
    daily_tokens: int = Query(100_000, description="Tokens input/dia"),
    output_ratio: float = Query(0.4),
    cache_ratio: float = Query(0.5),
    growth_rate: float = Query(0.0, description="Crecimiento mensual %%"),
    tps: float = Query(0.0),
    hours: float = Query(8.0),
    electricity: float = Query(0.12),
    gpu_watts: float = Query(250),
    provider: Optional[str] = Query(None),
    model: Optional[str] = Query(None),
):
    return run_forecast(
        daily_tokens=daily_tokens, output_ratio=output_ratio, cache_ratio=cache_ratio,
        growth_rate=growth_rate, tps=tps, hours_per_day=hours,
        electricity_cost_per_kwh=electricity, gpu_watts=gpu_watts,
        provider=provider, model=model)


@router.get("/api/optimize")
def optimize_endpoint(
    tps: float = Query(0.0),
    daily_tokens: int = Query(100_000),
    ram_gb: float = Query(8.0),
    has_gpu: bool = Query(False),
    budget_monthly: float = Query(10.0),
    use_case: str = Query("general"),
):
    return _compute_recommendations(tps, daily_tokens, ram_gb, has_gpu, budget_monthly, use_case)
