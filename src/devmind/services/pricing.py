"""Pricing data for LLM API providers."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ModelPricing:
    provider: str
    model: str
    input_per_1m: float
    output_per_1m: float
    cache_read_per_1m: float
    context_window: int
    category: str = "chat"

    @property
    def id(self) -> str:
        return f"{self.provider}/{self.model}"


PRICING_TABLE: list[ModelPricing] = [
    ModelPricing("openai", "gpt-4o", 2.50, 10.00, 1.25, 128000, "chat"),
    ModelPricing("openai", "gpt-4o-mini", 0.15, 0.60, 0.075, 128000, "chat"),
    ModelPricing("openai", "gpt-4.1", 2.00, 8.00, 1.00, 1047576, "chat"),
    ModelPricing("openai", "gpt-4.1-mini", 0.40, 1.60, 0.20, 1047576, "chat"),
    ModelPricing("openai", "gpt-4.1-nano", 0.10, 0.40, 0.05, 1047576, "chat"),
    ModelPricing("openai", "o3-mini", 1.10, 4.40, 0.55, 200000, "chat"),
    ModelPricing("openai", "o4-mini", 1.10, 4.40, 0.55, 200000, "chat"),
    ModelPricing("anthropic", "claude-sonnet-4", 3.00, 15.00, 0.30, 200000, "chat"),
    ModelPricing("anthropic", "claude-haiku-3.5", 0.80, 4.00, 0.08, 200000, "chat"),
    ModelPricing("anthropic", "claude-opus-4", 15.00, 75.00, 1.50, 200000, "chat"),
    ModelPricing("google", "gemini-2.5-flash", 0.15, 0.60, 0.0375, 1048576, "chat"),
    ModelPricing("google", "gemini-2.5-pro", 1.25, 10.00, 0.625, 1048576, "chat"),
    ModelPricing("google", "gemini-2.0-flash", 0.10, 0.40, 0.025, 1048576, "chat"),
    ModelPricing("deepseek", "deepseek-v3", 0.27, 1.10, 0.07, 65536, "chat"),
    ModelPricing("deepseek", "deepseek-r1", 0.55, 2.19, 0.14, 65536, "chat"),
    ModelPricing("groq", "llama-3.3-70b", 0.59, 0.79, 0.08, 131072, "chat"),
    ModelPricing("groq", "llama-3.1-8b", 0.05, 0.08, 0.003, 131072, "chat"),
    ModelPricing("groq", "mixtral-8x7b", 0.24, 0.24, 0.024, 32768, "chat"),
    ModelPricing("mistral", "mistral-large", 2.00, 6.00, 0.20, 131072, "chat"),
    ModelPricing("mistral", "mistral-small", 0.10, 0.30, 0.01, 131072, "chat"),
    ModelPricing("mistral", "codestral", 0.30, 0.90, 0.03, 32768, "code"),
    ModelPricing("cerebras", "llama-3.3-70b", 0.85, 1.20, 0.00, 131072, "chat"),
    ModelPricing("cerebras", "llama-3.1-8b", 0.10, 0.10, 0.00, 131072, "chat"),
    ModelPricing("together", "llama-3.3-70b", 0.88, 0.88, 0.22, 131072, "chat"),
    ModelPricing("together", "qwen-2.5-72b", 1.08, 1.08, 0.27, 32768, "chat"),
    ModelPricing("together", "deepseek-r1", 1.28, 5.32, 0.32, 65536, "chat"),
    ModelPricing("openrouter", "anthropic/claude-sonnet-4", 3.00, 15.00, 1.50, 200000, "chat"),
    ModelPricing("openrouter", "openai/gpt-4o", 2.50, 10.00, 1.25, 128000, "chat"),
    ModelPricing("openrouter", "meta-llama/llama-3.3-70b", 0.39, 0.39, 0.10, 131072, "chat"),
    ModelPricing("xai", "grok-3", 3.00, 15.00, 0.75, 131072, "chat"),
    ModelPricing("xai", "grok-3-mini", 0.30, 0.50, 0.075, 131072, "chat"),
]


def get_pricing(provider: Optional[str] = None, model: Optional[str] = None) -> list[ModelPricing]:
    results = PRICING_TABLE
    if provider:
        results = [p for p in results if provider.lower() in p.provider.lower()]
    if model:
        results = [p for p in results if model.lower() in p.model.lower()]
    return results


def calculate_api_cost(pricing, daily_input_tokens: int, daily_output_tokens: int, cache_hit_ratio: float = 0.5) -> dict:
    cache_tokens = int(daily_input_tokens * cache_hit_ratio)
    non_cache_tokens = daily_input_tokens - cache_tokens
    daily_input_cost = (non_cache_tokens * pricing.input_per_1m / 1_000_000) + (cache_tokens * pricing.cache_read_per_1m / 1_000_000)
    daily_output_cost = daily_output_tokens * pricing.output_per_1m / 1_000_000
    daily_total = daily_input_cost + daily_output_cost
    return {
        "model_id": pricing.id, "provider": pricing.provider, "model": pricing.model,
        "daily_input_tokens": daily_input_tokens, "daily_output_tokens": daily_output_tokens,
        "cache_hit_ratio": cache_hit_ratio, "daily_cost": round(daily_total, 4),
        "monthly_cost": round(daily_total * 30, 2), "yearly_cost": round(daily_total * 365, 2),
        "cost_per_1k_input": round((non_cache_tokens * pricing.input_per_1m / 1_000_000 + cache_tokens * pricing.cache_read_per_1m / 1_000_000) / max(daily_input_tokens, 1) * 1000, 6),
        "cost_per_1k_output": round(daily_output_cost / max(daily_output_tokens, 1) * 1000, 6),
    }


def calculate_local_cost(tokens_per_second: float, hours_per_day: float = 8.0, electricity_cost_per_kwh: float = 0.12, gpu_watts: float = 250) -> dict:
    daily_tokens = int(tokens_per_second * hours_per_day * 3600)
    daily_energy_kwh = (gpu_watts / 1000) * hours_per_day
    daily_electricity = daily_energy_kwh * electricity_cost_per_kwh
    return {
        "tokens_per_second": tokens_per_second, "hours_per_day": hours_per_day,
        "daily_tokens": daily_tokens, "daily_electricity_cost": round(daily_electricity, 4),
        "monthly_electricity_cost": round(daily_electricity * 30, 2),
        "yearly_electricity_cost": round(daily_electricity * 365, 2), "gpu_watts": gpu_watts,
    }
