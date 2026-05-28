"""
Comando: devmind explain
Explica warnings y checks del diagnostico en profundidad.

Uso:
  devmind explain             Explica los warnings del ultimo doctor
  devmind explain ram         Deep dive sobre RAM y modelos AI
  devmind explain gpu         GPUs compatibles para IA
  devmind explain python      Versiones Python y compatibilidad
  devmind explain ollama      Todo sobre Ollama y modelos
  devmind explain docker      Docker para entornos de IA
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from devmind.utils.logging import logger

console = Console()

EXPLAINATIONS = {
    "ram": """## RAM y Modelos de IA

La memoria RAM es uno de los factores mas criticos para ejecutar modelos de IA localmente. Cada modelo necesita cargar sus pesos en memoria antes de poder generar texto.

### Cuanta RAM necesitas

| Tamaño Modelo | Parametros | RAM minima (Q4) | RAM recomendada |
|--------------|-----------|-----------------|-----------------|
| 1B | ~1.3B | 2 GB | 4 GB |
| 3B | ~3.8B | 3 GB | 6 GB |
| 7B | ~7B | 5 GB | 8 GB |
| 13B | ~13B | 8 GB | 16 GB |
| 34B | ~34B | 20 GB | 32 GB |
| 70B | ~70B | 40 GB | 64 GB |

### Cuantizacion

La cuantizacion reduce el tamano del modelo comprimiendo los pesos:
- **FP16** (16-bit): Calidad maxima, doble de RAM
- **Q8** (8-bit): ~75% del tamano, perdida minima
- **Q4** (4-bit): ~40% del tamano, buena calidad
- **Q2** (2-bit): ~25% del tamano, calidad reducida

Ollama usa Q4 por defecto, lo cual es un buen balance.

### Tu configuracion

Con tu hardware, los modelos recomendados son:
- **phi3:mini** (3.8B, ~2.3GB) — Buen balance calidad/velocidad
- **llama3.2:1b** (1.3B, ~800MB) — Maxima velocidad
- **gemma2:2b** (2B, ~1.3GB) — Buena calidad en formato compacto

### Tips para RAM limitada

1. Cierra aplicaciones innecesarias antes de usar modelos
2. Usa `docker compose down` para liberar contenedores que no usas
3. Elige modelos mas pequenos para tareas simples
4. Reduce `num_ctx` (context window) si no necesitas contexto largo
5. Considera un upgrade a 16GB (2x8GB DDR4 cuesta ~$40-60 USD)
""",

    "gpu": """## GPUs para Inteligencia Artificial

Una GPU dedicada acelera la inferencia de modelos de IA dramaticamente: de 4-6 tokens/s en CPU a 30-80+ tokens/s en GPU.

### GPUs recomendadas por presupuesto

| GPU | VRAM | Tokens/s (7B) | Precio aprox |
|-----|------|---------------|-------------|
| GTX 1650 | 4 GB | ~15 | Usada ~$80 |
| RTX 3060 12GB | 12 GB | ~40 | ~$250 |
| RTX 4060 Ti 16GB | 16 GB | ~55 | ~$400 |
| RTX 3090 24GB | 24 GB | ~70 | Usada ~$700 |
| RTX 4090 24GB | 24 GB | ~90 | ~$1,600 |

### Por que importa la VRAM

La VRAM determina que tan grande puede ser el modelo:
- 4 GB VRAM: Modelos hasta 3B (Q4) o 7B (Q2)
- 8 GB VRAM: Modelos hasta 7B (Q4) o 13B (Q4 con offloading)
- 12 GB VRAM: Modelos hasta 13B (Q4) o 7B (FP16)
- 16 GB VRAM: Modelos hasta 13B (FP16) o 34B (Q4)
- 24 GB VRAM: Modelos hasta 70B (Q4) o 34B (FP16)

### NVIDIA vs AMD vs Intel

- **NVIDIA**: Mejor soporte. CUDA es el estandar de la industria. PyTorch, TensorFlow, Ollama — todo funciona de primera.
- **AMD**: ROCm mejora constantemente pero aun tiene gaps. Soporte parcial en PyTorch.
- **Intel**: Arc GPUs soportan OpenVINO y algunos modelos via IPEX. En desarrollo activo.

### Setup con GPU NVIDIA

Una vez instalada la GPU:
```bash
# Instalar drivers
sudo ubuntu-drivers autoinstall

# Verificar
nvidia-smi

# Instalar CUDA Toolkit
sudo apt install nvidia-cuda-toolkit

# Verificar con DevMind
devmind doctor
devmind benchmark ollama  # Ver la diferencia de velocidad
```

### Alternativas sin GPU

Si no podes instalar una GPU:
- **RunPod.io**: Alquila GPUs por hora (~$0.40/h RTX 3090)
- **Lambda Labs**: Similar, orientado a ML
- **Google Colab**: GPU gratuita por 12h (limitada)
- **Together AI / Groq**: APIs de inferencia con modelos potentes
""",

    "python": """## Python para Desarrollo de IA

La version de Python afecta directamente la compatibilidad con frameworks de IA.

### Versiones recomendadas

| Version | Estado | Recomendacion |
|---------|--------|---------------|
| 3.11 | Estable | Excelente para IA (max compatibilidad) |
| 3.12 | LTS | Mejor opcion actual (performance + compatibilidad) |
| 3.13 | Reciente | Buena, algunos paquetes aun no soportados |
| 3.14 | Muy reciente | Experimental para IA (algunos paquetes rotos) |
| 3.15 | Bleeding edge | No recomendada para produccion |

### Frameworks y compatibilidad

| Framework | 3.11 | 3.12 | 3.13 | 3.14 |
|-----------|------|------|------|------|
| PyTorch | OK | OK | OK | Parcial |
| TensorFlow | OK | OK | Parcial | No |
| scikit-learn | OK | OK | OK | Parcial |
| Transformers (HuggingFace) | OK | OK | OK | Parcial |
| LangChain | OK | OK | OK | Parcial |
| Ollama Python | OK | OK | OK | OK |

### Gestionar multiples versiones con pyenv

```bash
# Instalar pyenv
curl https://pyenv.run | bash

# Instalar Python 3.12
pyenv install 3.12.8

# Usar 3.12 como default
pyenv global 3.12.8

# Verificar
python --version

# Para un proyecto especifico
cd mi-proyecto-ai
pyenv local 3.12.8
```

### Tu situacion

Tu sistema tiene Python {python_version}. Para desarrollo de IA, se recomienda usar Python 3.12 como version principal via pyenv, y reservar 3.14 para testing y experimentacion.
""",

    "ollama": """## Ollama — Motor de Inferencia Local

Ollama es la forma mas facil de ejecutar modelos de lenguaje grandes (LLMs) localmente en Linux.

### Comandos esenciales

```bash
# Instalar
curl -fsSL https://ollama.com/install.sh | sh

# Iniciar servidor
ollama serve

# Listar modelos
ollama list

# Descargar modelo
ollama pull phi3:mini

# Chatear con modelo
ollama run phi3:mini

# Ejecutar en background
ollama serve &
```

### Modelos populares

| Modelo | Parametros | Tamano (Q4) | RAM necesaria | Mejor para |
|--------|-----------|-------------|---------------|------------|
| llama3.2:1b | 1.3B | ~800MB | 2 GB | Chat rapido, embedding |
| phi3:mini | 3.8B | ~2.3GB | 4 GB | Chat general, razonamiento |
| gemma2:2b | 2B | ~1.3GB | 3 GB | Chat, code |
| llama3.2:3b | 3.2B | ~2GB | 4 GB | Chat, instrucciones |
| mistral:7b | 7.3B | ~4.4GB | 8 GB | Chat avanzado, code |
| llama3.1:8b | 8B | ~4.9GB | 8 GB | Chat, RAG, agents |
| codellama:7b | 7B | ~3.8GB | 8 GB | Generacion de codigo |
| nomic-embed-text | 137M | ~274MB | 1 GB | Embeddings para RAG |

### API de Ollama

Ollama expone una API REST en `http://localhost:11434`:

```bash
# Generar texto
curl http://localhost:11434/api/generate -d '{
  "model": "phi3:mini",
  "prompt": "Hola, quien sos?"
}'

# Chat
curl http://localhost:11434/api/chat -d '{
  "model": "phi3:mini",
  "messages": [{"role": "user", "content": "Hola!"}]
}'

# Listar modelos
curl http://localhost:11434/api/tags
```

### Benchmark con DevMind

```bash
# Medir rendimiento
devmind benchmark ollama

# Multiples runs para promediar
devmind benchmark ollama --runs 3

# Modelo especifico
devmind benchmark ollama -m phi3:mini
```
""",

        "attention-precision": """## Precisiones de Atencion — FP4, FP8, FP16, BF16, FP32

La precision de los numeros en GPU determina cuanto VRAM usan los modelos, que tan rapido corren, y la calidad del output.

### Que es cada precision

| Precision | Bits | VRAM vs FP32 | Calidad | Velocidad |
|-----------|------|--------------|---------|-----------|
| FP32 | 32 | 1x (base) | Maxima | Lenta |
| FP16 | 16 | 0.5x | Excelente | 2x mas rapida |
| BF16 | 16 | 0.5x | Excelente | 2x mas rapida |
| FP8 | 8 | 0.25x | Buena | 4x mas rapida |
| FP4 | 4 | 0.125x | Aceptable | 8x mas rapida |

### Que significa en la practica

Un modelo de 70B parametros:
- **FP32**: 280 GB VRAM (imposible en GPU individual)
- **FP16**: 140 GB VRAM (necesita 8x A100 80GB)
- **FP8**: 70 GB VRAM (1x H100 80GB)
- **FP4**: 35 GB VRAM (1x RTX 4090 con offloading)

### FP4 y ThriftAttention

FP4 (4-bit floating point) es la precision mas nueva. ThriftAttention es un paper que propone usar FP4 para la capa de atencion mientras mantiene FP16 para el resto, logrando:
- **2x reduccion de VRAM** en la atencion
- **Calidad casi identica** a FP16 completo
- **Mejor throughput** por usar menos memoria

Actualmente FP4 es soportado principalmente por NPUs (Qualcomm Snapdragon, Intel Core Ultra) y experimentalmente en GPUs NVIDIA via software.

### Hardware compatible

| Hardware | FP4 | FP8 | FP16 | BF16 |
|---------|-----|-----|------|------|
| NVIDIA H100 | Experimental | Si | Si | Si |
| RTX 4090 | No | Si | Si | Si |
| RTX 3090 | No | No | Si | Si |
| RTX 3060 | No | No | Si | Si |
| AMD MI300X | No | Si | Si | Si |
| Apple M4 Max | No | No | Si | Si |
| Qualcomm X Elite | Si | Si | Si | Si |
| Intel Core Ultra | Si | Si | Si | Si |

### Cuando conviene cada una

- **FP32**: Solo para training preciso o cuando la calidad es critica
- **FP16/BF16**: Standard para inferencia. BF16 es mejor para training
- **FP8**: Ideal para inferencia de modelos grandes en GPUs modernas (RTX 40xx, H100)
- **FP4**: Futuro. Ideal para edge AI y NPUs. Aun experimental en GPUs

Ejecuta `devmind explain gpu` para ver GPUs recomendadas por presupuesto.
""",
    "docker": """## Docker para Entornos de IA

Docker te permite ejecutar herramientas de IA en contenedores aislados sin contaminar tu sistema.

### Comandos esenciales

```bash
# Instalar
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker

# Verificar
docker --version
docker compose version

# Ejecutar contenedor
docker run --rm hello-world
```

### Contenedores utiles para IA

| Contenedor | Uso | Comando |
|-----------|-----|---------|
| Ollama | Inferencia LLM | `docker run -d -p 11434:11434 ollama/ollama` |
| Jupyter | Notebooks | `docker run -d -p 8888:8888 jupyter/scipy-notebook` |
| ChromaDB | Vector store | `docker run -d -p 8000:8000 chromadb/chroma` |
| PostgreSQL+pgvector | DB + vectores | `docker run -d -p 5432:5432 pgvector/pgvector` |
| vLLM | Serving rapido | `docker run --gpus all -d vllm/vllm-openai` |

### Docker Compose

Permite definir stacks multi-contenedor con un solo YAML:

```bash
# Levantar stack
docker compose up -d

# Ver logs
docker compose logs -f

# Detener
docker compose down

# Detener y borrar datos
docker compose down -v
```

### Limpieza

Los contenedores e imagenes de IA ocupan mucho disco:

```bash
# Espacio usado
docker system df

# Limpiar todo (contenedores, imagenes, volumenes)
docker system prune -a --volumes

# Solo imagenes sin usar
docker image prune -a
```

### Setup con DevMind

```bash
# Verificar Docker
devmind doctor  # Revisa Docker + Compose

# Reparar si es necesario
devmind repair docker

# Crear stack completo
devmind setup local-llm  # Ollama + OpenWebUI
devmind setup rag-lab    # Ollama + ChromaDB + FastAPI
```
""",
}


def _get_last_doctor_warnings() -> Optional[list[dict]]:
    """Lee el ultimo doctor_run de los logs y retorna los warnings."""
    log_file = Path.home() / ".devmind" / "logs" / "devmind.log"
    if not log_file.exists():
        return None

    last_doctor = None
    with open(log_file) as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                if entry.get("event") == "doctor_run":
                    last_doctor = entry
            except (json.JSONDecodeError, ValueError):
                continue

    return last_doctor


def run_explain(
    topic: Optional[str] = None,
) -> None:
    """Explica un topic o los warnings del ultimo doctor."""
    start_time = time.time()
    logger.command_start("explain", {"topic": topic})

    console.print()
    console.print(Panel(
        "[bold cyan]DevMind Explain[/bold cyan] — Explicaciones en profundidad",
        border_style="cyan",
    ))
    console.print()

    # Si no se especifica topic, explicar warnings del ultimo doctor
    if topic is None:
        console.print("[bold]Explicando warnings del ultimo diagnostico...[/bold]")
        console.print()

        last_doctor = _get_last_doctor_warnings()
        if not last_doctor:
            console.print("  [yellow]No se encontro un diagnostico previo.[/yellow]")
            console.print("  [dim]Ejecuta 'devmind doctor' primero.[/dim]")
            console.print()
            console.print("[bold]Topics disponibles:[/bold]")
            for t in EXPLAINATIONS:
                console.print(f"  [cyan]{t}[/cyan]")
            console.print()
            logger.command_end("explain", time.time() - start_time)
            return

        data = last_doctor.get("data", {})
        warnings = data.get("warnings", 0)
        errors = data.get("errors", 0)
        health = data.get("health_score", 0)

        console.print(f"  [bold]Ultimo diagnostico:[/bold] Health {health}/100, "
                      f"{warnings} warnings, {errors} errors")
        console.print()

        if warnings == 0 and errors == 0:
            console.print("  [green]Tu sistema no tiene warnings.[/green]")
            console.print("  [dim]Todo esta bien. Explora topics especificos:[/dim]")
            for t in EXPLAINATIONS:
                console.print(f"  [cyan]$ devmind explain {t}[/cyan]")
        else:
            # Explicar topics relevantes basados en warnings
            console.print("[bold]Explicaciones relevantes:[/bold]")
            console.print()

            # Siempre explicar los topics mas comunes
            relevant = ["ram", "gpu", "python", "ollama", "docker"]
            for t in relevant:
                if t in EXPLAINATIONS:
                    console.print(Panel(
                        f"[bold]$ devmind explain {t}[/bold] — "
                        f"{t.upper()}",
                        border_style="dim",
                    ))

        console.print()
        console.print("[dim]Ejecuta 'devmind explain <topic>' para ver la explicacion completa.[/dim]")
        console.print()

    else:
        # Explicar topic especifico
        key = topic.lower().strip()

        if key not in EXPLAINATIONS:
            console.print(f"  [yellow]Topic desconocido:[/yellow] {topic}")
            console.print(f"  [dim]Disponibles: {', '.join(EXPLAINATIONS.keys())}[/dim]")
            console.print()
            logger.command_end("explain", time.time() - start_time, success=False)
            return

        content = EXPLAINATIONS[key]

        # Reemplazar placeholders
        sys_info = get_system_info_safe()
        content = content.replace("{python_version}", sys_info.get("python", "desconocida"))

        console.print(Markdown(content))
        console.print()

    logger.command_end("explain", time.time() - start_time)


def get_system_info_safe() -> dict:
    """Obtiene info del sistema de forma segura para explain."""
    try:
        from devmind.utils.system import get_system_info
        info = get_system_info()
        return {
            "python": info.python_version or "desconocida",
            "ram": info.ram_total_gb or 0,
            "cpu": info.cpu_name or "desconocida",
        }
    except Exception:
        return {"python": "desconocida", "ram": 0, "cpu": "desconocida"}
