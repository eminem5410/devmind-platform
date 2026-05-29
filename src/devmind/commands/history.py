"""
Comando: devmind history
Muestra historial de comandos ejecutados, evolucion del sistema
y comparaciones entre snapshots.

Uso:
  devmind history             Lista eventos recientes
  devmind history --doctor    Historial de diagnosticos
  devmind history --bench     Historial de benchmarks
  devmind history --last N    Ultimos N eventos (default: 20)
  devmind history --json      Output JSON estructurado
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from devmind.db.manager import get_llm_benchmarks, get_llm_benchmark_stats
from devmind.utils.logging import logger

console = Console()

LOG_FILE = Path.home() / ".devmind" / "logs" / "devmind.log"


def _read_log_entries(limit: int = 50) -> list[dict]:
    """Lee las ultimas N entries del log."""
    if not LOG_FILE.exists():
        return []

    entries: list[dict] = []
    with open(LOG_FILE) as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                entries.append(entry)
            except (json.JSONDecodeError, ValueError):
                continue

    return entries[-limit:]


def _format_ts(ts: str) -> str:
    """Formatea timestamp para display corto."""
    try:
        # "2026-05-28T05:48:09.538462+00:00" -> "05:48:09"
        return ts.split("T")[1][:8]
    except Exception:
        return ts[:8]


def _render_events(entries: list[dict], filter_event: Optional[str] = None) -> None:
    """Renderiza una tabla de eventos del log."""
    if not entries:
        console.print("  [yellow]No hay eventos registrados.[/yellow]")
        console.print("  [dim]Ejecuta 'devmind doctor' o 'devmind benchmark' para generar eventos.[/dim]")
        console.print()
        return

    # Filtrar si es necesario
    if filter_event:
        filtered = [e for e in entries if filter_event in e.get("event", "")]
    else:
        filtered = entries

    if not filtered:
        console.print(f"  [yellow]No hay eventos del tipo '{filter_event}'.[/yellow]")
        console.print()
        return

    # Tabla
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Hora", width=8)
    table.add_column("Evento", style="bold", width=20)
    table.add_column("Detalle", max_width=60)

    for entry in filtered:
        ts = _format_ts(entry.get("timestamp", ""))
        event = entry.get("event", "?")
        data = entry.get("data", {})
        level = entry.get("level", "INFO")

        # Color por nivel
        if level == "ERROR":
            event_style = "red"
        elif level == "WARNING":
            event_style = "yellow"
        else:
            event_style = "cyan"

        # Formatear detalle segun tipo de evento
        detail = ""
        if event == "command_start":
            cmd = data.get("command", "?")
            args = data.get("args", {})
            if args:
                arg_str = " ".join(f"{k}={v}" for k, v in args.items() if v and k != "args")
                detail = f"[bold]{cmd}[/bold] {arg_str}"
            else:
                detail = f"[bold]{cmd}[/bold]"
        elif event == "command_end":
            cmd = data.get("command", "?")
            dur = data.get("duration_s", 0)
            detail = f"{cmd} ({dur}s)"
        elif event == "doctor_run":
            hs = data.get("health_score", "?")
            w = data.get("warnings", 0)
            e = data.get("errors", 0)
            r = data.get("repairable", 0)
            detail = f"Health: {hs}/100 | W:{w} E:{e} Repair:{r}"
        elif event == "benchmark_run":
            model = data.get("model", "?")
            tps = data.get("tokens_per_sec", 0)
            ttft = data.get("ttft_ms", 0)
            ram = data.get("peak_ram_mb", 0)
            detail = f"{model}: {tps:.1f} tok/s | TTFT {ttft:.0f}ms | RAM {ram:.0f}MB"
        elif event == "snapshot_created":
            filepath = data.get("filepath", "?")
            fmt = data.get("format", "?")
            detail = f"{filepath} ({fmt})"
        elif event == "repair_action":
            target = data.get("target", "?")
            action = data.get("action", "?")
            success = data.get("success", False)
            ok = "[green]OK[/green]" if success else "[red]FAIL[/red]"
            detail = f"{target}: {action} {ok}"
        elif event == "model_download":
            model = data.get("model", "?")
            success = data.get("success", False)
            ok = "[green]OK[/green]" if success else "[red]FAIL[/red]"
            detail = f"{model} {ok}"
        else:
            detail = str(data)[:60]

        table.add_row(ts, f"[{event_style}]{event}[/{event_style}]", detail)

    console.print(table)
    console.print()

    # Resumen
    total = len(filtered)
    events_count = {}
    for e in filtered:
        ev = e.get("event", "other")
        events_count[ev] = events_count.get(ev, 0) + 1

    parts_str = ""
    if len(events_count) > 1:
        parts = [f"{v}x {k}" for k, v in sorted(events_count.items(), key=lambda x: -x[1])]
        parts_str = f" ({", ".join(parts)})"
    console.print(f"  [dim]Mostrando {total} eventos{parts_str}[/dim]")
    console.print()
    console.print()


def _render_doctor_history(entries: list[dict]) -> None:
    """Muestra historial de diagnosticos con evolucion del health score."""
    doctor_entries = [e for e in entries if e.get("event") == "doctor_run"]

    if not doctor_entries:
        console.print("  [yellow]No hay diagnosticos en el historial.[/yellow]")
        console.print("  [dim]Ejecuta 'devmind doctor' para generar el primero.[/dim]")
        console.print()
        return

    console.print("[bold]Evolucion del Health Score[/bold]")
    console.print()

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("#", width=3, justify="right")
    table.add_column("Hora", width=8)
    table.add_column("Health", width=10, justify="center")
    table.add_column("Checks", width=7, justify="center")
    table.add_column("Warnings", width=8, justify="center")
    table.add_column("Errors", width=6, justify="center")
    table.add_column("Repairable", width=10, justify="center")

    for i, entry in enumerate(doctor_entries, 1):
        ts = _format_ts(entry.get("timestamp", ""))
        data = entry.get("data", {})
        hs = data.get("health_score", 0)
        total = data.get("total_checks", 0)
        w = data.get("warnings", 0)
        e = data.get("errors", 0)
        r = data.get("repairable", 0)

        # Color del health score
        if hs >= 75:
            hs_style = "green"
        elif hs >= 50:
            hs_style = "yellow"
        else:
            hs_style = "red"

        table.add_row(
            str(i),
            ts,
            f"[{hs_style}]{hs}/100[/{hs_style}]",
            str(total),
            f"[yellow]{w}[/yellow]",
            f"[red]{e}[/red]" if e > 0 else "[green]0[/green]",
            f"[cyan]{r}[/cyan]" if r > 0 else "0",
        )

    console.print(table)
    console.print()

    # Evolucion
    if len(doctor_entries) >= 2:
        first = doctor_entries[0].get("data", {}).get("health_score", 0)
        last = doctor_entries[-1].get("data", {}).get("health_score", 0)
        delta = last - first
        if delta > 0:
            trend = f"[green]+{delta}[/green]"
        elif delta < 0:
            trend = f"[red]{delta}[/red]"
        else:
            trend = "[dim]=0[/dim]"
        console.print(f"  [bold]Tendencia:[/bold] {first} -> {last} ({trend})")
        console.print()


def _render_benchmark_history(entries: list[dict]) -> None:
    """Muestra historial de benchmarks con evolucion de rendimiento."""
    bench_entries = [e for e in entries if e.get("event") == "benchmark_run"]

    if not bench_entries:
        console.print("  [yellow]No hay benchmarks en el historial.[/yellow]")
        console.print("  [dim]Ejecuta 'devmind benchmark ollama' para generar el primero.[/dim]")
        console.print()
        return

    console.print("[bold]Historial de Benchmarks[/bold]")
    console.print()

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("#", width=3, justify="right")
    table.add_column("Hora", width=8)
    table.add_column("Modelo", width=14)
    table.add_column("tok/s", width=8, justify="right")
    table.add_column("TTFT", width=8, justify="right")
    table.add_column("RAM MB", width=8, justify="right")
    table.add_column("Duracion", width=8, justify="right")

    for i, entry in enumerate(bench_entries, 1):
        ts = _format_ts(entry.get("timestamp", ""))
        data = entry.get("data", {})
        model = data.get("model", "?")
        tps = data.get("tokens_per_sec", 0)
        ttft = data.get("ttft_ms", 0)
        ram = data.get("peak_ram_mb", 0)
        dur = data.get("duration_s", 0)

        # Color por throughput
        if tps >= 15:
            tps_style = "green"
        elif tps >= 8:
            tps_style = "green"
        elif tps >= 4:
            tps_style = "yellow"
        else:
            tps_style = "red"

        table.add_row(
            str(i),
            ts,
            model,
            f"[{tps_style}]{tps:.2f}[/{tps_style}]",
            f"{ttft:.0f}ms",
            f"{ram:.0f}",
            f"{dur:.1f}s",
        )

    console.print(table)
    console.print()

    # Promedios
    if bench_entries:
        avg_tps = sum(e.get("data", {}).get("tokens_per_sec", 0) for e in bench_entries) / len(bench_entries)
        avg_ttft = sum(e.get("data", {}).get("ttft_ms", 0) for e in bench_entries) / len(bench_entries)
        avg_ram = sum(e.get("data", {}).get("peak_ram_mb", 0) for e in bench_entries) / len(bench_entries)

        console.print(f"  [bold]Promedios:[/bold] {avg_tps:.2f} tok/s | "
                      f"TTFT {avg_ttft:.0f}ms | RAM {avg_ram:.0f}MB")
        console.print(f"  [dim]Total benchmarks: {len(bench_entries)}[/dim]")
        console.print()


def _render_llm_history(entries: list[dict], limit: int = 50) -> None:
    """Muestra historial de LLM benchmarks desde SQLite."""
    rows = get_llm_benchmarks(limit=limit)
    if not rows:
        console.print("  [yellow]No hay benchmarks LLM en la base de datos.[/yellow]")
        console.print("  [dim]Ejecuta [bold]devmind llm-benchmark run[/bold] para generar datos.[/dim]")
        console.print()
        return
    console.print("[bold]Historial de LLM Benchmarks (SQLite)[/bold]")
    console.print()
    table = Table(show_header=True, header_style="bold cyan", show_lines=True)
    table.add_column("#", width=3, justify="right")
    table.add_column("Fecha", width=16)
    table.add_column("Proveedor", style="bold", min_width=10)
    table.add_column("Modelo", min_width=16)
    table.add_column("tok/s", justify="right", width=7)
    table.add_column("TTFT", justify="right", width=7)
    table.add_column("Calidad", justify="right", width=7)
    table.add_column("Costo", justify="right", width=8)
    for i, r in enumerate(rows, 1):
        tps = r.get("tokens_per_sec", 0)
        if tps >= 15:
            tps_str = "[green]%.1f[/green]" % tps
        elif tps >= 5:
            tps_str = "[yellow]%.1f[/yellow]" % tps
        else:
            tps_str = "[red]%.1f[/red]" % tps
        qs = r.get("quality_score", 0)
        if qs >= 7:
            q_str = "[green]%.1f[/green]" % qs
        elif qs >= 4:
            q_str = "[yellow]%.1f[/yellow]" % qs
        else:
            q_str = "[red]%.1f[/red]" % qs
        cost = r.get("cost_usd", 0)
        cost_str = "$%.4f" % cost if cost > 0 else "Free"
        model = r.get("model", "?")
        if "/" in model:
            model = model.split("/")[-1]
        if len(model) > 20:
            model = model[:17] + "..."
        ts = r.get("timestamp", "")[:16].replace("T", " ")
        table.add_row(
            str(i), ts, r.get("provider", "?"), model,
            tps_str, "%dms" % r.get("ttft_ms", 0),
            q_str, cost_str,
        )
    console.print(table)
    stats = get_llm_benchmark_stats()
    if stats:
        console.print()
        st = stats
        summary_lines = [
            "Total runs: %d" % st.get("total_runs", 0),
            "Avg throughput: %.2f tok/s" % (st.get("avg_tps", 0) or 0),
            "Best throughput: %.2f tok/s" % (st.get("max_tps", 0) or 0),
            "Avg calidad: %.1f/10" % (st.get("avg_quality", 0) or 0),
            "Proveedores: %d | Modelos: %d" % (st.get("providers", 0), st.get("models", 0)),
        ]
        sep = chr(10)
        console.print(Panel(sep.join(summary_lines), title="Estadisticas", border_style="green"))
    console.print()
    console.print("[dim]DB: ~/.devmind/devmind.db[/dim]")
    console.print()

def run_history(
    last: int = typer.Option(
        20, "--last", "-n",
        help="Numero de eventos a mostrar (default: 20)",
    ),
    doctor: bool = typer.Option(
        False, "--doctor", "-d",
        help="Mostrar solo historial de diagnosticos",
    ),
    bench: bool = typer.Option(
        False, "--bench", "-b",
        help="Mostrar solo historial de benchmarks",
    ),
    llm: bool = typer.Option(
        False, "--llm",
        help="Mostrar historial de LLM benchmarks (SQLite)",
    ),
    json_output: bool = typer.Option(
        False, "--json", "-j",
        help="Output como JSON estructurado",
    ),
) -> None:
    """Muestra historial de comandos y metricas."""
    start_time = time.time()
    logger.command_start("history", {"last": last, "doctor": doctor, "bench": bench, "json": json_output})

    console.print()
    console.print(Panel(
        "[bold cyan]DevMind History[/bold cyan] — Historial de actividad",
        border_style="cyan",
    ))
    console.print()

    entries = _read_log_entries(limit=last)

    if not entries:
        console.print("  [yellow]No hay eventos registrados.[/yellow]")
        console.print("  [dim]Los eventos se guardan en ~/.devmind/logs/devmind.log[/dim]")
        console.print("  [dim]Ejecuta 'devmind doctor' o 'devmind benchmark ollama' para empezar.[/dim]")
        console.print()
        logger.command_end("history", time.time() - start_time)
        return

    # Session ID
    session = entries[-1].get("session_id", "?") if entries else "?"
    console.print(f"  [dim]Session: {session} | Log: ~/.devmind/logs/devmind.log[/dim]")
    console.print()

    if json_output:
        # Output JSON
        console.print_json(json.dumps(entries, indent=2, default=str))
    elif doctor:
        _render_doctor_history(entries)
    elif bench:
        _render_benchmark_history(entries)
    elif llm:
        _render_llm_history(entries, last)
    else:
        _render_events(entries)

    logger.command_end("history", time.time() - start_time)
