"""
Comando: devmind benchmark ollama
Mide el rendimiento de modelos Ollama locales.

Metricas:
  - tokens/sec (throughput de generacion)
  - TTFT (Time To First Token) — latencia inicial en ms
  - RAM pico consumida por Ollama durante generacion
  - Duracion total de generacion
  - Tokens generados vs tokens del prompt

Uso:
  devmind benchmark ollama                Benchmark con prompt default
  devmind benchmark ollama -m phi3:mini   Benchmark un modelo especifico
  devmind benchmark ollama -p "prompt"   Benchmark con prompt custom
  devmind benchmark ollama --json         Output JSON estructurado
  devmind benchmark ollama --runs 3      Ejecutar N veces (promediar)
"""

from __future__ import annotations

import json
import os
import time
from typing import Optional

import httpx
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from devmind.models.benchmark import BenchmarkReport, BenchmarkResult
from devmind.utils.logging import logger
from devmind.utils.ollama import check_ollama
from devmind.utils.system import get_system_info

console = Console()

benchmark_app = typer.Typer(
    name="benchmark",
    help="Mide rendimiento de modelos y servicios de IA",
    no_args_is_help=True,
)

OLLAMA_API = "http://localhost:11434"

# Prompts de benchmark
DEFAULT_PROMPTS = [
    "Explain in 3 sentences what machine learning is and how neural networks learn from data.",
    "Write a short paragraph about the benefits of open source software in modern development.",
    "Describe the Linux operating system and why it is popular for AI development.",
]


def _get_ollama_ram() -> float:
    """Obtiene el RAM consumido por el proceso de Ollama (en MB)."""
    try:
        import subprocess
        r = subprocess.run(
            ["sh", "-c", "ps aux | grep '[o]llama' | awk '{sum+=$6} END{print sum}'"],
            capture_output=True, text=True, timeout=5,
        )
        if r.returncode == 0 and r.stdout.strip():
            # ps aux reports RSS in KB
            return round(int(r.stdout.strip()) / 1024, 1)
    except Exception:
        pass
    return 0.0


def _run_single_benchmark(
    model: str,
    prompt: str,
) -> BenchmarkResult:
    """Ejecuta un benchmark individual contra un modelo Ollama.

    Usa la API /api/generate para medir TTFT y throughput con streaming.
    """
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": True,
        "options": {
            "num_predict": 200,  # Limitar generacion para benchmark rapido
        },
    }

    ram_before = _get_ollama_ram()

    try:
        start_time = time.time()
        first_token_time = None
        tokens_generated = 0
        response_text = ""

        with httpx.Client(timeout=120.0) as client:
            with client.stream("POST", f"{OLLAMA_API}/api/generate", json=payload) as response:
                if response.status_code != 200:
                    error_body = ""
                    try:
                        error_body = response.text
                    except Exception:
                        pass
                    return BenchmarkResult(
                        model=model,
                        prompt=prompt[:100],
                        response="",
                        response_tokens=0,
                        prompt_tokens=0,
                        total_tokens=0,
                        tokens_per_sec=0.0,
                        ttft_ms=0.0,
                        total_time_ms=0.0,
                        peak_ram_mb=ram_before,
                        ram_before_mb=ram_before,
                        success=False,
                        error=f"HTTP {response.status_code}: {error_body[:200]}",
                    )

                for line in response.iter_lines():
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                        if "response" in chunk:
                            delta = chunk.get("response", "")
                            response_text += delta
                            tokens_generated += 1  # Approx: 1 token per chunk

                            if first_token_time is None:
                                first_token_time = time.time()

                        if chunk.get("done", False):
                            break
                    except json.JSONDecodeError:
                        continue

        end_time = time.time()
        total_time_ms = (end_time - start_time) * 1000
        ttft_ms = (first_token_time - start_time) * 1000 if first_token_time else total_time_ms

        ram_after = _get_ollama_ram()
        peak_ram = max(ram_before, ram_after)

        # Tokens/sec (solo tokens generados)
        gen_time_s = (end_time - (first_token_time or start_time))
        tokens_per_sec = tokens_generated / gen_time_s if gen_time_s > 0 else 0.0

        # Truncar respuesta para el reporte
        truncated_response = response_text[:500] if response_text else ""

        return BenchmarkResult(
            model=model,
            prompt=prompt[:100],
            response=truncated_response,
            response_tokens=tokens_generated,
            prompt_tokens=len(prompt.split()),  # Aprox
            total_tokens=tokens_generated + len(prompt.split()),
            tokens_per_sec=round(tokens_per_sec, 2),
            ttft_ms=round(ttft_ms, 2),
            total_time_ms=round(total_time_ms, 2),
            peak_ram_mb=peak_ram,
            ram_before_mb=ram_before,
            ram_after_mb=ram_after,
            success=True,
        )

    except httpx.ConnectError:
        return BenchmarkResult(
            model=model,
            prompt=prompt[:100],
            response="",
            response_tokens=0,
            prompt_tokens=0,
            total_tokens=0,
            tokens_per_sec=0.0,
            ttft_ms=0.0,
            total_time_ms=0.0,
            peak_ram_mb=ram_before,
            success=False,
            error="No se pudo conectar a la API de Ollama (ollama serve no esta ejecutando)",
        )
    except Exception as e:
        return BenchmarkResult(
            model=model,
            prompt=prompt[:100],
            response="",
            response_tokens=0,
            prompt_tokens=0,
            total_tokens=0,
            tokens_per_sec=0.0,
            ttft_ms=0.0,
            total_time_ms=0.0,
            peak_ram_mb=ram_before,
            success=False,
            error=str(e)[:200],
        )


def _render_rich(report: BenchmarkReport) -> None:
    """Renderiza los resultados del benchmark en la terminal."""
    console.print()
    console.print(Panel(
        "[bold cyan]DevMind Benchmark[/bold cyan] — Rendimiento de modelos Ollama",
        border_style="cyan",
    ))
    console.print()

    if not report.results:
        console.print("  [yellow]No se ejecutaron benchmarks.[/yellow]")
        console.print()
        return

    # Hardware summary
    if report.hardware_summary:
        console.print(f"  [dim]Hardware: {report.hardware_summary}[/dim]")
        console.print()

    for i, result in enumerate(report.results, 1):
        if not result.success:
            console.print(f"  [red]Run {i} ({result.model}): FALLO[/red]")
            console.print(f"    [dim]Error: {result.error}[/dim]")
            console.print()
            continue

        # Color coding por rendimiento
        tps = result.tokens_per_sec
        if tps >= 15:
            tps_color = "green"
            tps_label = "Excelente"
        elif tps >= 8:
            tps_color = "green"
            tps_label = "Bueno"
        elif tps >= 4:
            tps_color = "yellow"
            tps_label = "Aceptable"
        elif tps >= 1:
            tps_color = "yellow"
            tps_label = "Lento"
        else:
            tps_color = "red"
            tps_label = "Muy lento"

        console.print(f"  [bold]Run {i}[/bold] — [cyan]{result.model}[/cyan]")
        console.print()

        # Tabla de metricas
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Metric", style="bold", width=22)
        table.add_column("Value")

        table.add_row("Throughput",
                       f"[{tps_color}]{tps:.2f} tokens/s[/{tps_color}] ({tps_label})")
        table.add_row("TTFT (Time to First Token)",
                       f"{result.ttft_ms:.0f} ms")
        table.add_row("Total time",
                       f"{result.total_time_ms:.0f} ms")
        table.add_row("Tokens generados",
                       f"{result.response_tokens} tokens")
        table.add_row("RAM pico Ollama",
                       f"{result.peak_ram_mb:.0f} MB")
        if result.ram_before_mb is not None and result.peak_ram_mb > 0:
            ram_delta = result.peak_ram_mb - result.ram_before_mb
            delta_color = "yellow" if ram_delta > 500 else "dim"
            table.add_row("RAM delta",
                           f"[{delta_color}]+{ram_delta:.0f} MB[/{delta_color}]")

        console.print(table)
        console.print()

        # Preview de respuesta (primera linea)
        if result.response:
            first_line = result.response.split("\n")[0][:80]
            console.print(f"  [dim]Respuesta: \"{first_line}...\"[/dim]")
            console.print()

    # ── Summary ───────────────────────────────────────────────────────
    if report.summary:
        s = report.summary
        console.print("[bold]Resumen[/bold]")
        console.print()

        successful = [r for r in report.results if r.success]
        if successful:
            avg_tps = s.get("avg_tokens_per_sec", 0)
            avg_tps_color = "green" if avg_tps >= 8 else "yellow" if avg_tps >= 4 else "red"

            summary_table = Table(show_header=False, box=None, padding=(0, 2))
            summary_table.add_column("Metric", style="bold", width=25)
            summary_table.add_column("Value")
            summary_table.add_row("Benchmarks OK", f"{s['benchmarks_ok']}/{s['benchmarks_total']}")
            summary_table.add_row("Avg throughput",
                                  f"[{avg_tps_color}]{avg_tps:.2f} tokens/s[/{avg_tps_color}]")
            summary_table.add_row("Range",
                                  f"{s['min_tokens_per_sec']:.2f} — {s['max_tokens_per_sec']:.2f} tokens/s")
            summary_table.add_row("Avg TTFT", f"{s['avg_ttft_ms']:.0f} ms")
            summary_table.add_row("Avg RAM pico", f"{s['avg_peak_ram_mb']:.0f} MB")
            summary_table.add_row("Total tokens", str(s['total_tokens_generated']))
            summary_table.add_row("Modelos", ", ".join(s.get('models_tested', [])))
            console.print(summary_table)

        console.print()

    # ── Tips ───────────────────────────────────────────────────────────
    console.print("[dim]Tips para mejorar rendimiento:[/dim]")
    console.print("[dim]  - Cuantizacion: usar modelos Q4 en vez de Q8 o FP16[/dim]")
    console.print("[dim]  - GPU: NVIDIA con CUDA es 10-50x mas rapido que CPU[/dim]")
    console.print("[dim]  - Contexto: prompts cortos = menos RAM y mas rapido[/dim]")
    console.print("[dim]  - num_ctx: reducir si no necesitas contexto largo[/dim]")
    console.print()


def _render_compact(report: BenchmarkReport) -> None:
    """Renderiza benchmark en formato compacto (una linea)."""
    if not report.results:
        console.print("[yellow]No benchmarks ejecutados[/yellow]")
        return

    successful = [r for r in report.results if r.success]
    if not successful:
        r = report.results[0]
        console.print(f"[red]Benchmark FAIL: {r.model} — {r.error}[/red]")
        return

    # Promediar si hay multiples runs
    if len(successful) == 1:
        r = successful[0]
        avg_tps = r.tokens_per_sec
        avg_ttft = r.ttft_ms
        avg_ram = r.peak_ram_mb
    else:
        avg_tps = sum(r.tokens_per_sec for r in successful) / len(successful)
        avg_ttft = sum(r.ttft_ms for r in successful) / len(successful)
        avg_ram = sum(r.peak_ram_mb for r in successful) / len(successful)

    tps_color = "green" if avg_tps >= 8 else "yellow" if avg_tps >= 4 else "red"
    model = successful[0].model

    console.print(
        f"[bold cyan]DevMind Benchmark[/bold cyan] | "
        f"Model: [cyan]{model}[/cyan] | "
        f"Throughput: [{tps_color}]{avg_tps:.2f} tok/s[/{tps_color}] | "
        f"TTFT: {avg_ttft:.0f}ms | "
        f"RAM: {avg_ram:.0f}MB | "
        f"Runs: {len(successful)}/{len(report.results)}"
    )


@benchmark_app.command(name="ollama")
def benchmark_ollama_cmd(
    model: Optional[str] = typer.Option(
        None, "--model", "-m",
        help="Modelo a benchmarkuear (default: primero disponible)",
    ),
    prompt: Optional[str] = typer.Option(
        None, "--prompt", "-p",
        help="Prompt custom para el benchmark",
    ),
    runs: int = typer.Option(
        1, "--runs", "-r",
        help="Numero de ejecuciones para promediar",
    ),
    json_output: bool = typer.Option(
        False, "--json", "-j",
        help="Output como JSON estructurado",
    ),
    compact: bool = typer.Option(
        False, "--compact", "-c",
        help="Output compacto de una linea",
    ),
):
    """Benchmark de modelos Ollama: mide tokens/s, latencia y RAM."""
    start_time = time.time()
    logger.command_start("benchmark", {
        "target": "ollama",
        "model": model,
        "runs": runs,
    })

    console.print()
    console.print(Panel(
        "[bold cyan]DevMind Benchmark[/bold cyan] — Ollama Performance",
        border_style="cyan",
    ))
    console.print()

    # ── Verificar Ollama ───────────────────────────────────────────────
    console.print("  Verificando Ollama...")
    ollama_status = check_ollama()

    if not ollama_status.installed:
        console.print("  [red]Ollama no esta instalado.[/red]")
        console.print("  Ejecuta [bold]devmind repair ollama[/bold] para instalar.")
        console.print()
        logger.command_end("benchmark", time.time() - start_time, success=False)
        return

    if not ollama_status.running:
        console.print("  [red]Ollama instalado pero el servidor no responde.[/red]")
        console.print("  Ejecuta [bold]ollama serve[/bold] o [bold]devmind repair ollama[/bold].")
        console.print()
        logger.command_end("benchmark", time.time() - start_time, success=False)
        return

    console.print(f"  [green]Ollama {ollama_status.version} ejecutando[/green]")

    # Seleccionar modelo
    if model:
        if model not in ollama_status.models:
            console.print(f"  [yellow]Modelo '{model}' no esta descargado.[/yellow]")
            console.print(f"  Modelos disponibles: {', '.join(ollama_status.models) or 'Ninguno'}")
            if not ollama_status.models:
                console.print("  Ejecuta [bold]devmind repair ollama[/bold] para descargar un modelo.")
            console.print()
            logger.command_end("benchmark", time.time() - start_time, success=False)
            return
    else:
        if ollama_status.models:
            model = ollama_status.models[0]
        else:
            console.print("  [yellow]No hay modelos descargados para benchmarkear.[/yellow]")
            console.print("  Ejecuta [bold]devmind repair ollama[/bold] para descargar un modelo.")
            console.print()
            logger.command_end("benchmark", time.time() - start_time, success=False)
            return

    console.print(f"  Modelo seleccionado: [bold cyan]{model}[/bold cyan]")
    console.print()

    # Hardware summary
    sys_info = get_system_info()
    hw_summary = (
        f"{sys_info.cpu_name or '?'} ({sys_info.cpu_cores}c), "
        f"{sys_info.ram_total_gb or '?'} GB RAM"
    )

    # Seleccionar prompts
    prompts = [prompt] if prompt else DEFAULT_PROMPTS[:runs]

    # ── Ejecutar benchmarks ──────────────────────────────────────────
    results: list[BenchmarkResult] = []

    for run_idx in range(runs):
        run_prompt = prompts[run_idx % len(prompts)]
        console.print(
            f"  [bold cyan]>>>[/bold cyan] Run {run_idx + 1}/{runs} — "
            f"Modelo: {model}"
        )
        console.print(f"  [dim]Prompt: \"{run_prompt[:60]}...\"[/dim]")
        console.print()

        result = _run_single_benchmark(model, run_prompt)
        results.append(result)

        if result.success:
            console.print(
                f"  [green]OK[/green] {result.tokens_per_sec:.2f} tokens/s | "
                f"TTFT: {result.ttft_ms:.0f}ms | "
                f"RAM: {result.peak_ram_mb:.0f}MB"
            )
        else:
            console.print(f"  [red]FALLO[/red] {result.error}")
        console.print()

    # ── Construir reporte ─────────────────────────────────────────────
    report = BenchmarkReport(
        hostname=sys_info.cpu_name or "unknown",
        hardware_summary=hw_summary,
        results=results,
    )
    report.compute_summary()

    # Log results
    for r in results:
        if r.success:
            logger.benchmark_run(
                model=r.model,
                tokens_per_sec=r.tokens_per_sec,
                total_tokens=r.total_tokens,
                ttft_ms=r.ttft_ms,
                peak_ram_mb=r.peak_ram_mb,
                prompt=run_prompt,
                duration_s=r.total_time_ms / 1000,
            )

    # ── Renderizar ───────────────────────────────────────────────────
    if json_output:
        console.print_json(json.dumps(
            report.model_dump(mode="json"),
            indent=2,
            default=str,
        ))
    elif compact:
        _render_compact(report)
    else:
        _render_rich(report)

    duration = time.time() - start_time
    logger.command_end("benchmark", duration)
