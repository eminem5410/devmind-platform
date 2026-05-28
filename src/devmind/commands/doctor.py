"""
Comando: devmind doctor
Diagnostico completo del sistema con severidad, recomendaciones y --json.

Modos de salida:
  - Terminal (Rich): Colores, tablas, paneles, iconos de severidad.
  - JSON (--json): Estructura Pydantic serializada para APIs, GUIs, telemetry.
"""

from __future__ import annotations

import json
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from devmind.models.diagnostic import (
    DiagnosticCheck,
    DiagnosticReport,
    Recommendation,
    Severity,
    SystemData,
)
from devmind.utils.gpu import detect_all_gpus, detect_cuda_toolkit, detect_vulkan
from devmind.utils.docker import check_docker
from devmind.utils.ollama import check_ollama
from devmind.utils.system import get_system_info
from devmind.utils.recommendations import generate_recommendations
from devmind.utils.logging import logger

console = Console()


# ── Recoleccion de datos ───────────────────────────────────────────────────

def _collect_system_data() -> SystemData:
    """Obtiene datos del sistema operativo y hardware."""
    sys_info = get_system_info()
    return SystemData(
        os_name=sys_info.os_name,
        os_version=sys_info.os_version,
        kernel=sys_info.kernel,
        arch=sys_info.arch,
        python_version=sys_info.python_version,
        ram_total_gb=sys_info.ram_total_gb,
        ram_used_gb=sys_info.ram_used_gb,
        cpu_name=sys_info.cpu_name,
        cpu_cores=sys_info.cpu_cores,
        disk_free_gb=sys_info.disk_free_gb,
    )


def _collect_checks(system: SystemData) -> list[DiagnosticCheck]:
    """Ejecuta todos los checks diagnosticos y retorna la lista."""
    checks: list[DiagnosticCheck] = []
    sys_info = get_system_info()

    # ── Sistema ────────────────────────────────────────────────────────
    checks.append(DiagnosticCheck(
        name="OS",
        category="system",
        severity=Severity.INFO,
        status="ok",
        value=f"{system.os_name} {system.os_version}",
        message=f"Kernel {system.kernel}, {system.arch}",
    ))

    py_major, py_minor = (system.python_version.split(".")[:2]
                          if system.python_version else ("0", "0"))
    py_sev = Severity.WARNING if int(py_minor) >= 14 else Severity.INFO
    checks.append(DiagnosticCheck(
        name="Python",
        category="system",
        severity=py_sev,
        status="ok",
        value=system.python_version,
        message=("Version muy reciente — puede haber incompatibilidades con tooling AI"
                 if int(py_minor) >= 14 else "Version compatible"),
    ))

    if system.cpu_name:
        checks.append(DiagnosticCheck(
            name="CPU",
            category="system",
            severity=Severity.INFO,
            status="ok",
            value=f"{system.cpu_name} ({system.cpu_cores} cores)",
        ))

    if system.ram_total_gb:
        ram_sev = Severity.WARNING if system.ram_total_gb < 8 else Severity.INFO
        used_pct = round((system.ram_used_gb or 0) / system.ram_total_gb * 100, 0)
        checks.append(DiagnosticCheck(
            name="RAM",
            category="system",
            severity=ram_sev,
            status="ok",
            value=f"{system.ram_used_gb or 0} / {system.ram_total_gb} GB ({int(used_pct)}%)",
            message=("RAM limitada para modelos grandes" if system.ram_total_gb < 8
                     else "RAM adecuada para desarrollo AI"),
        ))

    if system.disk_free_gb:
        disk_sev = (Severity.ERROR if system.disk_free_gb < 20
                    else Severity.WARNING if system.disk_free_gb < 50
                    else Severity.INFO)
        checks.append(DiagnosticCheck(
            name="Disco libre",
            category="system",
            severity=disk_sev,
            status="ok",
            value=f"{system.disk_free_gb} GB",
            message=("Espacio muy limitado para modelos AI" if system.disk_free_gb < 20
                     else "Espacio suficiente" if system.disk_free_gb > 50
                     else "Espacio ajustado para modelos grandes"),
        ))

    # ── Herramientas ──────────────────────────────────────────────────
    checks.append(DiagnosticCheck(
        name="Git",
        category="tools",
        severity=Severity.ERROR if not sys_info.git_installed else Severity.INFO,
        status="ok" if sys_info.git_installed else "missing",
        value="instalado" if sys_info.git_installed else None,
        message=("Control de versiones disponible"
                 if sys_info.git_installed else "Git es necesario para proyectos AI"),
    ))

    checks.append(DiagnosticCheck(
        name="pip",
        category="tools",
        severity=Severity.INFO if sys_info.pip_installed else Severity.WARNING,
        status="ok" if sys_info.pip_installed else "missing",
        value="instalado" if sys_info.pip_installed else None,
    ))

    # ── GPU ───────────────────────────────────────────────────────────
    gpus = detect_all_gpus()
    if gpus:
        checks.append(DiagnosticCheck(
            name="GPU Dedicada",
            category="gpu",
            severity=Severity.INFO,
            status="ok",
            value=", ".join(f"{g.vendor} {g.name}" for g in gpus),
        ))

        nvidia_gpus = [g for g in gpus if g.vendor.upper() == "NVIDIA"]
        if nvidia_gpus:
            checks.append(DiagnosticCheck(
                name="NVIDIA GPU",
                category="gpu",
                severity=Severity.INFO,
                status="ok",
                value=nvidia_gpus[0].name,
                message=f"Driver {nvidia_gpus[0].driver_version or 'N/A'}, "
                        f"VRAM {nvidia_gpus[0].vram_total_mb or '?'}MB",
            ))

        cuda_ver = detect_cuda_toolkit()
        checks.append(DiagnosticCheck(
            name="CUDA Toolkit",
            category="gpu",
            severity=Severity.INFO if cuda_ver else Severity.WARNING,
            status="ok" if cuda_ver else "missing",
            value=cuda_ver,
            message=("Listo para compilacion CUDA" if cuda_ver
                     else "nvidia-smi funciona pero nvcc no esta en PATH"),
        ))
    else:
        checks.append(DiagnosticCheck(
            name="GPU Dedicada",
            category="gpu",
            severity=Severity.WARNING,
            status="missing",
            value=None,
            message="No se detectaron GPUs — operando en CPU-only",
        ))

    vulkan = detect_vulkan()
    checks.append(DiagnosticCheck(
        name="Vulkan",
        category="gpu",
        severity=Severity.INFO if vulkan else Severity.INFO,
        status="ok" if vulkan else "missing",
        value=vulkan,
    ))

    # ── Docker ────────────────────────────────────────────────────────
    docker = check_docker()
    if docker.installed:
        checks.append(DiagnosticCheck(
            name="Docker",
            category="docker",
            severity=Severity.INFO,
            status="ok",
            value=docker.version,
            message=f"{docker.containers_running} contenedores activos, "
                    f"{docker.images_count} imagenes",
        ))
        checks.append(DiagnosticCheck(
            name="Docker Daemon",
            category="docker",
            severity=Severity.INFO if docker.running else Severity.ERROR,
            status="ok" if docker.running else "error",
            value="ejecutando" if docker.running else None,
            message=docker.error if not docker.running else None,
        ))
        checks.append(DiagnosticCheck(
            name="Docker Compose",
            category="docker",
            severity=Severity.INFO if docker.compose_version else Severity.WARNING,
            status="ok" if docker.compose_version else "missing",
            value=docker.compose_version,
        ))
    else:
        checks.append(DiagnosticCheck(
            name="Docker",
            category="docker",
            severity=Severity.WARNING,
            status="missing",
            value=None,
            message="Docker no instalado — necesario para contenedores AI",
        ))

    # ── Ollama ────────────────────────────────────────────────────────
    ollama = check_ollama()
    if ollama.installed:
        checks.append(DiagnosticCheck(
            name="Ollama",
            category="ollama",
            severity=Severity.INFO,
            status="ok",
            value=ollama.version,
        ))
        checks.append(DiagnosticCheck(
            name="Ollama Server",
            category="ollama",
            severity=Severity.INFO if ollama.running else Severity.ERROR,
            status="ok" if ollama.running else "error",
            value="ejecutando" if ollama.running else None,
            message=ollama.error if not ollama.running else None,
        ))
        if ollama.running:
            if ollama.models:
                checks.append(DiagnosticCheck(
                    name="Ollama Modelos",
                    category="ollama",
                    severity=Severity.INFO,
                    status="ok",
                    value=", ".join(ollama.models),
                ))
            else:
                checks.append(DiagnosticCheck(
                    name="Ollama Modelos",
                    category="ollama",
                    severity=Severity.WARNING,
                    status="warning",
                    value="Ninguno instalado",
                    message="Ollama listo pero sin modelos descargados",
                ))
    else:
        checks.append(DiagnosticCheck(
            name="Ollama",
            category="ollama",
            severity=Severity.WARNING,
            status="missing",
            value=None,
            message="Ollama no instalado — motor de inferencia local recomendado",
        ))

    return checks


# ── Renderizado Rich ──────────────────────────────────────────────────────

def _severity_badge(sev: Severity) -> Text:
    """Crea un badge de severidad con color."""
    colors = {
        Severity.INFO: "cyan",
        Severity.WARNING: "yellow",
        Severity.ERROR: "red",
        Severity.CRITICAL: "bold red",
    }
    labels = {
        Severity.INFO: "INFO",
        Severity.WARNING: "WARN",
        Severity.ERROR: "ERR ",
        Severity.CRITICAL: "CRIT",
    }
    return Text(f" [{labels[sev]}] ", style=f"on {colors[sev]} black")


def _render_rich(report: DiagnosticReport) -> None:
    """Renderiza el reporte completo en la terminal con Rich."""
    console.print()
    console.print(Panel(
        "[bold cyan]DevMind Doctor[/bold cyan] — Diagnostico inteligente del sistema",
        border_style="cyan",
    ))
    console.print()

    # ── Health Score ───────────────────────────────────────────────────
    summary = report.summary
    score = summary.get("health_score", 0)
    label = summary.get("health_label", "?")
    score_color = ("green" if score >= 75
                   else "yellow" if score >= 50
                   else "red" if score >= 25
                   else "bold red")

    console.print(f"  [bold]Salud del sistema:[/bold] [{score_color}]{score}/100[/] ({label})")

    # Barra visual de salud
    bar_len = 30
    filled = round(score / 100 * bar_len)
    bar = "[green]" + "█" * filled + "[/]" + "[dim]" + "░" * (bar_len - filled) + "[/]"
    console.print(f"  {bar}")
    console.print()

    # ── Checks por categoria ───────────────────────────────────────────
    categories = {
        "system": ("Sistema", "blue"),
        "tools": ("Herramientas", "magenta"),
        "gpu": ("GPU / Aceleracion", "green"),
        "docker": ("Docker", "blue"),
        "ollama": ("Ollama", "cyan"),
    }

    for cat_key, (cat_name, cat_color) in categories.items():
        cat_checks = [c for c in report.checks if c.category == cat_key]
        if not cat_checks:
            continue

        console.print(f"[bold][{cat_color}]{cat_name}[/{cat_color}][/bold]")

        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Badge", width=8)
        table.add_column("Check", width=20, style="bold")
        table.add_column("Value")
        table.add_column("Message", style="dim", max_width=50)

        for check in cat_checks:
            badge = _severity_badge(check.severity)
            value = check.value or "[dim]N/A[/dim]"
            msg = check.message or ""
            table.add_row(badge, check.name, value, msg)

        console.print(table)
        console.print()

    # ── Recomendaciones ───────────────────────────────────────────────
    if report.recommendations:
        console.print("[bold]Recomendaciones[/bold]")
        console.print()

        for i, rec in enumerate(report.recommendations, 1):
            # Header con icono de severidad
            sev_color = rec.severity.color
            icon = rec.severity.icon

            # Titulo
            console.print(f"  {icon} [bold][{sev_color}]{rec.title}[/{sev_color}][/bold]")

            # Mensaje (indentado, sin dobles puntos)
            for line in rec.message.split(". "):
                clean = line.strip().rstrip(".")
                if clean:
                    console.print(f"    [dim]{clean}.[/dim]")

            # Accion
            if rec.action:
                console.print(f"    [bold]Accion:[/bold] {rec.action}")

            # Comando
            if rec.command:
                console.print(f"    [green]$ {rec.command}[/green]")

            # Reparable badge
            if rec.repairable:
                console.print("    [dim][auto-reparable con devmind repair][/dim]")

            # Separador (solo si no es el ultimo)
            if i < len(report.recommendations):
                console.print()

        console.print()

    # ── Resumen final ─────────────────────────────────────────────────
    total = summary.get("total_checks", 0)
    warns = summary.get("warnings", 0)
    errs = summary.get("errors", 0)
    crits = summary.get("critical", 0)
    repairable = summary.get("repairable", 0)

    if errs == 0 and crits == 0 and warns == 0:
        panel_content = (
            "[bold green]Tu sistema esta listo para desarrollo de IA[/bold green]\n"
            f"[dim]{total} checks pasados, 0 issues detectados[/dim]"
        )
        border = "green"
    elif crits > 0 or errs > 0:
        panel_content = (
            f"[red]Se encontraron {crits} critico(s) + {errs} error(es)[/red]\n"
            f"[dim]{warns} advertencia(s) — {repairable} reparable(s) con "
            f"'devmind repair'[/dim]"
        )
        border = "red"
    else:
        panel_content = (
            f"[yellow]{warns} advertencia(s) encontradas[/yellow]\n"
            f"[dim]{repairable} reparable(s) automaticamente con "
            f"'devmind repair'[/dim]"
        )
        border = "yellow"

    console.print(Panel(panel_content, border_style=border))

    if repairable > 0:
        console.print()
        console.print("[dim]Ejecuta [bold]devmind repair all[/bold] para reparar "
                      f"automaticamente {repairable} issue(s).[/dim]")

    console.print()


# ── Renderizado JSON ──────────────────────────────────────────────────────

def _render_json(report: DiagnosticReport) -> None:
    """Renderiza el reporte como JSON estructurado."""
    console.print_json(json.dumps(
        report.model_dump(mode="json"),
        indent=2,
        default=str,
    ))


# ── Renderizado Compacto ──────────────────────────────────────────────────

def _fmt_check(report: DiagnosticReport, name: str) -> str:
    """Busca un check por nombre y retorna 'OK', 'WARN', 'ERR', 'CRIT' o '--'."""
    for c in report.checks:
        if c.name == name:
            sev = c.severity
            if sev in (Severity.INFO,) and c.status == "ok":
                return "[green]OK[/green]"
            elif sev == Severity.WARNING:
                return "[yellow]WARN[/yellow]"
            elif sev == Severity.ERROR:
                return "[red]ERR[/red]"
            elif sev == Severity.CRITICAL:
                return "[bold red]CRIT[/bold red]"
            return "[dim]--[/dim]"
    return "[dim]--[/dim]"


def _check_value(report: DiagnosticReport, name: str) -> str:
    """Retorna el value de un check por nombre."""
    for c in report.checks:
        if c.name == name:
            return c.value or "--"
    return "--"


def _render_compact(report: DiagnosticReport) -> None:
    """Renderiza output compacto de una pantalla — ideal para CI y scripting.

    Output esperado:
      DevMind v0.2.0 | Health: 93/100 (Excelente) | Warnings: 3 | Errors: 0
      OS: Linux x86_64 | Python: 3.14.4 | CPU: i5-7400 (4c)
      RAM: 6.3/7.1 GB (89%) | Disk: 287.2 GB
      GPU: WARN | CUDA: -- | Vulkan: OK
      Docker: OK (29.4.3) | Compose: OK (5.1.3)
      Ollama: OK (0.24.0) | Models: phi3:mini
      Git: OK | pip: OK
      Repairable: 0
    """
    s = report.summary
    sys = report.system

    # Helpers
    def _ok_or(check_name: str) -> str:
        val = _check_value(report, check_name)
        if val == "instalado" or val == "ejecutando":
            return "[green]OK[/green]"
        elif val == "--":
            return "[dim]--[/dim]"
        else:
            return val

    # Linea 1: Header
    score = s.get("health_score", 0)
    label = s.get("health_label", "?")
    sc = "green" if score >= 75 else "yellow" if score >= 50 else "red"
    warns = s.get("warnings", 0)
    errs = s.get("errors", 0)
    crits = s.get("critical", 0)

    console.print(
        f"[bold cyan]DevMind[/bold cyan] v{report.version} | "
        f"Health: [{sc}]{score}/100[/] ({label}) | "
        f"[yellow]W:{warns}[/] | "
        f"[red]E:{errs}[/]"
        f"{' | [bold red]C:' + str(crits) + '[/]' if crits else ''}"
    )

    # Linea 2: Sistema
    ram_val = _check_value(report, "RAM")
    disk_val = _check_value(report, "Disco libre")
    console.print(
        f"OS: {sys.os_name} {sys.arch} | "
        f"Python: {sys.python_version} | "
        f"CPU: {(sys.cpu_name or '?').split('@')[0].strip()} ({sys.cpu_cores}c)"
    )

    # Linea 3: RAM + Disco
    console.print(f"RAM: {ram_val} | Disk: {disk_val}")

    # Linea 4: GPU
    gpu_status = _fmt_check(report, "GPU Dedicada")
    cuda_val = _check_value(report, "CUDA Toolkit")
    if cuda_val == "--":
        cuda_display = "[dim]--[/dim]"
    else:
        cuda_display = f"[green]{cuda_val}[/green]"
    vulkan_status = _fmt_check(report, "Vulkan")
    console.print(f"GPU: {gpu_status} | CUDA: {cuda_display} | Vulkan: {vulkan_status}")

    # Linea 5: Docker
    docker_ver = _check_value(report, "Docker")
    docker_daemon = _fmt_check(report, "Docker Daemon")
    compose_ver = _check_value(report, "Docker Compose")
    compose_display = compose_ver if compose_ver not in ("--", "N/A") else "[dim]--[/dim]"
    console.print(
        f"Docker: {docker_daemon} ({docker_ver}) | Compose: {compose_display}"
    )

    # Linea 6: Ollama
    ollama_ver = _check_value(report, "Ollama")
    ollama_server = _fmt_check(report, "Ollama Server")
    models = _check_value(report, "Ollama Modelos")
    console.print(f"Ollama: {ollama_server} ({ollama_ver}) | Models: {models}")

    # Linea 7: Tools
    console.print(f"Git: {_ok_or('Git')} | pip: {_ok_or('pip')}")

    # Linea 8: Repairable
    repairable = s.get("repairable", 0)
    r_color = "green" if repairable == 0 else "yellow"
    console.print(f"Repairable: [{r_color}]{repairable}[/]")

    # Top warnings (una linea resumen)
    warn_recs = [r for r in report.recommendations if r.severity in (Severity.WARNING,)]
    if warn_recs:
        titles = [r.title for r in warn_recs[:3]]
        console.print(f"[dim]Warnings: {' | '.join(titles)}[/dim]")
        if len(warn_recs) > 3:
            console.print(f"[dim]  + {len(warn_recs) - 3} more[/dim]")


# ── Entry point ───────────────────────────────────────────────────────────

def run_doctor(
    json_output: bool = False,
    compact: bool = False,
) -> None:
    """Ejecuta el diagnostico completo del sistema.

    Args:
        json_output: Si True, imprime el reporte como JSON en vez de Rich.
        compact: Si True, imprime output compacto de una pantalla (CI/scripting).
    """
    import time
    start_time = time.time()
    logger.command_start("doctor", {"json": json_output, "compact": compact})

    # 1. Recolectar datos del sistema
    system = _collect_system_data()

    # 2. Ejecutar checks
    checks = _collect_checks(system)

    # 3. Construir reporte
    report = DiagnosticReport(
        system=system,
        checks=checks,
    )

    # 4. Generar recomendaciones
    report.recommendations = generate_recommendations(report)

    # 5. Calcular resumen
    report.compute_summary()

    # 6. Registrar en log estructurado
    logger.doctor_run(
        health_score=report.summary.get("health_score", 0),
        total_checks=report.summary.get("total_checks", 0),
        warnings=report.summary.get("warnings", 0),
        errors=report.summary.get("errors", 0),
        repairable=report.summary.get("repairable", 0),
    )

    # 7. Renderizar
    if json_output:
        _render_json(report)
    elif compact:
        _render_compact(report)
    else:
        _render_rich(report)

    duration = time.time() - start_time
    logger.command_end("doctor", duration)
