"""devmind optimize -- CLI command for model/provider recommendation."""

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from devmind.services.optimize import run_optimize

console = Console()
optimize_app = typer.Typer(
    name="optimize",
    help="Recomienda modelo y proveedor segun tu hardware y presupuesto.",
)


@optimize_app.command()
def run(
    tps: int = typer.Option(10, "--tps", help="Tokens por segundo objetivo"),
    ram: int = typer.Option(8, "--ram", help="RAM disponible (GB)"),
    gpu: str = typer.Option("", "--gpu", help="Nombre del GPU (vacio = auto-detect)"),
    budget: float = typer.Option(50.0, "--budget", help="Presupuesto mensual (USD)"),
    use_case: str = typer.Option("general", "--use-case", help="Uso: general, code, creative, reasoning"),
):
    """Recomienda el mejor modelo y proveedor."""
    console.print("\n[bold cyan]DevMind Optimize[/bold cyan]  v0.9.0")
    console.print(f"  TPS:         {tps}")
    console.print(f"  RAM:         {ram} GB")
    gpu_label = gpu if gpu else "auto-detect"
    console.print(f"  GPU:         {gpu_label}")
    console.print(f"  Presupuesto: ${budget:.0f}/mes")
    console.print(f"  Uso:         {use_case}\n")

    with console.status("[bold green]Buscando la mejor opcion..."):
        result = run_optimize(
            tps=tps,
            ram=ram,
            gpu=gpu or None,
            budget=budget,
            use_case=use_case,
        )

    # -- Tabla de recomendaciones --
    table = Table(title="Recomendaciones", show_lines=True)
    table.add_column("#", style="bold", justify="center")
    table.add_column("Proveedor", style="bold")
    table.add_column("Modelo")
    table.add_column("Precision", justify="center")
    table.add_column("TPS", justify="right")
    table.add_column("Costo/mes", justify="right", style="cyan")
    table.add_column("Calidad", justify="center")

    recs = result.get("recommendations", [])
    for i, rec in enumerate(recs, 1):
        table.add_row(
            str(i),
            rec.get("provider", ""),
            rec.get("model", ""),
            rec.get("precision", ""),
            str(rec.get("tps", 0)),
            f"${rec.get('monthly_cost', 0):.2f}",
            rec.get("quality_score", ""),
        )

    console.print(table)

    # -- Panel de opcion local --
    local = result.get("local_option")
    if local:
        parts = []
        parts.append("Modelo:     " + str(local.get("model", "N/A")))
        parts.append("Quant:      " + str(local.get("quantization", "N/A")))
        parts.append("RAM req:    " + f"{local.get('ram_required', 0):.1f} GB")
        parts.append("TPS est:    " + f"{local.get('estimated_tps', 0):.1f}")
        parts.append("Calidad:    " + str(local.get("quality_score", "N/A")))
        panel_text = Text()
        for i, part in enumerate(parts):
            if i > 0:
                panel_text.append("\n")
            panel_text.append(part)
        console.print(Panel(panel_text, title="Opcion Local (tu hardware)", border_style="bold green"))

    # -- Mejor opcion --
    best = result.get("best_pick")
    if best:
        provider = best.get("provider", "")
        model = best.get("model", "")
        console.print(f"\n[bold green]Mejor opcion: {provider} / {model}[/bold green]")
