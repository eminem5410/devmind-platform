# devmind/commands/chat.py
"""Interactive multi-provider LLM chat — v0.12.0

Commands:
  devmind chat               Start interactive chat session
  devmind chat --model X     Use specific model
  devmind chat --provider X  Use specific provider
  devmind chat --session N   Resume a previous session
  devmind chat --list       List recent chat sessions

Slash commands (inside chat):
  /model <name>    Switch model
  /provider <name> Switch provider
  /clear           Clear conversation history
  /sessions        List recent sessions
  /info            Show current session info
  /help            Show available commands
  /quit            Exit chat
"""

from __future__ import annotations

import sys
from datetime import datetime
from typing import Optional

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from devmind.config.settings import (
    get_default_model,
    get_default_provider,
    load_config,
    PROVIDERS,
)
from devmind.db.manager import (
    create_chat_session,
    get_chat_session,
    list_chat_sessions,
    update_chat_session,
    delete_chat_session,
    save_chat_message,
    get_chat_messages,
    get_chat_message_count,
)
from devmind.services.chat import ChatMessage, stream_chat

console = Console()
BT = chr(96) * 3
NL = chr(10)

def _print_welcome(provider: str, model: str, session_id: int) -> None:
    """Print the chat welcome banner."""
    console.print()
    welcome_lines = [
        "[bold cyan]DevMind Chat[/bold cyan] — [dim]v0.12.0[/dim]",
        "",
        "[bold]Provider:[/bold] " + provider,
        "[bold]Model:[/bold] " + model,
        "[bold]Session:[/bold] #" + str(session_id),
        "",
        "[dim]Escribe tu mensaje o /help para comandos[/dim]",
        "[dim]Presiona Ctrl+C o /quit para salir[/dim]",
    ]
    console.print(Panel(NL.join(welcome_lines), border_style="cyan"))
    console.print()

def _print_help() -> None:
    """Print available slash commands."""
    help_lines = [
        "[bold cyan]Comandos disponibles:[/bold cyan]",
        "",
        "  [bold]/model <nombre>[/bold]    Cambiar modelo (ej: /model llama3.2:3b)",
        "  [bold]/provider <nombre>[/bold] Cambiar provider (ollama, groq, together, openrouter, fireworks)",
        "  [bold]/clear[/bold]             Limpiar historial de la conversacion",
        "  [bold]/sessions[/bold]          Listar sesiones recientes",
        "  [bold]/info[/bold]              Mostrar info de la sesion actual",
        "  [bold]/help[/bold]              Mostrar esta ayuda",
        "  [bold]/quit[/bold]              Salir del chat",
    ]
    console.print(Panel(NL.join(help_lines), border_style="cyan"))

def _print_sessions(sessions: list[dict]) -> None:
    """Print chat sessions table."""
    if not sessions:
        console.print("[dim]No hay sesiones previas.[/dim]")
        return

    table = Table(title="Sesiones recientes", show_lines=False)
    table.add_column("ID", style="bold cyan", width=6)
    table.add_column("Provider", width=12)
    table.add_column("Model", width=25)
    table.add_column("Title", width=30)
    table.add_column("Updated", width=20, style="dim")

    for s in sessions:
        table.add_row(
            str(s["id"]),
            s.get("provider", ""),
            s.get("model", "")[:25],
            s.get("title", "")[:30] or "[dim]sin titulo[/dim]",
            s.get("updated_at", "")[:19],
        )

    console.print(table)

def _print_info(session: dict, provider: str, model: str, msg_count: int) -> None:
    """Print current session info."""
    info_lines = [
        "[bold cyan]Info de sesion[/bold cyan]",
        "",
        "[bold]ID:[/bold] #" + str(session.get("id", "?")),
        '[bold]Session:[/bold] ' + session.get("session_id", "?"),
        "[bold]Provider:[/bold] " + provider,
        "[bold]Model:[/bold] " + model,
        "[bold]Messages:[/bold] " + str(msg_count),
        '[bold]Title:[/bold] ' + (session.get("title", "") or "[dim]sin titulo[/dim]"),
        '[bold]Created:[/bold] ' + (session.get("created_at", "")[:19] or "?"),
        '[bold]Updated:[/bold] ' + (session.get("updated_at", "")[:19] or "?"),
    ]
    console.print(Panel(NL.join(info_lines), border_style="cyan"))

def _stream_response(provider: str, model: str, messages: list[ChatMessage]) -> tuple[str, int]:
    """Stream a response to the console and return (content, tokens)."""
    content_parts = []
    total_tokens = 0

    console.print()
    console.print("[bold green]Assistant:[/bold green] ", end="")

    for chunk in stream_chat(provider, model, messages):
        if chunk.error:
            console.print(f"\n[bold red]Error:[/bold red] {chunk.error}")
            return chunk.error, 0

        if chunk.token:
            content_parts.append(chunk.token)
            console.print(chunk.token, end="", highlight=False)
            sys.stdout.flush()
            total_tokens = chunk.tokens_so_far

        if chunk.done:
            total_tokens = chunk.tokens_so_far

    console.print()
    console.print()
    return "".join(content_parts), total_tokens

def _auto_title(messages: list[ChatMessage]) -> str:
    """Generate a title from the first user message."""
    for m in messages:
        if m.role == "user":
            first_msg = m.content.strip()
            if len(first_msg) > 40:
                return first_msg[:40] + "..."
            return first_msg
    return ""

def run_chat(
    model: Optional[str] = None,
    provider: Optional[str] = None,
    session: Optional[int] = None,
    list_sessions: bool = False,
    prompt_text: Optional[str] = None,
) -> None:
    """Run the interactive chat session."""

    # --list: show sessions and exit
    if list_sessions:
        sessions = list_chat_sessions(limit=20)
        _print_sessions(sessions)
        return

    # Determine provider and model
    current_provider = provider or get_default_provider()
    current_model = model or get_default_model()

    # Resume or create session
    if session is not None:
        existing = get_chat_session(session)
        if existing:
            db_session = existing
            current_provider = provider or db_session.get("provider", current_provider)
            current_model = model or db_session.get("model", current_model)
        else:
            console.print(f"[red]Sesion #{session} no encontrada. Creando nueva sesion.[/red]")
            db_session = None
    else:
        db_session = None

    if db_session is None:
        session_id = create_chat_session(current_provider, current_model)
    else:
        session_id = db_session["id"]

    # Load existing messages
    existing_messages = get_chat_messages(session_id, limit=1000)
    messages: list[ChatMessage] = [
        ChatMessage(role=m["role"], content=m["content"], tokens=m.get("tokens", 0))
        for m in existing_messages
    ]

    # Single prompt mode (non-interactive)
    if prompt_text:
        messages.append(ChatMessage(role="user", content=prompt_text))
        save_chat_message(session_id, "user", prompt_text)
        content, tokens = _stream_response(current_provider, current_model, messages)
        if content:
            messages.append(ChatMessage(role="assistant", content=content, tokens=tokens))
            save_chat_message(session_id, "assistant", content, tokens)
        if not existing_messages and not db_session:
            title = _auto_title(messages)
            update_chat_session(session_id, title=title)
        return

    # Interactive mode
    _print_welcome(current_provider, current_model, session_id)

    # Show existing messages if resuming
    if existing_messages:
        console.print(f"[dim]Resumida sesion con {len(existing_messages)} mensajes previos[/dim]")
        console.print()
        for m in existing_messages[-6:]:
            if m["role"] == "user":
                console.print(f'[bold cyan]You:[/bold cyan] {m["content"][:100]}')
            elif m["role"] == "assistant":
                console.print(f'[bold green]AI:[/bold green] {m["content"][:100]}...')
        console.print()

    try:
        while True:
            try:
                user_input = typer.prompt(
                    "\n[bold cyan]You[/bold cyan]",
                    default="",
                    show_default=False,
                )
            except (KeyboardInterrupt, EOFError):
                console.print("\n[dim]Usa /quit para salir[/dim]")
                continue

            user_input = user_input.strip()
            if not user_input:
                continue

            # Slash commands
            if user_input.startswith("/"):
                cmd = user_input.lower().split()
                cmd_name = cmd[0]

                if cmd_name in ("/quit", "/exit", "/q"):
                    console.print("[dim]Sesion finalizada.[/dim]")
                    return

                elif cmd_name in ("/help", "/h"):
                    _print_help()
                    continue

                elif cmd_name in ("/model", "/m"):
                    if len(cmd) < 2:
                        console.print("[yellow]Uso: /model <nombre>[/yellow]")
                        console.print(f"[dim]Modelo actual: {current_model}[/dim]")
                        continue
                    current_model = cmd[1]
                    update_chat_session(session_id, model=current_model)
                    console.print(f"[green]Modelo cambiado a: {current_model}[/green]")
                    continue

                elif cmd_name in ("/provider", "/p"):
                    if len(cmd) < 2:
                        console.print("[yellow]Uso: /provider <nombre>[/yellow]")
                        console.print(f"[dim]Provider actual: {current_provider}[/dim]")
                        console.print(f"[dim]Disponibles: {chr(39).join(PROVIDERS)}[/dim]")
                        continue
                    new_provider = cmd[1].lower()
                    if new_provider not in PROVIDERS:
                        console.print(f"[red]Provider desconocido: {new_provider}[/red]")
                        console.print(f"[dim]Disponibles: {chr(39).join(PROVIDERS)}[/dim]")
                        continue
                    current_provider = new_provider
                    console.print(f"[green]Provider cambiado a: {current_provider}[/green]")
                    continue

                elif cmd_name in ("/clear", "/c"):
                    messages.clear()
                    console.print("[green]Historial limpiado.[/green]")
                    continue

                elif cmd_name in ("/sessions", "/s"):
                    sessions = list_chat_sessions(limit=10)
                    _print_sessions(sessions)
                    continue

                elif cmd_name in ("/info", "/i"):
                    s = get_chat_session(session_id) or {}
                    mc = get_chat_message_count(session_id)
                    _print_info(s, current_provider, current_model, mc)
                    continue

                else:
                    console.print(f"[yellow]Comando desconocido: {cmd_name}[/yellow]")
                    console.print("[dim]Escribe /help para ver los comandos[/dim]")
                    continue

            # Regular message
            messages.append(ChatMessage(role="user", content=user_input))
            save_chat_message(session_id, "user", user_input)

            content, tokens = _stream_response(current_provider, current_model, messages)

            if content and not content.startswith("Error:"):
                messages.append(ChatMessage(role="assistant", content=content, tokens=tokens))
                save_chat_message(session_id, "assistant", content, tokens)

                # Auto-title on first exchange
                if len(messages) == 2:
                    title = _auto_title(messages)
                    update_chat_session(session_id, title=title)
            elif content and content.startswith("Error:"):
                console.print("[dim]Prueba con /provider o /model para cambiar.[/dim]")

    except KeyboardInterrupt:
        console.print("\n[dim]Sesion finalizada.[/dim]")
