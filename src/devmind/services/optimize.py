"""Service: Optimize - Recomendaciones de modelo y proveedor."""

from __future__ import annotations

from devmind.services.pricing import calculate_api_cost, calculate_local_cost

# Datos de proveedores: (nombre, modelo, precision, precio_input, precio_output, tps_max)
PROVIDERS = [
    {"provider": "OpenAI", "model": "GPT-4o", "precision": "FP16", "input_cost": 2.50, "output_cost": 10.0, "tps": 80},
    {"provider": "OpenAI", "model": "GPT-4o-mini", "precision": "FP16", "input_cost": 0.15, "output_cost": 0.60, "tps": 200},
    {"provider": "Anthropic", "model": "Claude 3.5 Sonnet", "precision": "FP8", "input_cost": 3.0, "output_cost": 15.0, "tps": 65},
    {"provider": "Anthropic", "model": "Claude 3 Haiku", "precision": "FP8", "input_cost": 0.25, "output_cost": 1.25, "tps": 150},
    {"provider": "Google", "model": "Gemini 1.5 Pro", "precision": "FP8", "input_cost": 1.25, "output_cost": 5.0, "tps": 70},
    {"provider": "Google", "model": "Gemini 1.5 Flash", "precision": "FP8", "input_cost": 0.075, "output_cost": 0.30, "tps": 200},
    {"provider": "Groq", "model": "Llama 3.1 70B", "precision": "FP4", "input_cost": 0.59, "output_cost": 0.79, "tps": 300},
    {"provider": "Groq", "model": "Mixtral 8x7B", "precision": "FP4", "input_cost": 0.24, "output_cost": 0.24, "tps": 400},
    {"provider": "Together AI", "model": "Llama 3.1 70B", "precision": "FP8", "input_cost": 0.88, "output_cost": 0.88, "tps": 120},
    {"provider": "Together AI", "model": "Qwen 2 72B", "precision": "FP8", "input_cost": 0.50, "output_cost": 0.50, "tps": 100},
    {"provider": "Fireworks AI", "model": "Llama 3.1 70B", "precision": "FP8", "input_cost": 0.80, "output_cost": 0.80, "tps": 150},
    {"provider": "Cerebras", "model": "Llama 3.1 70B", "precision": "FP4", "input_cost": 0.60, "output_cost": 0.60, "tps": 500},
]

# Modelos locales: (nombre, ram_requerida_gb, quantizacion, calidad_relativa)
LOCAL_MODELS = [
    {"model": "phi-3-mini", "ram": 2.5, "quantization": "Q4", "quality": 6.0},
    {"model": "Qwen2.5-3B", "ram": 3.0, "quantization": "Q4", "quality": 6.5},
    {"model": "Llama-3.2-3B", "ram": 3.5, "quantization": "Q4", "quality": 6.5},
    {"model": "Gemma2-9B", "ram": 6.0, "quantization": "Q4", "quality": 7.0},
    {"model": "Mistral-7B", "ram": 5.0, "quantization": "Q4", "quality": 7.0},
    {"model": "Llama-3.1-8B", "ram": 6.0, "quantization": "Q4", "quality": 7.5},
    {"model": "Qwen2.5-7B", "ram": 6.0, "quantization": "Q4", "quality": 7.5},
    {"model": "Llama-3.1-70B", "ram": 40.0, "quantization": "Q4", "quality": 8.5},
    {"model": "Qwen2.5-32B", "ram": 20.0, "quantization": "Q4", "quality": 8.0},
    {"model": "Mistral-Large", "ram": 45.0, "quantization": "Q4", "quality": 8.5},
]


def _compute_recommendations(
    tps: int, budget: float, use_case: str
) -> list[dict]:
    """Filtra proveedores que entren en presupuesto y retorna top 3."""
    # Estimar costos mensuales asumiendo uso razonable
    daily_tokens = 100_000
    monthly_tokens = daily_tokens * 30
    results = []
    for p in PROVIDERS:
        # Asumimos ~70% input, ~30% output
        input_tokens = monthly_tokens * 0.7
        output_tokens = monthly_tokens * 0.3
        cost = (input_tokens / 1_000_000 * p["input_cost"]) + (output_tokens / 1_000_000 * p["output_cost"])
        if cost <= budget:
            results.append({
                "provider": p["provider"],
                "model": p["model"],
                "precision": p["precision"],
                "tps": p["tps"],
                "monthly_cost": round(cost, 2),
                "quality_score": _quality_score(p["model"], use_case),
            })
    # Ordenar por calidad descendente
    results.sort(key=lambda x: x["quality_score"], reverse=True)
    return results[:3]


def _best_model_for_ram(ram_gb: float, has_gpu: bool, use_case: str) -> dict:
    """Encuentra el mejor modelo local que quepa en RAM."""
    available = [m for m in LOCAL_MODELS if m["ram"] <= ram_gb]
    if not available:
        return LOCAL_MODELS[0]  # fallback al mas chico
    # Ordenar por calidad
    available.sort(key=lambda x: x["quality"], reverse=True)
    best = available[0]
    return best


def _model_ram(model: str) -> float:
    """Retorna RAM aproximada requerida para un modelo local."""
    for m in LOCAL_MODELS:
        if m["model"].lower() == model.lower():
            return m["ram"]
    return 8.0  # default


def _quality_score(model: str, use_case: str) -> str:
    """Retorna puntuacion de calidad como string (1-10)."""
    base = 7.0
    name = model.lower()
    if "70b" in name or "large" in name:
        base = 8.5
    elif "32b" in name:
        base = 8.0
    elif "8b" in name or "9b" in name or "7b" in name:
        base = 7.5
    elif "3b" in name or "mini" in name:
        base = 6.5
    # Bonus por caso de uso
    if use_case == "code" and ("qwen" in name or "claude" in name):
        base += 0.3
    elif use_case == "creative" and ("mistral" in name or "llama" in name):
        base += 0.2
    elif use_case == "reasoning" and ("claude" in name or "gpt-4" in name):
        base += 0.3
    return f"{min(base, 10.0):.1f}"


def run_optimize(
    tps: int = 10,
    ram: int = 8,
    gpu: str | None = None,
    budget: float = 50.0,
    use_case: str = "general",
) -> dict:
    """Ejecuta la optimizacion completa: recomienda API + local."""
    # Buscar opciones API dentro del presupuesto
    recs = _compute_recommendations(tps, budget, use_case)

    # Opcion local
    has_gpu = gpu is not None or gpu == ""
    local_model = _best_model_for_ram(float(ram), has_gpu, use_case)
    local_option = {
        "model": local_model["model"],
        "quantization": local_model["quantization"],
        "ram_required": local_model["ram"],
        "estimated_tps": 2.0 if not has_gpu else 8.0,
        "quality_score": _quality_score(local_model["model"], use_case),
    }

    # Mejor opcion global
    best_pick = None
    if recs:
        best_pick = recs[0]
    elif local_option["quality_score"]:
        best_pick = {"provider": "Local", "model": local_option["model"]}

    return {
        "recommendations": recs,
        "local_option": local_option,
        "best_pick": best_pick,
    }
