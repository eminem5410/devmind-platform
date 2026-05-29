"""devmind config — View, edit, validate and reset DevMind configuration."""

from __future__ import annotations

import shutil
import subprocess
import urllib.request
import urllib.error

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from devmind.config.settings import (
    CONFIG_PATH,
    DEFAULT_CONFIG,
    PROVIDERS,
    load_config,
    save_config,
    set_api_key,
    set_default_model,
    set_default_provider,
    get_api_key,
)

console = Console()
config_app = typer.Typer(help="Manage DevMind configuration")


def _mask_key(key: str) -> str:
    """Mask API key for display."""
    if not key:
        return "[dim]not set[/]"
    if len(key) <= 8:
        return "****"
    return key[:4] + "..." + key[-4:]


@config_app.command("show")
def config_show() -> None:
    """Show current configuration (API keys masked)."""
    config = load_config()

    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("Key", style="cyan", width=20)
    table.add_column("Value")
    table.add_row("File", str(CONFIG_PATH))
    table.add_row("Default Provider", f"[bold]{config.get('default_provider', 'ollama')}[/]")
    table.add_row("Default Model", f"[bold]{config.get('default_model', 'phi3:mini')}[/]")

    console.print(Panel(table, title="[bold]DevMind Config[/]", border_style="cyan"))

    prov_table = Table(title="Providers", border_style="cyan")
    prov_table.add_column("Provider", style="bold cyan", width=12)
    prov_table.add_column("Base URL")
    prov_table.add_column("API Key", width=18)

    for prov in PROVIDERS:
        pdata = config.get("providers", {}).get(prov, {})
        key = pdata.get("api_key", "")
        url = pdata.get("base_url", "")
        marker = ""
        if prov == config.get("default_provider"):
            marker = " [dim](default)[/]"
        prov_table.add_row(f"{prov}{marker}", url, _mask_key(key))

    console.print(prov_table)

    aliases = config.get("aliases", {})
    if aliases:
        alias_table = Table(title="Aliases", border_style="cyan")
        alias_table.add_column("Alias", style="bold cyan")
        alias_table.add_column("Model")
        for alias, model in aliases.items():
            alias_table.add_row(alias, model)
        console.print(alias_table)


@config_app.command("set")
def config_set(
    key: str = typer.Argument(help="Key: provider, model, <provider>_api_key, base_url_<provider>"),
    value: str = typer.Argument(help="Value to set"),
) -> None:
    """Set a configuration value."""
    config = load_config()

    if key == "provider":
        if value not in PROVIDERS:
            console.print(f"[red]Invalid provider:[/] {value}. Valid: {', '.join(PROVIDERS)}")
            raise typer.Exit(1)
        set_default_provider(value)
        console.print(f"[green]+[/] Default provider set to [bold]{value}[/]")

    elif key == "model":
        set_default_model(value)
        console.print(f"[green]+[/] Default model set to [bold]{value}[/]")

    elif key.endswith("_api_key"):
        provider = key[:-8]
        if provider not in PROVIDERS:
            console.print(f"[red]Unknown provider:[/] {provider}. Valid: {', '.join(PROVIDERS)}")
            raise typer.Exit(1)
        set_api_key(provider, value)
        console.print(f"[green]+[/] {provider} API key set ({len(value)} chars)")

    elif key.startswith("base_url_"):
        provider = key[9:]
        if provider not in PROVIDERS:
            console.print(f"[red]Unknown provider:[/] {provider}. Valid: {', '.join(PROVIDERS)}")
            raise typer.Exit(1)
        if "providers" not in config:
            config["providers"] = {}
        if provider not in config["providers"]:
            config["providers"][provider] = DEFAULT_CONFIG["providers"][provider]
        config["providers"][provider]["base_url"] = value
        save_config(config)
        console.print(f"[green]+[/] {provider} base URL set to [bold]{value}[/]")

    else:
        console.print(f"[red]Unknown key:[/] {key}")
        console.print("[dim]Valid keys: provider, model, <provider>_api_key, base_url_<provider>[/]")
        raise typer.Exit(1)


@config_app.command("reset")
def config_reset(
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
) -> None:
    """Reset configuration to defaults (deletes API keys)."""
    if not yes:
        confirm = typer.confirm("This will delete all API keys and settings. Continue?")
        if not confirm:
            raise typer.Exit(0)
    save_config(DEFAULT_CONFIG)
    console.print("[green]+[/] Configuration reset to defaults")


@config_app.command("validate")
def config_validate() -> None:
    """Validate configuration: check services and API keys."""
    results = []

    # Ollama
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags", method="GET")
        resp = urllib.request.urlopen(req, timeout=3)
        data = __import__("json").loads(resp.read())
        models = [m.get("name", "") for m in data.get("models", [])]
        model_str = ", ".join(models[:3])
        if len(models) > 3:
            model_str += f" (+{len(models)-3} more)"
        results.append(("Ollama", f"[green]Connected[/]  {model_str}", True))
    except Exception:
        results.append(("Ollama", "[red]Not running[/]", False))

    # API keys
    for prov in PROVIDERS:
        if prov == "ollama":
            continue
        key = get_api_key(prov)
        if key:
            results.append((prov.capitalize(), "[green]Key set[/]", True))
        else:
            results.append((prov.capitalize(), "[yellow]No key[/]", False))

    # Docker
    if shutil.which("docker"):
        try:
            r = subprocess.run(["docker", "info"], capture_output=True, timeout=5)
            if r.returncode == 0:
                results.append(("Docker", "[green]Running[/]", True))
            else:
                results.append(("Docker", "[yellow]Installed, daemon not running[/]", False))
        except Exception:
            results.append(("Docker", "[yellow]Error checking[/]", False))
    else:
        results.append(("Docker", "[dim]Not installed[/]", False))

    # Config file
    results.append(("Config file", str(CONFIG_PATH), CONFIG_PATH.exists()))

    # Print
    table = Table(title="Validation Results", border_style="cyan")
    table.add_column("Service", style="bold", width=14)
    table.add_column("Status")
    for name, status, ok in results:
        table.add_row(name, status)
    console.print(table)

    total = len(results)
    passed = sum(1 for _, _, ok in results if ok)
    if passed == total:
        color = "green"
    elif passed > total // 2:
        color = "yellow"
    else:
        color = "red"
    console.print(f"\n[{color}]{passed}/{total}[/] checks passed")


@config_app.command("path")
def config_path() -> None:
    """Show configuration file path."""
    console.print(str(CONFIG_PATH))
