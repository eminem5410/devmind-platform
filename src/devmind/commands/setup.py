"""
Comando: devmind setup
Configura un ambiente completo de desarrollo AI usando perfiles.

Perfiles:
  devmind setup list          Lista perfiles disponibles
  devmind setup local-llm     Chat local con Ollama + OpenWebUI
  devmind setup ai-dev        Entorno completo AI: Docker + Ollama + Jupyter
  devmind setup rag-lab       Stack RAG: Ollama + ChromaDB + FastAPI

Opciones:
  --force     Sobreescribir archivos existentes
  --dry-run   Mostrar que se crearia sin escribir nada
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Table

from devmind.data.profiles import (
    get_available_profiles,
    generate_profile,
)
from devmind.utils.docker import check_docker
from devmind.utils.logging import logger
from devmind.utils.ollama import check_ollama
from devmind.utils.system import get_system_info

console = Console()


def _check_prerequisites(profile_name: str) -> list[str]:
    """Verifica prerequisitos y retorna lista de issues."""
    issues: list[str] = []
    docker = check_docker()
    ollama = check_ollama()

    # Todos los perfiles necesitan Docker
    if not docker.installed:
        issues.append("Docker no esta instalado (ejecuta 'devmind repair docker')")
    elif not docker.running:
        issues.append("Docker daemon no esta ejecutando (ejecuta 'sudo systemctl start docker')")

    # ai-dev y rag-lab necesitan Ollama nativo
    if profile_name in ("ai-dev", "rag-lab"):
        if not ollama.installed:
            issues.append("Ollama no esta instalado (ejecuta 'devmind repair ollama')")
        elif not ollama.running:
            issues.append("Ollama no esta ejecutando (ejecuta 'ollama serve')")

    return issues


def run_setup_profile(
    profile_name: str,
    output_dir: Optional[str] = None,
    force: bool = False,
    dry_run: bool = False,
) -> None:
    """Ejecuta el setup de un perfil."""
    start_time = time.time()
    logger.command_start("setup", {"profile": profile_name, "dry_run": dry_run})

    console.print()
    console.print(Panel(
        f"[bold cyan]DevMind Setup[/bold cyan] — Perfil: [bold]{profile_name}[/bold]",
        border_style="cyan",
    ))
    console.print()

    # ── Verificar perfil existe ──────────────────────────────────────────
    profiles = get_available_profiles()
    profile_names = [p["name"] for p in profiles]
    if profile_name not in profile_names:
        console.print(f"  [red]Perfil desconocido:[/red] {profile_name}")
        console.print(f"  [dim]Disponibles: {', '.join(profile_names)}[/dim]")
        console.print()
        return

    # ── Verificar prerequisitos ─────────────────────────────────────────
    issues = _check_prerequisites(profile_name)
    if issues:
        console.print("  [yellow]Prerequisitos faltantes:[/yellow]")
        for issue in issues:
            console.print(f"    [red]![/red] {issue}")
        console.print()
        console.print("  [dim]Ejecuta 'devmind repair all' para resolver automaticamente.[/dim]")
        console.print()
        logger.command_end("setup", time.time() - start_time, success=False)
        return

    # ── Obtener datos del sistema ───────────────────────────────────────
    sys_info = get_system_info()
    ollama = check_ollama()
    ram_gb = sys_info.ram_total_gb or 4.0
    has_gpu = False
    if ollama.models:
        console.print(f"  [dim]Hardware: {sys_info.cpu_name} ({sys_info.cpu_cores}c), "
                      f"{ram_gb} GB RAM[/dim]")
    else:
        console.print(f"  [dim]Hardware: {sys_info.cpu_name} ({sys_info.cpu_cores}c), "
                      f"{ram_gb} GB RAM, CPU-only[/dim]")
    console.print()

    # ── Generar perfil ──────────────────────────────────────────────────
    console.print(f"  [bold cyan]>>>[/bold cyan] Generando perfil [bold]{profile_name}[/bold]...")
    console.print()

    try:
        profile = generate_profile(
            name=profile_name,
            ram_gb=ram_gb,
            has_gpu=has_gpu,
            ollama_version=ollama.version if ollama.installed else None,
        )
    except ValueError as e:
        console.print(f"  [red]Error:[/red] {e}")
        console.print()
        return

    # ── Mostrar archivos a crear ────────────────────────────────────────
    target = Path(output_dir) if output_dir else Path.cwd()

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Archivo", style="bold")
    table.add_column("Tamano", justify="right")
    table.add_column("Descripcion")

    for filename, content in profile.files.items():
        size = len(content)
        if size > 1024:
            size_str = f"{size / 1024:.1f} KB"
        else:
            size_str = f"{size} B"

        descriptions = {
            "docker-compose.yml": "Stack Docker",
            "requirements.txt": "Dependencias Python",
            ".env": "Variables de entorno",
            "README.md": "Documentacion",
            "rag_engine.py": "Motor RAG (ingest + query)",
            "api.py": "API FastAPI",
        }
        desc = descriptions.get(filename, "")
        table.add_row(f"{target / filename}", size_str, desc)

    console.print(table)
    console.print()

    # ── Confirmar ────────────────────────────────────────────────────────
    if not dry_run:
        if not force:
            # Verificar si archivos ya existen
            existing = [
                f for f in profile.files
                if (target / f).exists()
            ]
            if existing:
                console.print(f"  [yellow]Archivos existentes: {', '.join(existing)}[/yellow]")
                console.print(f"  [dim]Usa --force para sobreescribir[/dim]")
                console.print()

        if not force:
            # Check if directory has content
            if target.exists() and any(target.iterdir()):
                if not Confirm.ask(f"  Crear archivos en [bold]{target}[/bold]?", default=True):
                    console.print("  [dim]Setup cancelado.[/dim]")
                    console.print()
                    return
            else:
                target.mkdir(parents=True, exist_ok=True)

    # ── Escribir archivos ────────────────────────────────────────────────
    if dry_run:
        console.print("  [dim]--dry-run: no se escribieron archivos (modo simulacion)[/dim]")
        console.print()
        return

    # Crear directorios necesarios
    for filename in profile.files:
        filepath = target / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)

    # Escribir archivos
    written = 0
    for filename, content in profile.files.items():
        filepath = target / filename

        if filepath.exists() and not force:
            console.print(f"  [yellow]SKIP[/yellow] {filename} (ya existe, usa --force)")
            continue

        filepath.write_text(content, encoding="utf-8")
        console.print(f"  [green]OK[/green] {filename}")
        written += 1

    console.print()

    # ── Resumen ──────────────────────────────────────────────────────────
    if written > 0:
        console.print(Panel(
            f"[bold green]Perfil '{profile_name}' creado con exito[/bold green]\n"
            f"[dim]{written} archivos escritos en {target}[/dim]",
            border_style="green",
        ))
        console.print()

        # Proximos pasos
        console.print("[bold]Proximos pasos:[/bold]")
        console.print()
        for cmd in profile.post_setup_commands:
            console.print(f"  [green]$[/green] {cmd}")
        console.print()
        console.print(f"  [bold]cd {target}[/bold] para empezar.")
    else:
        console.print("[yellow]No se escribieron archivos.[/yellow]")
        console.print("[dim]Usa --force para sobreescribir existentes.[/dim]")
        console.print()

    logger.command_end("setup", time.time() - start_time)


def run_setup_list() -> None:
    """Lista los perfiles disponibles."""
    console.print()
    console.print(Panel(
        "[bold cyan]DevMind Setup[/bold cyan] — Perfiles disponibles",
        border_style="cyan",
    ))
    console.print()

    profiles = get_available_profiles()

    table = Table(show_header=True, header_style="bold")
    table.add_column("Perfil", style="bold cyan", width=14)
    table.add_column("Descripcion", width=50)
    table.add_column("Requiere")

    for p in profiles:
        needs = ", ".join(p["needs"])
        table.add_row(p["name"], p["description"], needs)

    console.print(table)
    console.print()
    console.print("[dim]Usa: devmind setup <perfil> para crear el ambiente.[/dim]")
    console.print("[dim]Ejemplo: devmind setup local-llm[/dim]")
    console.print()
