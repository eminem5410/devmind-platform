"""Service: Forecast - Proyeccion de costos API vs Local."""

from __future__ import annotations

from devmind.services.pricing import (
    PRICING_TABLE,
    calculate_api_cost,
    calculate_local_cost,
)

MONTHS = [1, 3, 6, 12]
MAX_CROSSOVER_MONTHS = 60


def run_forecast(
    daily_tokens: int = 100_000,
    output_ratio: float = 0.4,
    cache_ratio: float = 0.5,
    growth_rate: float = 0.0,
    tps: float = 0.0,
    hours_per_day: float = 8.0,
    electricity_cost_per_kwh: float = 0.12,
    gpu_watts: float = 250,
    provider: str | None = None,
    model: str | None = None,
) -> dict:
    # Calcular costos API para cada pricing entry
    input_tokens = int(daily_tokens * (1 - output_ratio))
    output_tokens = int(daily_tokens * output_ratio)

    providers_cost = []
    for pricing in PRICING_TABLE:
        if provider and provider.lower() not in pricing.provider.lower():
            continue
        if model and model.lower() not in pricing.model.lower():
            continue
        cost = calculate_api_cost(pricing, input_tokens, output_tokens, cache_ratio)
        providers_cost.append(cost)

    # Calcular costo local
    local_cost = calculate_local_cost(
        tokens_per_second=tps,
        hours_per_day=hours_per_day,
        electricity_cost_per_kwh=electricity_cost_per_kwh,
        gpu_watts=gpu_watts,
    )

    # Proyecciones por mes
    projections = []
    for month in MONTHS:
        api_monthly = 0.0
        if providers_cost:
            cheapest = min(providers_cost, key=lambda p: p.get("monthly_cost", float("inf")))
            api_monthly = cheapest.get("monthly_cost", 0)

        local_monthly = local_cost.get("monthly_electricity_cost", 0)

        if growth_rate > 0:
            api_total = api_monthly * ((1 + growth_rate / 100) ** month)
            local_total = local_monthly
        else:
            api_total = api_monthly * month
            local_total = local_monthly * month

        projections.append({
            "month": month,
            "tokens": int(daily_tokens * ((1 + growth_rate / 100) ** month)),
            "api_cost": round(api_total, 2),
            "local_cost": round(local_total, 2),
        })

    # Crossover
    crossover = None
    if providers_cost:
        cheapest = min(providers_cost, key=lambda p: p.get("monthly_cost", float("inf")))
        api_base = cheapest.get("monthly_cost", float("inf"))
        local_base = local_cost.get("monthly_electricity_cost", 0)

        for month in range(1, MAX_CROSSOVER_MONTHS + 1):
            if growth_rate > 0:
                api_acc = api_base * ((1 + growth_rate / 100) ** month)
                local_acc = local_base
            else:
                api_acc = api_base * month
                local_acc = local_base * month

            if local_acc <= api_acc:
                crossover = {
                    "month": month,
                    "api_total": round(api_acc, 2),
                    "local_total": round(local_acc, 2),
                    "hardware_cost": round(local_base, 2),
                }
                break

    return {
        "params": {
            "daily_tokens": daily_tokens,
            "output_ratio": output_ratio,
            "growth_rate": growth_rate,
            "tps": tps,
        },
        "projections": projections,
        "crossover": crossover,
    }
