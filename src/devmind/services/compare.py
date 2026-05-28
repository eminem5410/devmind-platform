"""Compare local model costs vs API costs."""

from __future__ import annotations
from typing import Optional
from rich.console import Console
from rich.table import Table
from .pricing import calculate_api_cost, calculate_local_cost, get_pricing


def run_compare(daily_input_tokens=50000, daily_output_tokens=20000, cache_hit_ratio=0.5,
                local_tokens_per_second=0.0, local_model_name="local-model",
                vs_model=None, vs_provider=None, show_all=False, console=None) -> dict:
    if console is None:
        console = Console()
    api_models = get_pricing(provider=vs_provider, model=vs_model)
    if not api_models:
        console.print("[yellow]No se encontraron modelos con esos filtros.[/yellow]")
        return {"local": None, "api": [], "roi": None}
    if not show_all and not vs_model:
        api_models = sorted(api_models, key=lambda p: p.input_per_1m + p.output_per_1m)[:10]
    api_results = [calculate_api_cost(p, daily_input_tokens, daily_output_tokens, cache_hit_ratio) for p in api_models]
    local_result = calculate_local_cost(tokens_per_second=local_tokens_per_second) if local_tokens_per_second > 0 else None
    _print_table(console, local_result, api_results, local_model_name)
    cheapest = min(api_results, key=lambda x: x["monthly_cost"]) if api_results else None
    roi = None
    if local_result and cheapest:
        savings = cheapest["monthly_cost"] - local_result["monthly_electricity_cost"]
        if savings > 0:
            roi = {"monthly_savings": round(savings, 2), "yearly_savings": round(savings * 12, 2),
                   "cheapest_api": cheapest["model_id"], "cheapest_api_monthly": cheapest["monthly_cost"],
                   "local_monthly": local_result["monthly_electricity_cost"]}
            console.print(f"\n[bold green]ROI - Inferencia Local[/bold green]")
            console.print(f"  API mas barata:  [cyan]{roi['cheapest_api']}[/cyan] (${roi['cheapest_api_monthly']:.2f}/mes)")
            console.print(f"  Costo local:     [cyan]{local_model_name}[/cyan] (${roi['local_monthly']:.2f}/mes)")
            console.print(f"  Ahorro mensual:  [green]${roi['monthly_savings']:.2f}[/green]")
            console.print(f"  Ahorro anual:    [green]${roi['yearly_savings']:.2f}[/green]")
    return {"local": local_result, "api": api_results, "roi": roi,
            "params": {"daily_input_tokens": daily_input_tokens, "daily_output_tokens": daily_output_tokens, "cache_hit_ratio": cache_hit_ratio}}


def _print_table(console, local, api_results, local_model_name):
    table = Table(title="Comparacion de Costos: Local vs API", show_lines=True)
    table.add_column("Modelo", style="bold", max_width=35)
    table.add_column("Proveedor", max_width=15)
    table.add_column("Input/1M", justify="right")
    table.add_column("Output/1M", justify="right")
    table.add_column("Costo Diario", justify="right", style="bold")
    table.add_column("Costo Mensual", justify="right", style="bold")
    table.add_column("Costo Anual", justify="right")
    if local:
        table.add_row(f"[green]{local_model_name}[/green]", "Local", "$0.00", "$0.00",
                      f"${local['daily_electricity_cost']:.4f}", f"${local['monthly_electricity_cost']:.2f}", f"${local['yearly_electricity_cost']:.2f}")
    for c in sorted(api_results, key=lambda x: x["monthly_cost"]):
        table.add_row(c["model"], c["provider"], f"${c['cost_per_1k_input']:.4f}", f"${c['cost_per_1k_output']:.4f}",
                      f"${c['daily_cost']:.4f}", f"${c['monthly_cost']:.2f}", f"${c['yearly_cost']:.2f}")
    console.print()
    console.print(table)
