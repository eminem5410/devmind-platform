"""
Comando: devmind init
Inicializa un proyecto de IA con estructura estandar.
"""

import os
import subprocess
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

console = Console()

PROJECT_STRUCTURE = {
    "data/raw": "Datos crudos sin procesar",
    "data/processed": "Datos procesados listos para entrenamiento",
    "models": "Modelos entrenados y checkpoints",
    "notebooks": "Jupyter notebooks para experimentacion",
    "src": "Codigo fuente del proyecto",
    "src/data": "Scripts de procesamiento de datos",
    "src/models": "Definiciones de modelos",
    "src/training": "Scripts de entrenamiento",
    "src/evaluation": "Scripts de evaluacion",
    "src/inference": "Scripts de inferencia/prediccion",
    "src/api": "Endpoints de API (FastAPI)",
    "tests": "Tests unitarios e integracion",
    "configs": "Archivos de configuracion (YAML, JSON)",
    "docs": "Documentacion del proyecto",
    "scripts": "Scripts utilitarios",
}


def create_structure(project_name: str, path: Path) -> None:
    """Crea la estructura de directorios del proyecto."""
    base = path / project_name

    if base.exists():
        console.print(f"[red]El directorio '{base}' ya existe.[/red]")
        return

    console.print(f"\n[bold]Creando proyecto:[/bold] {project_name}")
    console.print(f"[dim]Ubicacion: {base}[/dim]\n")

    # Directorios
    created = []
    for dir_path, description in PROJECT_STRUCTURE.items():
        full_path = base / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        created.append((dir_path, description))

    # Archivos base
    # README
    readme = base / "README.md"
    readme.write_text(
        f"# {project_name}\n\n"
        f"Proyecto de IA inicializado con DevMind Platform.\n\n"
        f"## Estructura\n\n"
        + "\n".join(f"- `{d}`: {desc}" for d, desc in created) + "\n\n"
        f"## Inicio rapido\n\n"
        f"```bash\n# Crear entorno virtual\npython -m venv .venv\nsource .venv/bin/activate\n\n"
        f"# Instalar dependencias\npip install -r requirements.txt\n```\n"
    )

    # .gitignore
    gitignore = base / ".gitignore"
    gitignore.write_text(
        "# Python\n__pycache__/\n*.py[cod]\n*$py.class\n*.egg-info/\ndist/\nbuild/\n\n"
        "# Entorno virtual\n.venv/\nvenv/\n\n"
        "# Datos y modelos\nmodels/*.pt\nmodels/*.pth\nmodels/*.bin\ndata/\n\n"
        "# Jupyter\n.ipynb_checkpoints/\n\n"
        "# IDE\n.vscode/\n.idea/\n*.swp\n\n"
        "# OS\n.DS_Store\nThumbs.db\n"
    )

    # requirements.txt basico
    reqs = base / "requirements.txt"
    reqs.write_text(
        "# Core\ntorch>=2.0.0\ntransformers>=4.36.0\n\n"
        "# API\nfastapi>=0.109.0\nuvicorn>=0.27.0\n\n"
        "# Data\npandas>=2.0.0\nnumpy>=1.24.0\n\n"
        "# Dev\npytest>=8.0.0\nruff>=0.4.0\njupyter>=1.0.0\n"
    )

    # configs/config.yaml
    configs_dir = base / "configs"
    (configs_dir / "config.yaml").write_text(
        "# Configuracion del proyecto\nproject:\n  name: \"PROJECT_NAME\"\n  version: \"0.1.0\"\n\n"
        "model:\n  name: \"base\"\n  checkpoint: null\n\n"
        "training:\n  epochs: 10\n  batch_size: 32\n  learning_rate: 0.001\n"
    )

    # src/__init__.py
    (base / "src" / "__init__.py").write_text("")
    for sub in ["data", "models", "training", "evaluation", "inference", "api"]:
        (base / "src" / sub / "__init__.py").write_text("")

    # Tree
    console.print("[green]Estructura creada:[/green]\n")
    for dir_path, description in created:
        console.print(f"  [green]+[/green] {dir_path}/  [dim]{description}[/dim]")
    console.print(f"\n  [green]+[/green] README.md")
    console.print(f"  [green]+[/green] .gitignore")
    console.print(f"  [green]+[/green] requirements.txt")
    console.print(f"  [green]+[/green] configs/config.yaml")

    # Git init
    try:
        subprocess.run(["git", "init", str(base)], capture_output=True, timeout=5)
        console.print(f"\n  [green]+[/green] Git repository inicializado")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    console.print()
    console.print(Panel(
        f"[bold green]Proyecto '{project_name}' creado exitosamente[/bold green]\n\n"
        f"[dim]Siguientes pasos:[/dim]\n"
        f"  cd {base}\n"
        f"  python -m venv .venv && source .venv/bin/activate\n"
        f"  pip install -r requirements.txt",
        border_style="green",
    ))


def run_init() -> None:
    """Ejecuta la inicializacion de un proyecto AI."""
    console.print()
    console.print(Panel(
        "[bold cyan]DevMind Init[/bold cyan] — Inicializar proyecto de IA",
        border_style="cyan",
    ))

    project_name = Prompt.ask("\n[bold]Nombre del proyecto[/bold]", default="my-ai-project")
    project_name = project_name.strip().lower().replace(" ", "-")

    target = Prompt.ask("[bold]Ubicacion[/bold]", default=".")
    path = Path(target).resolve()

    # Confirm
    console.print()
    console.print(f"  Proyecto: [bold]{project_name}[/bold]")
    console.print(f"  Path: [bold]{path / project_name}[/bold]")
    console.print()

    if Confirm.ask("Crear proyecto?", default=True):
        create_structure(project_name, path)
    else:
        console.print("[dim]Cancelado.[/dim]")
