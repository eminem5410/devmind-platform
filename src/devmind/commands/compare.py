"""CLI command: devmind compare."""

from __future__ import annotations
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from devmind.services import compare as compare_svc

compare_app = typer.Typer(help="Compara costos de inferencia local vs APIs", no_args_is_help=False)
console = Console()


def _get_last_benchmark_tps() -> float:
    try:
        from devmind.db import get_engine
        from sqlalchemy import text
        engine = get_engine()
        with engine.connect() as conn:
            r = conn.execute(text("SELECT tokens_per_second FROM benchmarks ORDER BY created_at DESC LIMIT 1")).fetchone()
            if r and r[0]:
                return float(r[0])
    except Exception:
        pass
    return 0.0


@compare_app.callback(invoke_without_command=True)
def compare_main(
    model: str = typer.Option("local-model", "--model", "-m", help="Nombre del modelo local"),
    vs: Optional[str] = typer.Option(None, "--vs", help="Modelo API a comparar (substring)"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="Filtrar por proveedor"),
    daily_tokens: int = typer.Option(50000, "--daily-tokens", "-t", help="Tokens input/dia"),
    output_ratio: float = typer.Option(0.4, "--output-ratio", help="Ratio output/input"),
    cache_ratio: float = typer.Option(0.5, "--cache-ratio", help="Ratio cache hit (0-1)"),
    tps: Optional[float] = typer.Option(None, "--tps", help="Tokens/s local"),
    all_models: bool = typer.Option(False, "--all", "-a", help="Todos los modelos"),
    export_format: Optional[str] = typer.Option(None, "--export", "-e", help="Exportar (json,csv,html)"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Archivo salida"),
) -> None:
    """Compara costos de inferencia local vs APIs de LLM."""
    daily_input = daily_tokens
    daily_output = int(daily_tokens * output_ratio)
    real_tps = tps
    if real_tps is None:
        real_tps = _get_last_benchmark_tps()
        if real_tps > 0:
            console.print(f"[dim]Auto-detect: {real_tps:.1f} tokens/s del ultimo benchmark[/dim]")
    results = compare_svc.run_compare(
        daily_input_tokens=daily_input, daily_output_tokens=daily_output,
        cache_hit_ratio=cache_ratio, local_tokens_per_second=real_tps,
        local_model_name=model, vs_model=vs, vs_provider=provider, show_all=all_models, console=console)
    if export_format:
        from devmind.services.export import export_data
        payload = {"params": results.get("params", {}), "local": results.get("local"),
                   "api": results.get("api", []), "roi": results.get("roi")}
        path = export_data(payload, export_format, output, prefix="compare")
        if path:
            console.print(f"[green]Exportado: {path}[/green]")
