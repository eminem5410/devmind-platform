"""devmind export — Export chat sessions to Markdown or JSON."""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console

from devmind.db.manager import (
    get_chat_messages,
    get_chat_session,
    list_chat_sessions,
)

console = Console()
export_app = typer.Typer(help="Export chat sessions to Markdown or JSON")


def _session_to_markdown(session_id: int) -> str:
    """Convert a session to Markdown."""
    session = get_chat_session(session_id)
    if not session:
        return f"# Session #{session_id}\n\nSession not found.\n"

    messages = get_chat_messages(session_id, limit=10000)
    title = session.get("title", f"Session #{session_id}")

    lines = [
        f"# {title}",
        "",
        f"- **Provider:** {session.get('provider', 'N/A')}",
        f"- **Model:** {session.get('model', 'N/A')}",
        f"- **Created:** {session.get('created_at', 'N/A')}",
        f"- **Messages:** {len(messages)}",
        "",
        "---",
        "",
    ]

    for msg in messages:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        tokens = msg.get("tokens", 0)
        timestamp = msg.get("timestamp", "")

        if role == "user":
            lines.append("## User")
        elif role == "assistant":
            lines.append("## Assistant")
        else:
            lines.append(f"## {role.title()}")

        meta = []
        if timestamp:
            meta.append(timestamp)
        if tokens:
            meta.append(f"{tokens} tokens")
        if meta:
            lines.append(f"*{' | '.join(meta)}*")
        lines.append("")
        lines.append(content)
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def _session_to_json(session_id: int) -> dict:
    """Convert a session to JSON dict."""
    session = get_chat_session(session_id)
    if not session:
        return {"error": "Session not found", "session_id": session_id}

    messages = get_chat_messages(session_id, limit=10000)
    return {
        "session_id": session_id,
        "title": session.get("title", ""),
        "provider": session.get("provider", ""),
        "model": session.get("model", ""),
        "created_at": session.get("created_at", ""),
        "updated_at": session.get("updated_at", ""),
        "messages": [
            {
                "role": m.get("role", ""),
                "content": m.get("content", ""),
                "tokens": m.get("tokens", 0),
                "timestamp": m.get("timestamp", ""),
            }
            for m in messages
        ],
    }


@export_app.callback(invoke_without_command=True)
def export(
    session: int = typer.Option(None, "--session", "-s", help="Session ID to export"),
    all_sessions: bool = typer.Option(False, "--all", "-a", help="Export all sessions"),
    provider: str = typer.Option(None, "--provider", "-p", help="Filter by provider"),
    model: str = typer.Option(None, "--model", "-m", help="Filter by model"),
    format: str = typer.Option("md", "--format", "-f", help="Output format: md or json"),
    output: str = typer.Option(None, "--output", "-o", help="Output file path"),
) -> None:
    """Export chat sessions to Markdown or JSON."""
    if format not in ("md", "json"):
        console.print("[red]Invalid format:[/] use 'md' or 'json'")
        raise typer.Exit(1)

    sessions = list_chat_sessions(limit=1000)

    if session:
        target = [s for s in sessions if s.get("id") == session]
        if not target:
            console.print(f"[red]Session #{session} not found.[/]")
            raise typer.Exit(1)
        sessions = target

    if provider:
        sessions = [s for s in sessions if s.get("provider") == provider]

    if model:
        sessions = [s for s in sessions if s.get("model") == model]

    if not all_sessions and not session and not provider and not model:
        console.print("[yellow]No filter specified.[/] Use --session, --all, --provider, or --model.")
        console.print("\n[dim]Available sessions:[/]")
        for s in sessions[:5]:
            sid = s.get("id", "?")
            stitle = s.get("title", "untitled")[:50]
            sprov = s.get("provider", "?")
            console.print(f"  [cyan]#{sid}[/] {stitle} [dim]({sprov})[/]")
        if len(sessions) > 5:
            console.print(f"  [dim]...and {len(sessions)-5} more[/]")
        raise typer.Exit(1)

    if not sessions:
        console.print("[yellow]No sessions match the given filters.[/]")
        raise typer.Exit(0)

    # Build content
    if len(sessions) == 1:
        sid = sessions[0]["id"]
        if format == "md":
            content = _session_to_markdown(sid)
        else:
            content = json.dumps(_session_to_json(sid), indent=2, ensure_ascii=False)
        default_name = f"session_{sid}.{format}"
    else:
        if format == "md":
            parts = [_session_to_markdown(s["id"]) for s in sessions]
            content = "\n\n".join(parts)
        else:
            data = [_session_to_json(s["id"]) for s in sessions]
            content = json.dumps(data, indent=2, ensure_ascii=False)
        default_name = f"export_{len(sessions)}_sessions.{format}"

    out_path = Path(output) if output else Path(default_name)
    out_path.write_text(content, encoding="utf-8")
    console.print(f"[green]+[/] Exported {len(sessions)} session(s) to [bold]{out_path}[/]")
