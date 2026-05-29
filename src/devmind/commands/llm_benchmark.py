"""
Comando: devmind llm-benchmark
Compara rendimiento de modelos LLM (Ollama local vs API providers).
"""

from __future__ import annotations

import json
import time
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from devmind.services.llm_benchmark import (
    run_llm_benchmark,
    get_available_providers,
    API_PROVIDERS,
    BENCHMARK_PROMPTS,
)
from devmind.utils.logging import logger

console = Console()

llm_bench_app = typer.Typer(
    name="llm-benchmark",
    help="Compara rendimiento de modelos LLM (local vs API)",
    no_args_is_help=True,
)


@llm_bench_app.command(name="run")
def llm_benchmark_run(
    providers: Optional[str] = typer.Option(
        None, "--providers", "-P",
        help="Proveedores API separados por coma (groq,together,openrouter,fireworks)",
    ),
    models: Optional[str] = typer.Option(
        None, "--models", "-M",
        help="Modelos API separados por coma (solo para primer proveedor)",
    ),
    ollama_model: Optional[str] = typer.Option(
        None, "--ollama-model", "-m",
        help="Modelo Ollama a benchmarkear (default: primero disponible)",
    ),
    prompt: Optional[str] = typer.Option(
        None, "--prompt", "-p",
        help="Prompt custom para benchmark",
    ),
    runs: int = typer.Option(
        1, "--runs", "-r",
        help="Numero de ejecuciones para promediar",
    ),
    no_local: bool = typer.Option(
        False, "--no-local",
        help="Omitir benchmark local de Ollama",
    ),
    json_output: bool = typer.Option(
        False, "--json", "-j",
        help="Output como JSON estructurado",
    ),
):
    """Benchmark LLM: compara Ollama local vs proveedores API."""
    start_time = time.time()

    console.print()
    console.print(Panel(
        "[bold cyan]DevMind LLM Benchmark[/bold cyan] — Local vs API",
        border_style="cyan",
    ))
    console.print()
    console.print("[bold cyan]v0.10.0[/bold cyan]")
    console.print()

    # Parse providers
    provider_list = None
    if providers:
        provider_list = [p.strip() for p in providers.split(",")]
        console.print("  Proveedores: [bold]" + ", ".join(provider_list) + "[/bold]")
    else:
        console.print("  Proveedores: [dim]auto-detect desde env vars[/dim]")

    # Parse models
    model_list = None
    if models:
        model_list = [m.strip() for m in models.split(",")]
        console.print("  Modelos API: [bold]" + ", ".join(model_list) + "[/bold]")

    if ollama_model:
        console.print("  Ollama model: [bold]" + ollama_model + "[/bold]")
    elif not no_local:
        console.print("  Ollama model: [dim]auto-detect[/dim]")

    console.print("  Runs: [bold]" + str(runs) + "[/bold]")
    console.print()

    # Check available providers
    available = get_available_providers()
    found_any = False
    avail_names = []
    for name, key in available.items():
        if key:
            avail_names.append(name + " [green](key found)[/green]")
            found_any = True
        else:
            avail_names.append(name + " [dim](no key)[/dim]")

    console.print("  API keys detectadas:")
    for name_line in avail_names:
        console.print("    " + name_line)
    console.print()

    if not found_any and no_local:
        console.print("  [red]No hay API keys configuradas y --no-local esta activo.[/red]")
        console.print("  Setea GROQ_API_KEY, TOGETHER_API_KEY, OPENROUTER_API_KEY o FIREWORKS_API_KEY.")
        console.print()
        return

    # Run benchmark
    console.print("  [bold cyan]Ejecutando benchmarks...[/bold cyan]")
    console.print()

    results = run_llm_benchmark(
        providers=provider_list,
        models=model_list,
        prompt=prompt,
        runs=runs,
        include_local=not no_local,
        ollama_model=ollama_model,
    )

    # Render results
    if json_output:
        json_results = []
        for r in results:
            json_results.append({
                "provider": r.provider,
                "model": r.model,
                "tokens_per_sec": r.tokens_per_sec,
                "ttft_ms": r.ttft_ms,
                "total_time_ms": r.total_time_ms,
                "quality_score": r.quality.score,
                "quality_completeness": r.quality.completeness,
                "quality_clarity": r.quality.clarity,
                "quality_structure": r.quality.structure,
                "quality_vocabulary": r.quality.vocabulary,
                "prompt_tokens": r.prompt_tokens,
                "response_tokens": r.response_tokens,
                "cost_usd": r.cost_usd,
                "success": r.success,
                "error": r.error,
            })
        console.print_json(json.dumps(json_results, indent=2))
        duration = time.time() - start_time
        logger.command_end("llm-benchmark", duration)
        return

    # Rich table
    successful = [r for r in results if r.success]
    failed = [r for r in results if not r.success]

    if successful:
        table = Table(title="\nResultados del Benchmark LLM", show_lines=True)
        table.add_column("#", style="dim", width=3, justify="right")
        table.add_column("Proveedor", style="bold", min_width=12)
        table.add_column("Modelo", min_width=20)
        table.add_column("tok/s", justify="right", min_width=8)
        table.add_column("TTFT", justify="right", min_width=7)
        table.add_column("Calidad", justify="right", min_width=7)
        table.add_column("Tokens", justify="right", min_width=7)
        table.add_column("Costo", justify="right", min_width=8)

        for i, r in enumerate(successful, 1):
            tps = r.tokens_per_sec
            if tps >= 15:
                tps_str = "[green]" + str(tps) + "[/green]"
            elif tps >= 5:
                tps_str = "[yellow]" + str(tps) + "[/yellow]"
            else:
                tps_str = "[red]" + str(tps) + "[/red]"

            qs = r.quality.score
            if qs >= 7:
                q_str = "[green]" + str(qs) + "[/green]"
            elif qs >= 4:
                q_str = "[yellow]" + str(qs) + "[/yellow]"
            else:
                q_str = "[red]" + str(qs) + "[/red]"

            model_short = r.model.split("/")[-1] if "/" in r.model else r.model
            if len(model_short) > 28:
                model_short = model_short[:25] + "..."

            cost_str = "$" + str(r.cost_usd) if r.cost_usd > 0 else "Free"
            ttft_str = str(int(r.ttft_ms)) + "ms"
            tokens_str = str(r.prompt_tokens + r.response_tokens)

            table.add_row(
                str(i),
                r.provider,
                model_short,
                tps_str,
                ttft_str,
                q_str,
                tokens_str,
                cost_str,
            )

        console.print(table)

        # Quality details
        if successful:
            console.print()
            detail_table = Table(title="Detalle de Calidad (heuristica 0-10)", show_lines=True)
            detail_table.add_column("Proveedor", style="bold", min_width=12)
            detail_table.add_column("Modelo", min_width=20)
            detail_table.add_column("Total", justify="right", min_width=6)
            detail_table.add_column("Complet.", justify="right", min_width=8)
            detail_table.add_column("Claridad", justify="right", min_width=8)
            detail_table.add_column("Estruct.", justify="right", min_width=8)
            detail_table.add_column("Vocab.", justify="right", min_width=6)

            for r in successful:
                model_short = r.model.split("/")[-1] if "/" in r.model else r.model
                if len(model_short) > 28:
                    model_short = model_short[:25] + "..."
                detail_table.add_row(
                    r.provider,
                    model_short,
                    str(r.quality.score),
                    str(r.quality.completeness),
                    str(r.quality.clarity),
                    str(r.quality.structure),
                    str(r.quality.vocabulary),
                )

            console.print(detail_table)

    if failed:
        console.print()
        console.print("[bold red]Errores:[/bold red]")
        for r in failed:
            console.print("  [red]" + r.provider + ": " + r.error + "[/red]")

    # Summary
    if successful:
        console.print()
        tps_values = [r.tokens_per_sec for r in successful]
        ttft_values = [r.ttft_ms for r in successful]
        quality_values = [r.quality.score for r in successful]

        best_tps = max(successful, key=lambda x: x.tokens_per_sec)
        best_quality = max(successful, key=lambda x: x.quality.score)

        summary_text = Text()
        summary_text.append("\nMejor throughput: ", style="bold")
        summary_text.append(best_tps.provider + " / " + best_tps.model.split("/")[-1], style="cyan")
        summary_text.append(" (" + str(best_tps.tokens_per_sec) + " tok/s)", style="green")
        summary_text.append("\nMejor calidad:    ", style="bold")
        summary_text.append(best_quality.provider + " / " + best_quality.model.split("/")[-1], style="cyan")
        summary_text.append(" (" + str(best_quality.quality.score) + "/10)", style="green")
        summary_text.append("\nAvg throughput:   ", style="bold")
        summary_text.append(str(round(sum(tps_values) / len(tps_values), 2)) + " tok/s")
        summary_text.append("\nAvg TTFT:         ", style="bold")
        summary_text.append(str(int(sum(ttft_values) / len(ttft_values))) + " ms")
        summary_text.append("\nAvg calidad:      ", style="bold")
        summary_text.append(str(round(sum(quality_values) / len(quality_values), 1)) + "/10")

        console.print(Panel(summary_text, title="Resumen", border_style="green"))

    console.print()
    console.print("[dim]Tip: Configura API keys para comparar vs Ollama local:[/dim]")
    console.print("[dim]  export GROQ_API_KEY=gsk_...[/dim]")
    console.print("[dim]  export TOGETHER_API_KEY=...[/dim]")
    console.print("[dim]  export OPENROUTER_API_KEY=...[/dim]")
    console.print("[dim]  export FIREWORKS_API_KEY=...[/dim]")
    console.print()

    duration = time.time() - start_time
    logger.command_end("llm-benchmark", duration)


@llm_bench_app.command(name="providers")
def llm_benchmark_providers():
    """Lista proveedores API soportados y sus modelos."""
    console.print()
    console.print(Panel(
        "[bold cyan]DevMind LLM Benchmark[/bold cyan] — Proveedores API",
        border_style="cyan",
    ))
    console.print()

    available = get_available_providers()

    for name, config in API_PROVIDERS.items():
        key = available.get(name)
        if key:
            status = "[green]Configured[/green] (key: ..." + key[-4:] + ")"
        else:
            env_name = config["env_key"]
            status = "[red]Not configured[/red] — set " + env_name

        console.print("  [bold cyan]" + name.upper() + "[/bold cyan]")
        console.print("  " + status)
        console.print("  Endpoint: " + config["base_url"])

        cost_in = config["cost_per_1k_input"]
        cost_out = config["cost_per_1k_output"]
        if cost_in == 0:
            console.print("  Costo: [green]Free tier[/green]")
        else:
            console.print("  Costo: $" + str(cost_in) + "/1K in, $" + str(cost_out) + "/1K out")

        console.print("  Modelos:")
        for model_name in config["models"]:
            short = model_name.split("/")[-1] if "/" in model_name else model_name
            console.print("    - " + short + "  [dim](" + model_name + ")[/dim]")

        console.print()

    console.print("[dim]Para usar:[/dim]")
    console.print("[dim]  export GROQ_API_KEY=gsk_xxxxxxxx[/dim]")
    console.print("[dim]  devmind llm-benchmark run --providers groq[/dim]")
    console.print()
