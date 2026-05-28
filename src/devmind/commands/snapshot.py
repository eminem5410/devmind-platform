"""
Comando: devmind snapshot
Exporta el estado completo del sistema a JSON o YAML.

Uso:
  devmind snapshot                    Muestra snapshot en terminal
  devmind snapshot --json            Output JSON
  devmind snapshot -o state.json     Guardar a archivo JSON
  devmind snapshot -o state.yaml     Guardar a archivo YAML
  devmind snapshot --compact         Output compacto (una pantalla)

Los snapshots son utiles para:
- Compartir estado del sistema en issues/foros
- Comparar antes/despues de cambios
- Debugging remoto
- Reproducibilidad
"""

from __future__ import annotations

import json
import platform
import shutil
import socket
import time
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from devmind.models.snapshot import (
    SnapshotHardware,
    SnapshotNetwork,
    SnapshotReport,
    SnapshotSoftware,
)
from devmind.utils.docker import check_docker
from devmind.utils.gpu import detect_all_gpus
from devmind.utils.logging import logger
from devmind.utils.ollama import check_ollama
from devmind.utils.system import get_system_info

console = Console()


def _collect_snapshot() -> SnapshotReport:
    """Recolecta todos los datos del sistema para el snapshot."""
    sys_info = get_system_info()
    docker = check_docker()
    ollama = check_ollama()
    gpus = detect_all_gpus()

    # RAM usage %
    ram_pct = None
    if sys_info.ram_total_gb and sys_info.ram_total_gb > 0:
        ram_pct = round((sys_info.ram_used_gb or 0) / sys_info.ram_total_gb * 100, 1)

    # Disk usage %
    try:
        import shutil as _shutil
        stat = _shutil.disk_usage("/home")
        disk_total = round(stat.total / (1024 ** 3), 1)
        disk_free = round(stat.free / (1024 ** 3), 1)
        disk_pct = round(stat.used / stat.total * 100, 1)
    except Exception:
        disk_total = disk_pct = None

    # GPU data as dicts
    gpu_list = None
    if gpus:
        gpu_list = []
        for g in gpus:
            gpu_list.append({
                "vendor": g.vendor,
                "name": g.name,
                "driver_version": g.driver_version,
                "cuda_version": g.cuda_version,
                "vram_total_mb": g.vram_total_mb,
                "vram_used_mb": g.vram_used_mb,
                "temperature_c": g.temperature_c,
                "utilization_pct": g.utilization_pct,
            })

    # IP local
    try:
        local_ip = socket.gethostbyname(socket.gethostname())
    except Exception:
        local_ip = None

    # Git version
    git_ver = None
    code, out = _run_cmd(["git", "--version"])
    if code == 0:
        git_ver = out.replace("git version ", "")

    # pip version
    pip_ver = None
    for cmd_name in ["pip3", "pip"]:
        if shutil.which(cmd_name):
            code, out = _run_cmd([cmd_name, "--version"])
            if code == 0:
                pip_ver = out.split(" ")[1]
                break

    report = SnapshotReport(
        hostname=platform.node(),
        hardware=SnapshotHardware(
            cpu_name=sys_info.cpu_name,
            cpu_cores=sys_info.cpu_cores,
            ram_total_gb=sys_info.ram_total_gb,
            ram_used_gb=sys_info.ram_used_gb,
            ram_usage_pct=ram_pct,
            disk_total_gb=disk_total,
            disk_free_gb=disk_free,
            disk_usage_pct=disk_pct,
            gpu=gpu_list,
        ),
        software=SnapshotSoftware(
            os_name=sys_info.os_name,
            os_version=sys_info.os_version,
            kernel=sys_info.kernel,
            arch=sys_info.arch,
            python_version=sys_info.python_version,
            git_version=git_ver,
            pip_version=pip_ver,
            docker_version=docker.version if docker.installed else None,
            docker_compose_version=docker.compose_version,
            docker_running=docker.running,
            docker_containers_running=docker.containers_running,
            docker_images_count=docker.images_count,
            ollama_version=ollama.version if ollama.installed else None,
            ollama_running=ollama.running,
            ollama_models=ollama.models,
        ),
        network=SnapshotNetwork(
            hostname=platform.node(),
            ip_local=local_ip,
        ),
    )

    return report


def _run_cmd(cmd: list[str], timeout: int = 10) -> tuple[int, str]:
    """Ejecuta un comando y retorna (returncode, stdout)."""
    import subprocess
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return -1, ""


def _try_yaml_dump(data: dict) -> str:
    """Intenta serializar a YAML. Si no hay PyYAML, retorna None."""
    try:
        import yaml
        return yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False)
    except ImportError:
        return None


def _render_rich(report: SnapshotReport) -> None:
    """Renderiza el snapshot en la terminal con Rich."""
    console.print()
    console.print(Panel(
        "[bold cyan]DevMind Snapshot[/bold cyan] — Estado completo del sistema",
        border_style="cyan",
    ))
    console.print()

    # ── Metadata ──────────────────────────────────────────────────────
    console.print(f"  [bold]Timestamp:[/bold] {report.timestamp}")
    console.print(f"  [bold]Hostname:[/bold] {report.hostname}")
    console.print(f"  [bold]Version:[/bold] DevMind {report.version}")
    console.print()

    # ── Hardware ───────────────────────────────────────────────────────
    h = report.hardware
    console.print("[bold blue]Hardware[/bold blue]")
    hw_table = Table(show_header=False, box=None, padding=(0, 1))
    hw_table.add_column("Key", style="bold", width=20)
    hw_table.add_column("Value")

    hw_table.add_row("CPU", f"{h.cpu_name or 'N/A'} ({h.cpu_cores} cores)")
    hw_table.add_row("RAM", f"{h.ram_used_gb or '?'} / {h.ram_total_gb or '?'} GB"
                     f" ({h.ram_usage_pct or '?'}%)")
    if h.disk_free_gb:
        hw_table.add_row("Disco", f"{h.disk_free_gb} GB libres / {h.disk_total_gb} GB"
                         f" ({h.disk_usage_pct}%)")
    if h.gpu:
        for i, g in enumerate(h.gpu):
            label = f"GPU {i+1}" if len(h.gpu) > 1 else "GPU"
            vram = (f"{g['vram_used_mb']}MB / {g['vram_total_mb']}MB"
                    if g.get('vram_total_mb') else "N/A")
            hw_table.add_row(label, f"{g['vendor']} {g['name']} ({vram})")
    else:
        hw_table.add_row("GPU", "[dim]No detectada (CPU-only)[/dim]")
    console.print(hw_table)
    console.print()

    # ── Software ─────────────────────────────────────────────────────────
    s = report.software
    console.print("[bold magenta]Software[/bold magenta]")
    sw_table = Table(show_header=False, box=None, padding=(0, 1))
    sw_table.add_column("Key", style="bold", width=22)
    sw_table.add_column("Value")

    sw_table.add_row("OS", f"{s.os_name} {s.kernel} ({s.arch})")
    sw_table.add_row("Python", s.python_version or "N/A")
    sw_table.add_row("Git", s.git_version or "[dim]no instalado[/dim]")
    sw_table.add_row("pip", s.pip_version or "[dim]no instalado[/dim]")

    docker_status = f"{s.docker_version}" if s.docker_version else "[dim]no instalado[/dim]"
    if s.docker_running and s.docker_version:
        docker_status += f" [green](running)[/green]"
    elif s.docker_version:
        docker_status += " [yellow](daemon stopped)[/yellow]"
    sw_table.add_row("Docker", docker_status)
    sw_table.add_row("Docker Compose", s.docker_compose_version or "[dim]no disponible[/dim]")
    if s.docker_version:
        sw_table.add_row("Contenedores", f"{s.docker_containers_running} activos, {s.docker_images_count} imagenes")

    ollama_status = f"{s.ollama_version}" if s.ollama_version else "[dim]no instalado[/dim]"
    if s.ollama_running and s.ollama_version:
        ollama_status += " [green](running)[/green]"
    elif s.ollama_version:
        ollama_status += " [yellow](server stopped)[/yellow]"
    sw_table.add_row("Ollama", ollama_status)
    if s.ollama_models:
        sw_table.add_row("Modelos", ", ".join(s.ollama_models))
    elif s.ollama_running:
        sw_table.add_row("Modelos", "[dim]ninguno instalado[/dim]")

    console.print(sw_table)
    console.print()

    # ── Network ────────────────────────────────────────────────────────
    n = report.network
    console.print("[bold green]Red[/bold green]")
    net_table = Table(show_header=False, box=None, padding=(0, 1))
    net_table.add_column("Key", style="bold", width=15)
    net_table.add_column("Value")
    net_table.add_row("Hostname", n.hostname)
    net_table.add_row("IP Local", n.ip_local or "[dim]N/A[/dim]")
    console.print(net_table)
    console.print()

    console.print("[dim]Usa --json para output estructurado o -o archivo.json para guardar.[/dim]")
    console.print()


def _render_compact(report: SnapshotReport) -> None:
    """Renderiza snapshot compacto de una pantalla."""
    h = report.hardware
    s = report.software

    console.print(f"[bold cyan]DevMind Snapshot[/bold cyan] | {report.timestamp}")
    console.print(
        f"CPU: {h.cpu_name or '?'} ({h.cpu_cores}c) | "
        f"RAM: {h.ram_used_gb or '?'}/{h.ram_total_gb or '?'} GB | "
        f"Disk: {h.disk_free_gb or '?'} GB free"
    )
    gpu_str = ", ".join(f"{g['vendor']} {g['name']}" for g in (h.gpu or []))
    if not gpu_str:
        gpu_str = "[dim]CPU-only[/dim]"
    console.print(f"GPU: {gpu_str}")
    console.print(
        f"OS: {s.os_name} {s.kernel} | Python: {s.python_version} | "
        f"Git: {s.git_version or '[dim]no[/dim]'}"
    )
    docker_str = f"{s.docker_version}" if s.docker_version else "[dim]no[/dim]"
    ollama_str = f"{s.ollama_version}" if s.ollama_version else "[dim]no[/dim]"
    models_str = ", ".join(s.ollama_models) if s.ollama_models else "[dim]none[/dim]"
    console.print(f"Docker: {docker_str} | Ollama: {ollama_str} | Models: {models_str}")


def _save_to_file(report: SnapshotReport, filepath: str) -> None:
    """Guarda el snapshot a un archivo JSON o YAML."""
    data = report.model_dump(mode="json")

    path = Path(filepath)
    fmt = path.suffix.lower().lstrip(".")

    if fmt == "yaml" or fmt == "yml":
        yaml_str = _try_yaml_dump(data)
        if yaml_str is None:
            console.print()
            console.print("[yellow]PyYAML no esta instalado — guardando como JSON.[/yellow]")
            fmt = "json"
            path = path.with_suffix(".json")
            filepath = str(path)

    if fmt == "json":
        content = json.dumps(data, indent=2, default=str, ensure_ascii=False)
    else:
        content = yaml_str

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

    size = path.stat().st_size
    console.print(f"  [green]Snapshot guardado:[/green] {filepath} ({size:,} bytes)")

    logger.snapshot_created(filepath=filepath, format=fmt, size_bytes=size)


def run_snapshot(
    json_output: bool = False,
    compact: bool = False,
    output: Optional[str] = None,
) -> None:
    """Ejecuta el snapshot del sistema.

    Args:
        json_output: Si True, imprime el snapshot como JSON.
        compact: Si True, imprime output compacto.
        output: Si proporcionado, guarda a archivo (JSON o YAML).
    """
    start_time = time.time()
    logger.command_start("snapshot", {"json": json_output, "compact": compact, "output": output})

    # Recolectar datos
    report = _collect_snapshot()

    # Guardar a archivo si se solicito
    if output:
        console.print()
        console.print(Panel(
            "[bold cyan]DevMind Snapshot[/bold cyan] — Exportando estado del sistema",
            border_style="cyan",
        ))
        console.print()
        _save_to_file(report, output)
        console.print()
        return

    # Renderizar segun modo
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
    logger.command_end("snapshot", duration)
