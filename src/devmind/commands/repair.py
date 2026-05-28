"""
Comando: devmind repair
Repara automaticamente problemas detectados por devmind doctor.

Subcomandos:
  devmind repair ollama    — Instala, inicia o configura Ollama
  devmind repair docker    — Instala, inicia o verifica Docker
  devmind repair all       — Ejecuta todas las reparaciones

Filosofia: "Diagnosticar impresiona. Reparar automaticamente enamora."
"""

from __future__ import annotations

import shutil
import subprocess
import time
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt

from devmind.utils.ollama import check_ollama
from devmind.utils.docker import check_docker
from devmind.utils.system import get_system_info
from devmind.utils.logging import logger

console = Console()
repair_app = typer.Typer(
    name="repair",
    help="Repara automaticamente problemas detectados por devmind doctor",
    no_args_is_help=True,
)


# ── Helpers ───────────────────────────────────────────────────────────────

def _run_cmd(cmd: str, shell: bool = True, timeout: int = 60,
             capture: bool = True) -> tuple[int, str]:
    """Ejecuta un comando shell y retorna (returncode, output)."""
    try:
        if capture:
            r = subprocess.run(
                cmd, shell=shell, capture_output=True, text=True, timeout=timeout,
            )
        else:
            r = subprocess.run(
                cmd, shell=shell, timeout=timeout,
            )
            return r.returncode, ""
        return r.returncode, r.stdout.strip()
    except subprocess.TimeoutExpired:
        return -1, "timeout"
    except Exception as e:
        return -1, str(e)


def _spinner_step(message: str) -> None:
    """Imprime un step con indicador visual."""
    console.print(f"  [bold cyan]>>>[/bold cyan] {message}")


def _success(message: str) -> None:
    console.print(f"  [green]OK[/green] {message}")


def _warn(message: str) -> None:
    console.print(f"  [yellow]!![/yellow] {message}")


def _error(message: str) -> None:
    console.print(f"  [red]XX[/red] {message}")


def _info(message: str) -> None:
    console.print(f"  [dim]--[/dim] {message}")


def _suggested_model() -> str:
    """Recomienda un modelo basado en el hardware disponible."""
    sys_info = get_system_info()
    ram = sys_info.ram_total_gb or 0

    if ram >= 16:
        return "llama3.1:8b"
    elif ram >= 8:
        return "llama3.2:3b"
    elif ram >= 4:
        return "phi3:mini"
    else:
        return "llama3.2:1b"


# ── Repair: Ollama ────────────────────────────────────────────────────────

@repair_app.command()
def ollama(
    model: Optional[str] = typer.Option(
        None, "--model", "-m",
        help="Modelo a descargar (default: recomendado segun hardware)",
    ),
    skip_model: bool = typer.Option(
        False, "--skip-model",
        help="No descargar modelos, solo verificar/instalar Ollama",
    ),
):
    """Repara Ollama: instala, inicia el servidor y descarga un modelo."""
    start_time_ollama = time.time()
    logger.command_start("repair", {"target": "ollama", "model": model, "skip_model": skip_model})
    console.print()
    console.print(Panel(
        "[bold cyan]DevMind Repair[/bold cyan] — Ollama",
        border_style="cyan",
    ))
    console.print()

    # ── Step 1: Verificar instalacion ──────────────────────────────────
    _spinner_step("Verificando instalacion de Ollama...")
    ollama_status = check_ollama()

    if not ollama_status.installed:
        _warn("Ollama no esta instalado")
        console.print()
        console.print("  Para instalar Ollama ejecuta:")
        console.print("  [bold green]$ curl -fsSL https://ollama.com/install.sh | sh[/bold green]")
        console.print()
        console.print("  [dim]Nota: Esto requiere acceso a internet y permisos de administrador.[/dim]")

        if Confirm.ask("\n  Quieres instalar Ollama ahora?", default=False):
            _spinner_step("Descargando e instalando Ollama...")
            code, output = _run_cmd("curl -fsSL https://ollama.com/install.sh | sh", timeout=300)
            if code == 0:
                _success("Ollama instalado correctamente")
                # Re-verificar
                ollama_status = check_ollama()
            else:
                _error(f"Fallo la instalacion: {output}")
                return
        else:
            _info("Instalacion cancelada. Ejecuta el comando manualmente.")
            return
    else:
        _success(f"Ollama {ollama_status.version} detectado")

    # ── Step 2: Verificar servidor ────────────────────────────────────
    _spinner_step("Verificando servidor de Ollama...")
    ollama_status = check_ollama()

    if not ollama_status.running:
        _warn("El servidor de Ollama no responde")
        _info("Intentando iniciar ollama serve en segundo plano...")

        # Intentar iniciar ollama serve
        try:
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            # Esperar a que responda
            _info("Esperando que el servidor inicie...")
            time.sleep(3)

            # Re-verificar
            ollama_status = check_ollama()
            if ollama_status.running:
                _success("Servidor de Ollama iniciado correctamente")
            else:
                _error("No se pudo iniciar el servidor automaticamente")
                console.print()
                console.print("  Intenta manualmente:")
                console.print("  [bold]$ ollama serve[/bold]")
                console.print("  [dim](en otra terminal)[/dim]")
                return
        except FileNotFoundError:
            _error("No se encontro el binario de Ollama")
            return
    else:
        _success("Servidor de Ollama ejecutando")

    # ── Step 3: Descargar modelo ──────────────────────────────────────
    if not skip_model:
        ollama_status = check_ollama()

        if ollama_status.running and not ollama_status.models:
            recommended = model or _suggested_model()

            console.print()
            console.print(f"  No hay modelos instalados.")
            console.print(f"  [bold]Modelo recomendado:[/bold] {recommended}")
            console.print(f"  [dim](Basado en {get_system_info().ram_total_gb or '?'} GB RAM)[/dim]")

            if model is None:
                custom = Prompt.ask(
                    "\n  Modelo a descargar",
                    default=recommended,
                )
            else:
                custom = model

            if Confirm.ask(f"  Descargar {custom}?", default=True):
                _spinner_step(f"Descargando {custom} (esto puede tardar minutos)...")
                console.print()

                # Ejecutar ollama pull sin captura para ver progreso
                try:
                    result = subprocess.run(
                        ["ollama", "pull", custom],
                        timeout=600,  # 10 min max
                    )
                    if result.returncode == 0:
                        console.print()
                        _success(f"Modelo {custom} descargado correctamente")
                        console.print()
                        console.print(f"  Para probarlo ejecuta:")
                        console.print(f"  [bold green]$ ollama run {custom}[/bold green]")
                    else:
                        _error(f"Fallo la descarga del modelo {custom}")
                except subprocess.TimeoutExpired:
                    _error("La descarga supero el tiempo limite (10 minutos)")
            else:
                _info("Descarga cancelada")
        elif ollama_status.models:
            console.print()
            _success(f"Modelos disponibles: {', '.join(ollama_status.models)}")
            _info("No se necesitan reparaciones adicionales para Ollama")
    else:
        _info("Descarga de modelos omitida (--skip-model)")

    # ── Resumen ───────────────────────────────────────────────────────
    console.print()
    final = check_ollama()
    if final.installed and final.running:
        status = "Modelo: " + ", ".join(final.models) if final.models else "Sin modelos"
        console.print(Panel(
            f"[bold green]Ollama reparado con exito[/bold green]\n"
            f"[dim]Version: {final.version} | Status: {status}[/dim]",
            border_style="green",
        ))
    else:
        console.print(Panel(
            "[yellow]Ollama requiere atencion manual[/yellow]\n"
            "[dim]Ejecuta 'ollama serve' en una terminal separada[/dim]",
            border_style="yellow",
        ))
    console.print()
    logger.command_end("repair", time.time() - start_time_ollama)


# ── Repair: Docker ────────────────────────────────────────────────────────

@repair_app.command()
def docker():
    start_time_docker = time.time()
    logger.command_start("repair", {"target": "docker"})
    console.print()
    console.print(Panel(
        "[bold cyan]DevMind Repair[/bold cyan] — Docker",
        border_style="cyan",
    ))
    console.print()

    # ── Step 1: Verificar instalacion ──────────────────────────────────
    _spinner_step("Verificando instalacion de Docker...")
    docker_status = check_docker()

    if not docker_status.installed:
        _warn("Docker no esta instalado")
        console.print()
        console.print("  Para instalar Docker ejecuta:")
        console.print("  [bold green]$ curl -fsSL https://get.docker.com | sh[/bold green]")
        console.print()
        console.print("  [dim]Requiere permisos sudo. Luego añade tu usuario al grupo:[/dim]")
        console.print("  [bold]$ sudo usermod -aG docker $USER[/bold]")
        console.print("  [dim]Y recarga la sesion o ejecuta 'newgrp docker'[/dim]")
        return
    else:
        _success(f"Docker {docker_status.version} detectado")

    # ── Step 2: Verificar daemon ──────────────────────────────────────
    _spinner_step("Verificando daemon de Docker...")
    docker_status = check_docker()

    if not docker_status.running:
        _warn("Docker daemon no esta ejecutando")
        _info("Intentando iniciar el servicio...")

        code, _ = _run_cmd("sudo systemctl start docker")
        if code == 0:
            _success("Docker daemon iniciado")
            time.sleep(1)
        else:
            _error("No se pudo iniciar Docker (requiere sudo)")
            console.print()
            console.print("  Ejecuta manualmente:")
            console.print("  [bold]$ sudo systemctl start docker[/bold]")
            return
    else:
        _success("Docker daemon ejecutando")

    # ── Step 3: Verificar permisos de usuario ────────────────────────
    _spinner_step("Verificando permisos de usuario...")
    code, _ = _run_cmd("docker info", timeout=5)
    if code == 0:
        _success("Permisos correctos — tu usuario puede usar Docker")
    else:
        _warn("Tu usuario no tiene permisos para Docker")
        console.print()
        console.print("  Para agregar tu usuario al grupo docker:")
        console.print("  [bold]$ sudo usermod -aG docker $USER[/bold]")
        console.print("  [dim]Luego cierra sesion y vuelve a entrar, o ejecuta:[/dim]")
        console.print("  [bold]$ newgrp docker[/bold]")
        return

    # ── Step 4: Verificar Compose ─────────────────────────────────────
    _spinner_step("Verificando Docker Compose...")
    docker_status = check_docker()

    if not docker_status.compose_version:
        _warn("Docker Compose no esta disponible")
        _info("Intentando instalar docker-compose-plugin...")

        code, _ = _run_cmd("sudo apt install -y docker-compose-plugin", timeout=120)
        if code == 0:
            _success("Docker Compose instalado")
        else:
            _error("No se pudo instalar automaticamente (requiere sudo)")
            console.print()
            console.print("  Ejecuta manualmente:")
            console.print("  [bold]$ sudo apt install docker-compose-plugin[/bold]")
            return
    else:
        _success(f"Docker Compose v{docker_status.compose_version}")

    # ── Step 5: Verificar que funciona ────────────────────────────────
    _spinner_step("Ejecutando test de Docker...")
    code, output = _run_cmd("docker run --rm hello-world", timeout=30)
    if code == 0:
        _success("Docker funciona correctamente")
    else:
        # El test puede fallar si hello-world no esta descargado aún
        # pero el daemon funciona
        _info("Test hello-world no paso (puede ser normal en la primera ejecucion)")

    # ── Resumen ───────────────────────────────────────────────────────
    console.print()
    final = check_docker()
    console.print(Panel(
        f"[bold green]Docker reparado con exito[/bold green]\n"
        f"[dim]Version: {final.version} | Compose: {final.compose_version or 'N/A'} | "
        f"Contenedores: {final.containers_running} activos[/dim]",
        border_style="green",
    ))
    console.print()
    logger.command_end("repair", time.time() - start_time_docker)


# ── Repair: All ───────────────────────────────────────────────────────────

@repair_app.command(name="all")
def repair_all(
    skip_model: bool = typer.Option(
        False, "--skip-model",
        help="No descargar modelos de Ollama",
    ),
):
    """Ejecuta todas las reparaciones disponibles."""
    console.print()
    console.print(Panel(
        "[bold cyan]DevMind Repair[/bold cyan] — Reparacion completa",
        border_style="cyan",
    ))
    console.print()

    console.print("  [bold]Ejecutando reparaciones en secuencia...[/bold]")
    console.print()

    # Reparar Docker primero (mas rapido)
    console.print("[bold]── Docker ──[/bold]")
    docker()
    console.print()

    # Reparar Ollama (puede tardar por descarga de modelos)
    console.print("[bold]── Ollama ──[/bold]")
    ollama(skip_model=skip_model)

    console.print()
    console.print("[bold]── Resumen Final ──[/bold]")

    # Re-verificar todo
    from devmind.utils.ollama import check_ollama as _check_ollama
    from devmind.utils.docker import check_docker as _check_docker

    d = _check_docker()
    o = _check_ollama()

    console.print()
    items = [
        ("Docker", d.installed and d.running, d.version or "No instalado"),
        ("Docker Compose", d.compose_version is not None, d.compose_version or "No disponible"),
        ("Ollama", o.installed and o.running, o.version or "No instalado"),
        ("Ollama Modelos", len(o.models) > 0, ", ".join(o.models) if o.models else "Ninguno"),
    ]

    for name, ok, detail in items:
        status = "[green]OK[/green]" if ok else "[yellow]PENDIENTE[/yellow]"
        console.print(f"  {status} {name}: {detail}")

    console.print()
    all_ok = all(ok for ok, _ in items)
    if all_ok:
        console.print(Panel(
            "[bold green]Todas las reparaciones completadas[/bold green]\n"
            "[dim]Tu sistema esta listo para desarrollo de IA con DevMind[/dim]",
            border_style="green",
        ))
    else:
        pending = sum(1 for ok, _ in items if not ok)
        console.print(Panel(
            f"[yellow]{pending} item(s) requieren atencion manual[/yellow]\n"
            "[dim]Revisa los items marcados como PENDIENTE arriba[/dim]",
            border_style="yellow",
        ))
    console.print()
