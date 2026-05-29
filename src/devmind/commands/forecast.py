"""devmind forecast -- CLI command for cost projection."""

from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
import typer

from devmind.services.forecast import run_forecast

console = Console()
forecast_app = typer.Typer(
    name="forecast",
    help="Proyecta costos de API vs inferencia local a 12 meses.",
)


def _fmt(v: float) -> str:
    if v >= 1_000_000:
        return f"${v / 1_000_000:.1f}M"
    if v >= 1_000:
        return f"${v / 1_000:.1f}K"
    return f"${v:.2f}"


@forecast_app.command()
def run(
    tps: int = typer.Option(10, "--tps", help="Tokens por segundo objetivo"),
    daily_tokens: int = typer.Option(100_000, "--daily-tokens", help="Tokens promedio diarios"),
    growth: float = typer.Option(0.1, "--growth", help="Crecimiento mensual (decimal, ej 0.1 = 10%)"),
    vs: str = typer.Option("all", "--vs", help="Comparar contra: api, local, all"),
    export: Path = typer.Option(None, "--export", help="Exportar a CSV"),
):
    """Proyecta costos API vs Local a 12 meses."""
    console.print("\n[bold cyan]DevMind Forecast[/bold cyan]  v0.12.0")
    console.print(f"  TPS objetivo:    {tps}")
    console.print(f"  Tokens/dia:      {daily_tokens:,}")
    console.print(f"  Crecimiento:     {growth * 100:.0f}% mensual\n")

    with console.status("[bold green]Calculando proyeccion..."):
        result = run_forecast(tps=tps, daily_tokens=daily_tokens, growth_rate=growth)

    # -- Tabla de proyecciones --
    table = Table(title="Proyeccion de Costos", show_lines=True)
    table.add_column("Mes", style="bold", justify="right")
    table.add_column("API Costo", justify="right", style="red")
    table.add_column("Local Costo", justify="right", style="green")
    table.add_column("Ahorro Local", justify="right", style="cyan")

    projections = result.get("projections", [])
    for p in projections:
        month = p.get("month", 0)
        api_cost = p.get("api_cost", 0)
        local_cost = p.get("local_cost", 0)
        saving = api_cost - local_cost
        saving_pct = (saving / api_cost * 100) if api_cost > 0 else 0
        table.add_row(
            str(month),
            _fmt(api_cost),
            _fmt(local_cost),
            f"{_fmt(saving)} ({saving_pct:.0f}%)",
        )

    if vs in ("all", "api"):
        console.print(table)

    # -- Panel de crossover --
    crossover = result.get("crossover")
    if crossover and crossover.get("month"):
        co_month = crossover["month"]
        co_api = crossover.get("api_total", 0)
        co_local = crossover.get("local_total", 0)
        co_hw = crossover.get("hardware_cost", 0)
        title = "Break-even: Mes " + str(co_month)
        parts = []
        parts.append("API acumulado:   " + _fmt(co_api))
        parts.append("Local acumulado: " + _fmt(co_local))
        parts.append("  (Hardware:     " + _fmt(co_hw) + ")")
        parts.append("A partir del mes " + str(co_month) + ", inferencia local es mas economica.")
        panel_text = Text()
        for i, part in enumerate(parts):
            if i > 0:
                panel_text.append("\n")
            panel_text.append(part)
        console.print(Panel(panel_text, title=title, border_style="bold yellow"))
    else:
        msg = Text("No se alcanza break-even en 60 meses con los parametros actuales.")
        msg.append("\nLa API es mas economica a largo plazo.")
        console.print(Panel(msg, title="Break-even", border_style="dim"))

    # -- CSV export --
    if export:
        rows = []
        rows.append("month,tokens,api_cost,local_cost,saving")
        for p in projections:
            m = p.get("month", 0)
            t = p.get("tokens", 0)
            ac = p.get("api_cost", 0)
            lc = p.get("local_cost", 0)
            rows.append(f"{m},{t},{ac:.2f},{lc:.2f},{ac - lc:.2f}")
        export.write_text("\n".join(rows))
        console.print(f"\n[green]Exportado a {export}[/green]")
