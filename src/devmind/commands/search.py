# devmind/commands/search.py
"""Full-Text Search in Chat History — v0.13.0

Commands:
  devmind search <query>               Search in chat history (FTS5)
  devmind search <query> --export md   Export results as Markdown
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel

from devmind.db.manager import search_chat_messages

console = Console()


def run_search(
    query: str,
    provider: Optional[str] = None,
    role: Optional[str] = None,
    limit: int = 20,
    export_format: Optional[str] = None,
    output_file: Optional[str] = None,
) -> None:
    """Search chat history using FTS5 full-text search."""
    if not query.strip():
        console.print("[yellow]Usage: devmind search <query>[/yellow]")
        return

    results = search_chat_messages(
        query=query.strip(),
        limit=limit,
        provider=provider,
        role=role,
    )

    if not results:
        console.print(f"[dim]No results for: {query}[/dim]")
        return

    if export_format:
        _export_results(results, query, export_format, output_file)
        return

    console.print()
    console.print(Panel(
        f"[bold cyan]Search Results[/bold cyan] — "
        f"[dim]{len(results)} result(s) for: {query}[/dim]",
        border_style="cyan",
    ))
    console.print()

    for i, r in enumerate(results, 1):
        _print_result(i, r)

    console.print(f"[dim]Showing {len(results)} result(s)[/dim]")


def _print_result(idx: int, r: dict) -> None:
    """Print a single search result."""
    role = r.get("role", "?")
    content = r.get("content", "")[:200]
    prov = r.get("provider", "?")
    model = r.get("model", "?")
    title = r.get("session_title", "") or r.get("title", "")
    ts = str(r.get("timestamp", ""))[:19]
    tokens = r.get("tokens", 0)
    sid = r.get("session_id", "?")

    role_style = "bold cyan" if role == "user" else "bold green"
    console.print(f"  [bold]#{idx}[/bold] [dim]Session {sid}[/dim] — {title}")
    console.print(f"  [{role_style}]{role}[/{role_style}] | {prov}/{model} | {tokens} tok | {ts}")
    if len(content) >= 200:
        console.print(f"  [dim]{content}...[/dim]")
    else:
        console.print(f"  [dim]{content}[/dim]")
    console.print()


def _export_results(
    results: list[dict],
    query: str,
    fmt: str,
    output_file: Optional[str] = None,
) -> None:
    """Export search results to Markdown."""
    lines = []
    lines.append(f"# Search Results: {query}")
    lines.append(f"Found {len(results)} result(s)")
    lines.append("")

    for i, r in enumerate(results, 1):
        role = r.get("role", "?")
        content = r.get("content", "")
        prov = r.get("provider", "?")
        model = r.get("model", "?")
        title = r.get("session_title", "") or r.get("title", "")
        ts = str(r.get("timestamp", ""))[:19]
        sid = r.get("session_id", "?")

        lines.append(f"## #{i} — {title}")
        lines.append(f"- **Session:** #{sid}")
        lines.append(f"- **Role:** {role} | **Model:** {prov}/{model}")
        lines.append(f"- **Date:** {ts}")
        lines.append("")
        lines.append(f"> {content}")
        lines.append("")

    md_content = "\n".join(lines)

    if output_file:
        Path(output_file).write_text(md_content, encoding="utf-8")
        console.print(f"[green]Exported to: {output_file}[/green]")
    else:
        console.print(md_content)
