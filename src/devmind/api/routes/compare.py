"""API route: /api/compare — Cost comparison endpoint."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query

router = APIRouter(tags=["compare"])


@router.get("/api/compare")
def api_compare(
    model: str = Query("local-model", description="Nombre del modelo local"),
    vs: Optional[str] = Query(None, description="Modelo API a comparar"),
    provider: Optional[str] = Query(None, description="Filtrar por proveedor"),
    daily_tokens: int = Query(50000, description="Tokens input/dia"),
    output_ratio: float = Query(0.4, description="Ratio output/input"),
    cache_ratio: float = Query(0.5, description="Ratio cache hit"),
    tps: Optional[float] = Query(None, description="Tokens/s local"),
    show_all: bool = Query(False, description="Todos los modelos"),
) -> dict:
    """Compare local inference costs vs API costs."""
    from devmind.services.pricing import get_pricing, calculate_api_cost, calculate_local_cost

    daily_input = daily_tokens
    daily_output = int(daily_tokens * output_ratio)

    # Auto-detect tps from DB if not provided
    real_tps = tps
    if real_tps is None:
        try:
            from devmind.db import get_engine
            from sqlalchemy import text
            engine = get_engine()
            with engine.connect() as conn:
                r = conn.execute(text("SELECT tokens_per_second FROM benchmarks ORDER BY created_at DESC LIMIT 1")).fetchone()
                if r and r[0]:
                    real_tps = float(r[0])
        except Exception:
            pass

    api_models = get_pricing(provider=provider, model=vs)
    if not show_all and not vs:
        api_models = sorted(api_models, key=lambda p: p.input_per_1m + p.output_per_1m)[:10]

    api_results = [calculate_api_cost(p, daily_input, daily_output, cache_ratio) for p in api_models]

    local_result = None
    if real_tps and real_tps > 0:
        local_result = calculate_local_cost(tokens_per_second=real_tps)

    cheapest = min(api_results, key=lambda x: x["monthly_cost"]) if api_results else None
    roi = None
    if local_result and cheapest:
        savings = cheapest["monthly_cost"] - local_result["monthly_electricity_cost"]
        if savings > 0:
            roi = {
                "monthly_savings": round(savings, 2),
                "yearly_savings": round(savings * 12, 2),
                "cheapest_api": cheapest["model_id"],
                "cheapest_api_monthly": cheapest["monthly_cost"],
                "local_monthly": local_result["monthly_electricity_cost"],
            }

    return {
        "local": local_result,
        "api": api_results,
        "roi": roi,
        "params": {
            "daily_input_tokens": daily_input,
            "daily_output_tokens": daily_output,
            "cache_hit_ratio": cache_ratio,
            "tokens_per_second": real_tps,
        },
    }


@router.get("/api/compare/providers")
def api_providers() -> dict:
    """List all available providers and models."""
    from devmind.services.pricing import PRICING_TABLE

    providers = {}
    for p in PRICING_TABLE:
        if p.provider not in providers:
            providers[p.provider] = {"models": [], "count": 0}
        providers[p.provider]["models"].append({
            "model": p.model,
            "id": p.id,
            "input_per_1m": p.input_per_1m,
            "output_per_1m": p.output_per_1m,
            "context_window": p.context_window,
        })
        providers[p.provider]["count"] += 1

    return {"providers": providers, "total_models": len(PRICING_TABLE)}
