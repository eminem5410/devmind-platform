# devmind/commands/stats.py
"""Chat Analytics Dashboard — v0.13.0

Commands:
  devmind stats              Show full analytics dashboard
  devmind stats --compact    One-line summary for scripts
"""

from __future__ import annotations

from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from devmind.db.manager import get_chat_stats, get_daily_activity

console = Console()


def run_stats(compact: bool = False, days: int = 7) -> None:
    """Display chat analytics dashboard."""
    stats = get_chat_stats()
    activity = get_daily_activity(days)

    if compact:
        _print_compact(stats)
        return

    _print_dashboard(stats, activity, days)


def _print_compact(stats: dict) -> None:
    """One-line compact output for scripts."""
    tokens = stats.get("total_tokens", 0)
    sessions = stats.get("total_sessions", 0)
    messages = stats.get("total_messages", 0)
    top = stats.get("top_models", [])
    top_model = top[0]["model"] if top else "N/A"
    providers = stats.get("provider_breakdown", {})
    top_prov = list(providers.keys())[0] if providers else "N/A"
    avg_tok = stats.get("avg_response_tokens", 0)

    console.print(
        f"Sessions: {sessions} | Messages: {messages} | Tokens: {tokens:,}"
    )
    console.print(
        f"Top model: {top_model} | Provider: {top_prov} | Avg resp: {avg_tok} tok"
    )


def _print_dashboard(stats: dict, activity: list, days: int) -> None:
    """Full Rich dashboard."""
    console.print()
    console.print(Panel(
        "[bold cyan]DevMind Analytics[/bold cyan] — [dim]v0.13.0[/dim]",
        border_style="cyan",
    ))
    console.print()

    console.print("[bold]Overview[/bold]")
    tokens = stats.get("total_tokens", 0)
    sessions = stats.get("total_sessions", 0)
    messages = stats.get("total_messages", 0)
    avg_tok = stats.get("avg_response_tokens", 0)
    console.print(f"  [bold]Tokens:[/bold]        {tokens:,}")
    console.print(f"  [bold]Sessions:[/bold]      {sessions}")
    console.print(f"  [bold]Messages:[/bold]      {messages}")
    console.print(f"  [bold]Avg response:[/bold]  {avg_tok} tok")
    console.print()

    providers = stats.get("provider_breakdown", {})
    if providers:
        console.print("[bold]Providers[/bold]")
        for prov, count in providers.items():
            console.print(f"  [cyan]{prov:12s}[/cyan] {count} sessions")
        console.print()

    top = stats.get("top_models", [])
    if top:
        console.print("[bold]Top Models[/bold]")
        for m in top:
            console.print(f'  [green]{m["model"]:25s}[/green] {m["sessions"]} sessions')
        console.print()

    console.print(f"[bold]Activity (last {days} days)[/bold]")
    s7 = stats.get("sessions_7d", 0)
    m7 = stats.get("messages_7d", 0)
    t7 = stats.get("tokens_7d", 0)
    console.print(f"  Sessions: {s7} | Messages: {m7} | Tokens: {t7:,}")
    console.print()

    if activity:
        table = Table(title=f"Daily Activity (last {days} days)")
        table.add_column("Date", width=14)
        table.add_column("Messages", justify="right", width=10)
        table.add_column("Tokens", justify="right", width=12)
        table.add_column("Sessions", justify="right", width=10)
        for d in activity:
            table.add_row(
                str(d.get("date", "?")),
                str(d.get("messages", 0)),
                f"{d.get('tokens', 0):,}",
                str(d.get("sessions", 0)),
            )
        console.print(table)
        console.print()

    latest = stats.get("latest_session")
    if latest:
        console.print("[bold]Latest Session[/bold]")
        sid = latest.get("session_id", "?")
        title = latest.get("title", "?")
        prov = latest.get("provider", "?")
        model = latest.get("model", "?")
        console.print(f"  [dim]#{sid}[/dim] {title}")
        console.print(f"  {prov} / {model}")
        console.print()
