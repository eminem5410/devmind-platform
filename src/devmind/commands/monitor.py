"""devmind monitor — Real-time AI environment monitor."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from datetime import datetime

import psutil
import typer
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from devmind.utils.docker import check_docker
from devmind.utils.gpu import detect_all_gpus
from devmind.utils.ollama import check_ollama

console = Console()

# ── Data Collection ──

def _fetch_json(url: str, timeout: float = 3) -> dict | None:
    """Fetch JSON from a URL."""
    try:
        req = urllib.request.Request(url, method="GET")
        resp = urllib.request.urlopen(req, timeout=timeout)
        return json.loads(resp.read())
    except Exception:
        return None


def _ollama_models() -> list[str]:
    """Get list of Ollama models via API."""
    data = _fetch_json("http://localhost:11434/api/tags")
    if data:
        return [m.get("name", "") for m in data.get("models", [])]
    return []


def _ollama_ps() -> dict | None:
    """Get Ollama process/memory info via /api/ps."""
    return _fetch_json("http://localhost:11434/api/ps")


def _tokens_today() -> int:
    """Get tokens used today from SQLite."""
    try:
        from devmind.db.manager import get_daily_activity
        today = datetime.now().strftime("%Y-%m-%d")
        rows = get_daily_activity(days=1)
        for r in rows:
            if r.get("date") == today:
                return r.get("tokens", 0)
    except Exception:
        pass
    return 0


def _pressure_color(pct: float) -> str:
    """Return color based on resource pressure."""
    if pct >= 90:
        return "red"
    elif pct >= 70:
        return "yellow"
    return "green"


def _health_score(cpu: float, ram_pct: float, ollama: bool, disk_pct: float) -> int:
    """Compute a 0-100 health score."""
    score = 100
    if cpu > 90:
        score -= 20
    elif cpu > 70:
        score -= 10
    if ram_pct > 90:
        score -= 25
    elif ram_pct > 75:
        score -= 10
    if not ollama:
        score -= 15
    if disk_pct > 90:
        score -= 20
    elif disk_pct > 80:
        score -= 10
    return max(0, min(100, score))


def _collect_data(ai_mode: bool = False) -> dict:
    """Collect all monitor data."""
    # System
    cpu = psutil.cpu_percent(interval=0.3)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    ram_total = mem.total / (1024**3)
    ram_used = mem.used / (1024**3)
    ram_pct = mem.percent
    disk_free = disk.free / (1024**3)
    disk_total = disk.total / (1024**3)
    disk_pct = (disk.used / disk.total) * 100

    # GPU
    gpus = detect_all_gpus()
    gpu_info = ""
    gpu_vram = ""
    if gpus:
        g = gpus[0]
        gpu_info = g.name
        if g.vram_total_mb:
            used = g.vram_used_mb or 0
            gpu_vram = f"{used}/{g.vram_total_mb} MB"

    # Ollama
    ollama_status = check_ollama()
    models = _ollama_models()
    ollama_running = ollama_status.running
    model_str = ", ".join(models[:3]) if models else "none"
    if len(models) > 3:
        model_str += f" (+{len(models)-3})"

    # Docker
    docker = check_docker()

    # Health
    health = _health_score(cpu, ram_pct, ollama_running, disk_pct)

    result = {
        "cpu": cpu,
        "cpu_cores": psutil.cpu_count(),
        "ram_used": round(ram_used, 1),
        "ram_total": round(ram_total, 1),
        "ram_pct": ram_pct,
        "disk_free": round(disk_free, 1),
        "disk_total": round(disk_total, 1),
        "disk_pct": round(disk_pct, 1),
        "gpu": gpu_info,
        "gpu_vram": gpu_vram,
        "ollama_running": ollama_running,
        "ollama_version": ollama_status.version or "",
        "models": models,
        "models_display": model_str,
        "docker_running": docker.running,
        "docker_containers": docker.containers_running,
        "docker_images": docker.images_count,
        "health": health,
        "timestamp": datetime.now().strftime("%H:%M:%S"),
    }

    # AI-specific metrics
    if ai_mode:
        ollama_ps = _ollama_ps()
        ollama_ram = 0.0
        active_model = ""
        if ollama_ps:
            for model_info in ollama_ps.get("models", []):
                ollama_ram += model_info.get("size", 0) / (1024**3)
                if not active_model:
                    active_model = model_info.get("name", "")
        result["ollama_ram_gb"] = round(ollama_ram, 2)
        result["active_model"] = active_model
        result["tokens_today"] = _tokens_today()

        # System pressure
        pressures = []
        if cpu > 80:
            pressures.append("CPU")
        if ram_pct > 80:
            pressures.append("RAM")
        if ollama_ram > 0 and ollama_ram > ram_total * 0.6:
            pressures.append("VRAM")
        result["pressure"] = "HIGH" if len(pressures) >= 2 else ("MEDIUM" if pressures else "LOW")
        result["pressure_items"] = pressures

    return result


# ── Render Functions ──

def _render_dashboard(data: dict, ai_mode: bool = False) -> Panel:
    """Build the Rich dashboard panel."""
    # System table
    sys_table = Table(show_header=False, box=None, padding=(0, 1), expand=True)
    sys_table.add_column("Label", style="bold cyan", width=14)
    sys_table.add_column("Value")

    cpu_color = _pressure_color(data["cpu"])
    ram_color = _pressure_color(data["ram_pct"])
    disk_color = _pressure_color(data["disk_pct"])
    health_color = _pressure_color(100 - data["health"])  # invert: low health = red

    sys_table.add_row("CPU", f"[{cpu_color}]{data['cpu']}%[/] ({data['cpu_cores']} cores)")
    sys_table.add_row("RAM", f"[{ram_color}]{data['ram_used']} / {data['ram_total']} GB[/] ({data['ram_pct']}%)")
    sys_table.add_row("Disk", f"[{disk_color}]{data['disk_free']} GB free[/] / {data['disk_total']} GB")

    # AI table
    ai_table = Table(show_header=False, box=None, padding=(0, 1), expand=True)
    ai_table.add_column("Label", style="bold cyan", width=14)
    ai_table.add_column("Value")

    ollama_status = "[green]Running[/]" if data["ollama_running"] else "[red]Stopped[/]"
    ver = f" v{data['ollama_version']}" if data["ollama_version"] else ""
    ai_table.add_row("Ollama", f"{ollama_status}{ver}")
    ai_table.add_row("Models", data["models_display"])

    if data["gpu"]:
        ai_table.add_row("GPU", data["gpu"])
        if data["gpu_vram"]:
            ai_table.add_row("VRAM", data["gpu_vram"])

    docker_status = "[green]Running[/]" if data["docker_running"] else "[dim]Stopped[/]"
    ai_table.add_row("Docker", f"{docker_status} ({data['docker_containers']} containers)")

    # AI-specific metrics
    if ai_mode:
        ai_table.add_row("Ollama RAM", f"{data.get('ollama_ram_gb', 0)} GB")
        active = data.get("active_model", "")
        ai_table.add_row("Active model", active if active else "[dim]none[/]")
        tokens = data.get("tokens_today", 0)
        ai_table.add_row("Tokens today", f"{tokens:,}")

        pressure = data.get("pressure", "LOW")
        p_color = {"LOW": "green", "MEDIUM": "yellow", "HIGH": "red"}[pressure]
        p_items = " + ".join(data.get("pressure_items", [])) if data.get("pressure_items") else ""
        p_str = f"[{p_color}]{pressure}[/]"
        if p_items:
            p_str += f" [dim]({p_items})[/]"
        ai_table.add_row("Pressure", p_str)

    # Health bar
    health = data["health"]
    bar_len = 20
    filled = int(health / 100 * bar_len)
    bar = "█" * filled + "░" * (bar_len - filled)
    ai_table.add_row("Health", f"[{health_color}]{bar}[/] {health}/100")

    # Layout
    title = "DevMind AI Monitor"
    if ai_mode:
        title += " [dim](AI mode)[/]"

    layout = Table.grid(expand=True)
    layout.add_column(ratio=1)
    layout.add_column(ratio=1)
    layout.add_row(
        Panel(sys_table, title="[bold]System[/]", border_style="blue"),
        Panel(ai_table, title="[bold]AI Stack[/]", border_style="green"),
    )

    footer = Text()
    footer.append(f" Updated: {data['timestamp']} ", style="dim")

    return Panel(
        layout,
        title=f"[bold]{title}[/]",
        border_style="cyan",
        subtitle=footer,
    )


def _render_compact(data: dict) -> str:
    """Compact single-line output."""
    ollama = "RUNNING" if data["ollama_running"] else "STOPPED"
    return (
        f"CPU: {data['cpu']}% | "
        f"RAM: {data['ram_used']}/{data['ram_total']}GB | "
        f"Disk: {data['disk_free']}GB free | "
        f"Ollama: {ollama} | "
        f"Health: {data['health']}/100"
    )


# ── Commands ──

def run_monitor(
    once: bool = typer.Option(False, "--once", help="Single snapshot, no loop"),
    json_output: bool = typer.Option(False, "--json", help="JSON output"),
    ai_mode: bool = typer.Option(False, "--ai", help="Show AI-specific metrics"),
    interval: float = typer.Option(2.0, "--interval", "-i", help="Refresh interval in seconds"),
) -> None:
    """Real-time AI environment monitor."""
    data = _collect_data(ai_mode=ai_mode)

    if json_output:
        # Clean data for JSON output
        out = {
            "cpu_percent": data["cpu"],
            "cpu_cores": data["cpu_cores"],
            "ram_used_gb": data["ram_used"],
            "ram_total_gb": data["ram_total"],
            "ram_percent": data["ram_pct"],
            "disk_free_gb": data["disk_free"],
            "disk_total_gb": data["disk_total"],
            "disk_percent": data["disk_pct"],
            "gpu": data["gpu"],
            "gpu_vram": data["gpu_vram"],
            "ollama": {
                "running": data["ollama_running"],
                "version": data["ollama_version"],
                "models": data["models"],
            },
            "docker": {
                "running": data["docker_running"],
                "containers": data["docker_containers"],
                "images": data["docker_images"],
            },
            "health": data["health"],
            "timestamp": data["timestamp"],
        }
        if ai_mode:
            out["ai"] = {
                "ollama_ram_gb": data.get("ollama_ram_gb", 0),
                "active_model": data.get("active_model", ""),
                "tokens_today": data.get("tokens_today", 0),
                "pressure": data.get("pressure", "LOW"),
            }
        console.print_json(json.dumps(out, indent=2))
        return

    if once:
        console.print(_render_dashboard(data, ai_mode=ai_mode))
        return

    # Interactive mode
    try:
        with Live(
            _render_dashboard(data, ai_mode=ai_mode),
            console=console,
            refresh_per_second=1,
        ) as live:
            while True:
                time.sleep(interval)
                data = _collect_data(ai_mode=ai_mode)
                live.update(_render_dashboard(data, ai_mode=ai_mode))
    except KeyboardInterrupt:
        console.print("\n[dim]Monitor stopped.[/]")
