"""
DevMind Platform CLI — Punto de entrada principal.

Comandos:
  devmind doctor              Diagnostica el sistema con severidad y recomendaciones
  devmind doctor --json       Output estructurado para APIs/GUIs/telemetry
  devmind doctor -c           Output compacto de una pantalla (CI)
  devmind snapshot            Exporta el estado completo del sistema a JSON/YAML
  devmind benchmark           Mide rendimiento de modelos Ollama (tokens/s, RAM, latencia)
  devmind explain             Explica warnings y topics en profundidad
  devmind history             Muestra historial de diagnosticos y benchmarks
  devmind setup               Configura ambientes AI con perfiles predefinidos
  devmind serve               Levanta la API REST (FastAPI + Uvicorn)
  devmind gpu                 Verifica GPUs, drivers CUDA y Vulkan
  devmind init                Inicializa un proyecto de IA con estructura estandar
  devmind repair              Repara problemas detectados automaticamente
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
def init(
    interactive: bool = typer.Option(
        False, "--interactive", "-i",
        help="Wizard interactivo: configurar API keys, provider y modelo default",
    ),
):
    """Inicializa un proyecto de IA o configura DevMind (--interactive)."""
    if interactive:
        from devmind.commands.init_cmd import run_init_wizard
        run_init_wizard()
    else:
        from devmind.commands.init_cmd import run_init
        run_init()


@app.command()
def snapshot(
    json_output: bool = typer.Option(
        False, "--json", "-j",
        help="Output como JSON estructurado",
    ),
    compact: bool = typer.Option(
        False, "--compact", "-c",
        help="Output compacto de una pantalla",
    ),
    output: str = typer.Option(
        None, "--output", "-o",
        help="Guardar snapshot a archivo (ej: state.json, state.yaml)",
    ),
):
    """Exporta el estado completo del sistema a JSON o YAML."""
    from devmind.commands.snapshot import run_snapshot
    run_snapshot(json_output=json_output, compact=compact, output=output)


@app.command()
def explain(
    topic: str = typer.Argument(
        None,
        help="Topic a explicar: ram, gpu, python, ollama, docker. Sin argumento muestra warnings del ultimo doctor.",
    ),
):
    """Explica warnings y topics de IA en profundidad."""
    from devmind.commands.explain import run_explain
    run_explain(topic=topic)


@app.command()
def history(
    last: int = typer.Option(
        20, "--last", "-n",
        help="Numero de eventos a mostrar (default: 20)",
    ),
    doctor: bool = typer.Option(
        False, "--doctor", "-d",
        help="Mostrar solo historial de diagnosticos",
    ),
    bench: bool = typer.Option(
        False, "--bench", "-b",
        help="Mostrar solo historial de benchmarks",
    ),
    llm: bool = typer.Option(
        False, "--llm",
        help="Mostrar historial de LLM benchmarks (SQLite)",
    ),
    json_output: bool = typer.Option(
        False, "--json", "-j",
        help="Output como JSON estructurado",
    ),
):
    """Muestra historial de diagnosticos, benchmarks y snapshots."""
    from devmind.commands.history import run_history
    run_history(last=last, doctor=doctor, bench=bench, llm=llm, json_output=json_output)


@app.command()
def serve(
    port: int = typer.Option(
        8080, "--port", "-p",
        help="Puerto para la API (default: 8080)",
    ),
    host: str = typer.Option(
        "127.0.0.1", "--host",
        help="Host para escuchar (default: 127.0.0.1)",
    ),
    reload: bool = typer.Option(
        False, "--reload",
        help="Auto-reload en desarrollo",
    ),
):
    """Levanta la API REST de DevMind con FastAPI + Uvicorn."""
    from devmind.commands.serve import run_serve
    run_serve(port=port, host=host, reload=reload)


@app.command(name="setup")
def setup(
    profile: str = typer.Argument(
        None,
        help="Perfil de setup: local-llm, ai-dev, rag-lab. Sin argumento lista perfiles disponibles.",
    ),
    output_dir: str = typer.Option(
        None, "--dir", "-d",
        help="Directorio de salida (default: directorio actual)",
    ),
    force: bool = typer.Option(
        False, "--force", "-f",
        help="Sobreescribir archivos existentes",
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run",
        help="Mostrar que se crearia sin escribir archivos",
    ),
):
    """Configura ambientes AI completos con perfiles predefinidos."""
    if profile is None or profile == "list":
        from devmind.commands.setup import run_setup_list
        run_setup_list()
    else:
        from devmind.commands.setup import run_setup_profile
        run_setup_profile(
            profile_name=profile,
            output_dir=output_dir,
            force=force,
            dry_run=dry_run,
        )


# ── Repair: subcommand group ──────────────────────────────────────────────
# ── Chat: interactive LLM ─────────────────────────────────────────────────

@app.command()
def chat(
    model: str = typer.Option(
        None, "--model", "-m",
        help="Modelo a usar (default: configurado en init)",
    ),
    provider: str = typer.Option(
        None, "--provider", "-p",
        help="Provider a usar (ollama, groq, together, openrouter, fireworks)",
    ),
    session: int = typer.Option(
        None, "--session", "-s",
        help="ID de sesion a resumir",
    ),
    list_sessions: bool = typer.Option(
        False, "--list", "-l",
        help="Listar sesiones recientes",
    ),
    prompt: str = typer.Option(
        None, "--prompt",
        help="Enviar un mensaje y salir (modo non-interactive)",
    ),
):
    """Chat interactivo con LLMs (Ollama local + APIs)."""
    from devmind.commands.chat import run_chat
    run_chat(
        model=model,
        provider=provider,
        session=session,
        list_sessions=list_sessions,
        prompt_text=prompt,
    )


# ── Stats: analytics dashboard ────────────────────────────────────────────

@app.command()
def stats(
    compact: bool = typer.Option(
        False, "--compact", "-c",
        help="Output compacto de una linea (para scripts)",
    ),
    days: int = typer.Option(
        7, "--days", "-d",
        help="Dias de actividad a mostrar (default: 7)",
    ),
):
    """Dashboard de analytics: tokens, sesiones, providers."""
    from devmind.commands.stats import run_stats
    run_stats(compact=compact, days=days)


# ── Search: full-text search ──────────────────────────────────────────────

@app.command()
def search(
    query: str = typer.Argument(
        None,
        help="Texto a buscar en el historial de chats",
    ),
    provider: str = typer.Option(
        None, "--provider", "-p",
        help="Filtrar por provider (ollama, groq, together, openrouter, fireworks)",
    ),
    role: str = typer.Option(
        None, "--role", "-r",
        help="Filtrar por rol (user, assistant)",
    ),
    limit: int = typer.Option(
        20, "--limit", "-n",
        help="Maximo de resultados (default: 20)",
    ),
    export_format: str = typer.Option(
        None, "--export", "-e",
        help="Exportar resultados (formato: md)",
    ),
    output: str = typer.Option(
        None, "--output", "-o",
        help="Archivo de salida para exportacion",
    ),
):
    """Busca en el historial de chats usando FTS5 full-text search."""
    from devmind.commands.search import run_search
    run_search(
        query=query or "",
        provider=provider,
        role=role,
        limit=limit,
        export_format=export_format,
        output_file=output,
    )


from devmind.commands.repair import repair_app
app.add_typer(repair_app, name="repair")

# ── Benchmark: subcommand group ───────────────────────────────────────────
from devmind.commands.benchmark import benchmark_app
app.add_typer(benchmark_app, name="benchmark")

# ── Compare: subcommand group ─────────────────────────────────────────────
from devmind.commands.compare import compare_app
app.add_typer(compare_app, name="compare")

from devmind.commands.forecast import forecast_app
from devmind.commands.llm_benchmark import llm_bench_app
app.add_typer(forecast_app, name="forecast")
app.add_typer(llm_bench_app, name="llm-benchmark")

from devmind.commands.optimize import optimize_app
app.add_typer(optimize_app, name="optimize")

from devmind.commands.config_cmd import config_app
app.add_typer(config_app, name="config")

from devmind.commands.export import export_app
app.add_typer(export_app, name="export")


# ── Callback principal (sin subcomando) ──────────────────────────────────

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """DevMind Platform — Herramientas CLI para desarrollo de IA en Linux."""
    if ctx.invoked_subcommand is None:
        console.print()
        console.print("[bold cyan]DevMind Platform[/bold cyan] v0.14.0")
        console.print("[dim]Plataforma integral para desarrollo de IA en Linux[/dim]")
        console.print()
        console.print("Comandos disponibles:")
        console.print()
        console.print("  [bold]devmind doctor[/bold]           Diagnostica el sistema completo")
        console.print("  [bold]devmind doctor --json[/bold]      Output JSON estructurado")
        console.print("  [bold]devmind doctor -c[/bold]         Output compacto (CI/scripting)")
        console.print("  [bold]devmind snapshot[/bold]          Exporta estado del sistema")
        console.print("  [bold]devmind benchmark ollama[/bold]    Benchmark modelos Ollama")
        console.print("  [bold]devmind compare[/bold]             Compara costos local vs APIs")
        console.print("  [bold]devmind forecast[/bold]            Prediccion de costos a futuro")
        console.print("  [bold]devmind optimize[/bold]            Recomienda modelo/provider optimo")
        console.print("  [bold]devmind explain[/bold]           Explica warnings en profundidad")
        console.print("  [bold]devmind history[/bold]           Historial de diagnosticos/benchmarks")
        console.print("  [bold]devmind setup[/bold]             Configura ambiente AI (perfiles)")
        console.print("  [bold]  setup local-llm[/bold]        Chat local: Ollama + OpenWebUI")
        console.print("  [bold]  setup ai-dev[/bold]           Entorno AI: Docker + Jupyter + deps")
        console.print("  [bold]  setup rag-lab[/bold]          Stack RAG: Ollama + ChromaDB")
        console.print("  [bold]devmind gpu[/bold]              Verifica GPUs y drivers")
        console.print("  [bold]devmind stats[/bold]               Dashboard de analytics")
        console.print("  [bold]  stats --compact[/bold]         Resumen en una linea")
        console.print("  [bold]devmind search <query>[/bold]     Buscar en historial de chats")
        console.print("  [bold]  search --export md[/bold]      Exportar resultados")
        console.print("  [bold]devmind chat[/bold]               Chat interactivo con LLMs")
        console.print("  [bold]  chat --provider groq[/bold]     Usar provider especifico")
        console.print("  [bold]  chat --list[/bold]             Listar sesiones")
        console.print("  [bold]devmind init[/bold]             Inicializa un proyecto de IA")
        console.print("  [bold]  init --interactive[/bold]       Configurar API keys y provider")
        console.print("  [bold]devmind repair[/bold]           Repara problemas automaticamente")
        console.print("  [bold]devmind serve[/bold]             Levanta API REST (FastAPI)")
        console.print("  [bold]  serve --port 3000[/bold]       Puerto custom")
        console.print("  [bold]  repair ollama[/bold]          Instala/inicia Ollama + modelos")
        console.print("  [bold]  repair docker[/bold]          Verifica/instala Docker + Compose")
        console.print("  [bold]  repair all[/bold]             Repara todo automaticamente")
        console.print()
        console.print("[dim]Ejecuta 'devmind <comando> --help' para mas detalles.[/dim]")
        console.print()


if __name__ == "__main__":
    app()
