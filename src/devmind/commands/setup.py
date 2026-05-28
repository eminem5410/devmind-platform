"""
Comando: devmind setup
Configura un ambiente completo de desarrollo AI.

NOTA: Este comando sera implementado completamente en la proxima fase.
Actualmente muestra un placeholder informativo.
"""

from rich.console import Console
from rich.panel import Panel

console = Console()


def run_setup() -> None:
    """Muestra informacion sobre setup (placeholder para v0.3.0)."""
    console.print()
    console.print(Panel(
        "[bold cyan]DevMind Setup[/bold cyan] — Configuracion de ambiente AI",
        border_style="cyan",
    ))
    console.print()
    console.print("  [yellow]Este comando estara disponible en DevMind v0.3.0[/yellow]")
    console.print()
    console.print("  Mientras tanto, podes usar:")
    console.print("  [bold]devmind repair all[/bold]   para configurar Ollama + Docker")
    console.print("  [bold]devmind init[/bold]         para crear un proyecto de IA")
    console.print()
    console.print("  [dim]El setup completo incluira: stacks Docker, templates,[/dim]")
    console.print("  [dim]Jupyter, bases de datos vectoriales, y mas.[/dim]")
    console.print()
