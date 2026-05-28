"""
Comando: devmind serve
Levanta la API REST de DevMind con FastAPI + Uvicorn.

Uso:
  devmind serve                  Levanta en localhost:8080
  devmind serve --port 3000      Levanta en puerto 3000
  devmind serve --host 0.0.0.0   Escuchar en todas las interfaces
  devmind serve --reload         Auto-reload en desarrollo
"""

from __future__ import annotations

import typer
from rich.console import Console

console = Console()


def run_serve(
    port: int = 8080,
    host: str = "127.0.0.1",
    reload: bool = False,
):
    """Levanta la API REST de DevMind."""
    import uvicorn

    console.print()
    console.print("[bold cyan]DevMind API[/bold cyan] — Server v0.7.0")
    console.print()
    console.print(f"  [bold]Host:[/bold] {host}")
    console.print(f"  [bold]Port:[/bold] {port}")
    console.print(f"  [bold]Docs:[/bold] http://{host}:{port}/docs")
    console.print(f"  [bold]Redoc:[/bold] http://{host}:{port}/redoc")
    console.print()
    console.print("[dim]Endpoints disponibles:[/dim]")
    console.print("  GET  /api/health")
    console.print("  GET  /api/version")
    console.print("  GET  /api/doctor")
    console.print("  GET  /api/snapshot")
    console.print("  POST /api/benchmark/ollama")
    console.print("  GET  /api/setup/profiles")
    console.print("  POST /api/setup/{profile}")
    console.print("  GET  /api/history")
    console.print("  GET  /api/explain")
    console.print()
    console.print("[dim]Presiona Ctrl+C para detener.[/dim]")
    console.print()

    uvicorn.run(
        "devmind.api.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )
