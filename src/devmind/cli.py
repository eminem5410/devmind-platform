"""
DevMind Platform CLI — Punto de entrada principal.

Comandos:
  devmind doctor          Diagnostica el sistema con severidad y recomendaciones
  devmind doctor --json   Output estructurado para APIs/GUIs/telemetry
  devmind gpu             Verifica GPUs, drivers CUDA y Vulkan
  devmind init            Inicializa un proyecto de IA con estructura estandar
  devmind repair          Repara problemas detectados automaticamente
  devmind setup           Configura un ambiente completo de desarrollo AI
"""

import typer
from rich.console import Console

app = typer.Typer(
    name="devmind",
    help="DevMind Platform — Herramientas CLI para desarrollo de IA en Linux",
    no_args_is_help=True,
    add_completion=False,
)

console = Console()


@app.command()
def doctor(
    json_output: bool = typer.Option(
        False, "--json", "-j",
        help="Output como JSON estructurado (para APIs, GUIs, telemetry)",
    ),
    compact: bool = typer.Option(
        False, "--compact", "-c",
        help="Output compacto de una pantalla (para CI y scripting)",
    ),
):
    """Diagnostica el sistema, detecta problemas y genera recomendaciones."""
    from devmind.commands.doctor import run_doctor
    run_doctor(json_output=json_output, compact=compact)


@app.command()
def gpu():
    """Verifica GPUs, drivers CUDA y Vulkan."""
    from devmind.commands.gpu_check import run_gpu_check
    run_gpu_check()


@app.command()
def init():
    """Inicializa un proyecto de IA con estructura estandar."""
    from devmind.commands.init_cmd import run_init
    run_init()


@app.command(name="setup")
def setup():
    """Configura un ambiente completo de desarrollo AI."""
    from devmind.commands.setup import run_setup
    run_setup()


# ── Repair: subcommand group ──────────────────────────────────────────────
# Importamos la sub-app de repair y la registramos como subgrupo
from devmind.commands.repair import repair_app

app.add_typer(repair_app, name="repair")


# ── Callback principal (sin subcomando) ──────────────────────────────────

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """DevMind Platform — Herramientas CLI para desarrollo de IA en Linux."""
    if ctx.invoked_subcommand is None:
        console.print()
        console.print("[bold cyan]DevMind Platform[/bold cyan] v0.2.0")
        console.print("[dim]Plataforma integral para desarrollo de IA en Linux[/dim]")
        console.print()
        console.print("Comandos disponibles:")
        console.print()
        console.print("  [bold]devmind doctor[/bold]       Diagnostica el sistema completo")
        console.print("  [bold]devmind doctor --json[/bold]  Output JSON estructurado")
        console.print("  [bold]devmind doctor -c[/bold]     Output compacto (CI/scripting)")
        console.print("  [bold]devmind gpu[/bold]          Verifica GPUs y drivers")
        console.print("  [bold]devmind init[/bold]         Inicializa un proyecto de IA")
        console.print("  [bold]devmind repair[/bold]       Repara problemas automaticamente")
        console.print("  [bold]  repair ollama[/bold]      Instala/inicia Ollama + modelos")
        console.print("  [bold]  repair docker[/bold]      Verifica/instala Docker + Compose")
        console.print("  [bold]  repair all[/bold]         Repara todo automaticamente")
        console.print("  [bold]devmind setup[/bold]        Configura ambiente AI completo")
        console.print()
        console.print("[dim]Ejecuta 'devmind <comando> --help' para mas detalles.[/dim]")
        console.print()


if __name__ == "__main__":
    app()
