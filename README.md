<p align="center">
  <img width="600" alt="DevMind Platform" src="https://img.shields.io/badge/DevMind-Platform-00d4ff?style=for-the-badge&labelColor=0a0a1a&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0id2hpdGUiPjxwYXRoIGQ9Ik0xMiAyTDIgN2wxMCA1IDEwLTV6TTIgN2wxMCA1IDEwLTUtMTAgNXptMCAwTDIgMTJsMTAtNSAxMCA1LTIgN3ptMCAwTDIgMTdsMTAtNSAxMCA1LTIgN3oiLz48L3N2Zz4=">
  <br/>
  <strong>Linux-first AI environment diagnostics, observability & automation</strong>
  <br/>
  <br/>
  <a href="https://pypi.org/project/devmind/"><img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"></a>
  <a href="https://github.com/eminem5410/devmind-platform/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-Apache_2.0-blue?style=flat-square" alt="License"></a>
  <a href="https://github.com/eminem5410/devmind-platform/releases"><img src="https://img.shields.io/badge/Version-0.4.0-00d4ff?style=flat-square" alt="Version"></a>
  <img src="https://img.shields.io/badge/Linux-Ready-FCC624?style=flat-square&logo=linux&logoColor=black" alt="Linux">
</p>

---

> *"Diagnosticar impresiona. Reparar automáticamente enamora. Observar es comprender."*

DevMind es una CLI que **diagnostica, recomienda, repara, observa y configura** tu entorno de desarrollo AI en Linux. Detecta tu hardware, verifica herramientas, calcula un health score, repara problemas automáticamente, exporta snapshots, benchmarkea modelos locales, genera ambientes completos con perfiles predefinidos, explica warnings en profundidad y hace seguimiento de todo tu historial de actividad.

## Demo (v0.2.0 — Diagnostics + Repair)

<a href="https://asciinema.org/a/Pao5xWmKrGC3BfRU" target="_blank"><img src="https://asciinema.org/a/Pao5xWmKrGC3BfRU.svg" width="720" alt="DevMind Demo"/></a>

## Por qué DevMind

Configurar un entorno de IA en Linux es fragmentado: drivers NVIDIA, CUDA, Ollama, Docker, Python versions, RAM limits, modelos... DevMind unifica todo eso en un flujo inteligente:

```
Diagnosticar  →  Recomendar  →  Reparar  →  Observar  →  Configurar  →  Explicar
```

## Instalación

```bash
# Clonar el repo
git clone https://github.com/eminem5410/devmind-platform.git
cd devmind-platform

# Crear entorno virtual e instalar
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Quick Start

```bash
# Diagnosticar tu sistema completo
devmind doctor

# Configurar un stack de AI completo (adaptado a tu hardware)
devmind setup local-llm          # Ollama + OpenWebUI
devmind setup ai-dev             # Docker + Ollama + Jupyter + deps
devmind setup rag-lab            # Ollama + ChromaDB + FastAPI

# Benchmark de modelos Ollama (tokens/s, RAM, latencia)
devmind benchmark ollama

# Explicar warnings del doctor en profundidad
devmind explain ram              # RAM y modelos AI
devmind explain gpu              # GPUs para IA

# Ver historial de actividad
devmind history                  # Eventos recientes
devmind history -b               # Historial de benchmarks
devmind history -d               # Evolución del health score

# Exportar estado del sistema a JSON
devmind snapshot -o state.json

# Output compacto (ideal para CI y scripting)
devmind doctor --compact

# Output JSON estructurado (para APIs, GUIs, telemetry)
devmind doctor --json

# Reparar todo automáticamente
devmind repair all
```

## Output real

### `devmind doctor` — Diagnóstico completo

```
╭──────────────────────────────────────────────────────────────────────────╮
│ DevMind Doctor — Diagnostico inteligente del sistema                    │
╰──────────────────────────────────────────────────────────────────────────╯

  Salud del sistema: 93/100 (Excelente)
  ████████████████████████████░░

Sistema
  [INFO]   OS                    Linux x86_64
  [WARN]   Python                3.14.4  Version muy reciente
  [INFO]   CPU                   Intel(R) Core(TM) i5-7400 (4 cores)
  [WARN]   RAM                   6.5 / 7.1 GB (91%)  RAM limitada para modelos grandes
  [INFO]   Disco libre           287.2 GB

Ollama
  [INFO]   Ollama                0.24.0
  [INFO]   Ollama Server         ejecutando
  [INFO]   Ollama Modelos        phi3:mini

Recomendaciones
  [!] RAM limitada (7.1 GB)
      Se recomienda usar modelos pequenos (1B-4B) como phi3:mini.
      Accion: Considerar upgrade de RAM o usar quantization para modelos grandes

╭──────────────────────────────────────────────────────────────────────────╮
│ Tu sistema esta listo para desarrollo de IA                             │
╰──────────────────────────────────────────────────────────────────────────╯
```

### `devmind doctor --compact` — CI / Scripting

```
DevMind v0.4.0 | Health: 93/100 (Excelente) | W:3 | E:0
OS: Linux x86_64 | Python: 3.14.4 | CPU: Intel(R) Core(TM) i5-7400 (4c)
RAM: 6.5 / 7.1 GB (91%) | Disk: 287.2 GB
GPU: WARN | CUDA: -- | Vulkan: OK
Docker: OK (29.4.3) | Compose: v5.1.3
Ollama: OK (0.24.0) | Models: phi3:mini
Git: OK | pip: OK
Repairable: 0
```

### `devmind setup rag-lab --dry-run` — Perfiles de setup

```
╭──────────────────────────────────────────────────────────────────────────╮
│ DevMind Setup — Perfil: rag-lab                                         │
╰──────────────────────────────────────────────────────────────────────────╯

  Hardware: Intel(R) Core(TM) i5-7400 CPU @ 3.00GHz (4c), 7.1 GB RAM

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Archivo                          ┃ Tamano ┃ Descripcion                ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ docker-compose.yml               │  699 B │ Stack Docker               │
│ requirements.txt                 │  422 B │ Dependencias Python        │
│ rag_engine.py                    │  2.9 KB│ Motor RAG (ingest + query) │
│ api.py                           │  1.1 KB│ API FastAPI                │
│ .env                             │   91 B │ Variables de entorno       │
│ README.md                        │  1.2 KB│ Documentacion              │
└──────────────────────────────────┴────────┴────────────────────────────┘
```

### `devmind snapshot -c` — Observabilidad del sistema

```
DevMind Snapshot | 2026-05-28T05:48:09+00:00
CPU: Intel(R) Core(TM) i5-7400 CPU @ 3.00GHz (4c) | RAM: 6.5/7.1 GB | Disk: 287.2 GB free
GPU: CPU-only
OS: Linux 7.0.0-15-generic | Python: 3.14.4 | Git: 2.53.0
Docker: 29.4.3 | Ollama: 0.24.0 | Models: phi3:mini
```

### `devmind benchmark ollama` — Rendimiento de modelos

```
╭──────────────────────────────────────────────────────────────────────────╮
│ DevMind Benchmark — Ollama Performance                                   │
╰──────────────────────────────────────────────────────────────────────────╯

  Hardware: Intel(R) Core(TM) i5-7400 CPU @ 3.00GHz (4c), 7.1 GB RAM

  Run 1 — phi3:mini

  Throughput                6.17 tokens/s (Aceptable)
  TTFT (Time to First Token) 219 ms
  Total time                26154 ms
  Tokens generados          160 tokens
  RAM pico Ollama           3750 MB

Resumen
  Benchmarks OK             1/1
  Avg throughput            6.17 tokens/s
  Avg TTFT                  219 ms
  Avg RAM pico              3750 MB
```

### `devmind history -b` — Historial de benchmarks

```
Historial de Benchmarks

┏━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━╳━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━┓
┃   # ┃ Hora     ┃ Modelo         ┃    tok/s ┃     TTFT ┃   RAM MB ┃ Duracion ┃
┡━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━┩
│   1 │ 05:50:26 │ phi3:mini      │     2.62 │   5731ms │     3747 │    50.8s │
│   2 │ 05:51:12 │ phi3:mini      │     6.12 │    239ms │     3749 │    22.9s │
│   3 │ 05:51:41 │ phi3:mini      │     6.17 │    219ms │     3750 │    26.1s │
└─────┴──────────┴────────────────┴──────────┴──────────┴──────────┴──────────┘

  Promedios: 4.97 tok/s | TTFT 2063ms | RAM 3749MB
  Total benchmarks: 3
```

### `devmind explain ram` — Explicaciones en profundidad

```
## RAM y Modelos de IA

La memoria RAM es uno de los factores mas criticos para ejecutar modelos de IA
localmente. Cada modelo necesita cargar sus pesos en memoria antes de poder
generar texto.

### Cuanta RAM necesitas

| Tamaño Modelo | Parametros | RAM minima (Q4) | RAM recomendada |
|--------------|-----------|-----------------|-----------------|
| 1B           | ~1.3B     | 2 GB            | 4 GB            |
| 3B           | ~3.8B     | 3 GB            | 6 GB            |
| 7B           | ~7B       | 5 GB            | 8 GB            |
...
```

## Comandos

### Diagnostico y reparacion

| Comando | Descripción |
|---------|-------------|
| `devmind doctor` | Diagnóstico completo con severity, health score y recomendaciones |
| `devmind doctor --compact` | Output de 10 líneas para CI y scripting |
| `devmind doctor --json` | Output JSON estructurado para APIs, GUIs, telemetry |
| `devmind repair ollama` | Instala, inicia Ollama y descarga modelo recomendado |
| `devmind repair docker` | Inicia daemon, instala Compose, verifica permisos |
| `devmind repair all` | Ejecuta todas las reparaciones en secuencia |

### Observabilidad

| Comando | Descripción |
|---------|-------------|
| `devmind snapshot` | Exporta estado completo del sistema (terminal) |
| `devmind snapshot -o state.json` | Guardar snapshot a archivo JSON |
| `devmind snapshot -o state.yaml` | Guardar snapshot a archivo YAML |
| `devmind snapshot --json` | Snapshot como JSON por stdout |
| `devmind snapshot -c` | Snapshot compacto de 6 líneas |
| `devmind benchmark ollama` | Benchmark de modelos Ollama (tokens/s, TTFT, RAM) |
| `devmind benchmark ollama --runs 3` | 3 runs y promedia resultados |
| `devmind benchmark ollama -m phi3:mini` | Benchmark un modelo específico |
| `devmind benchmark ollama -c` | Benchmark compacto de 1 línea |
| `devmind benchmark ollama --json` | Benchmark como JSON estructurado |

### Ecosistema (v0.4.0)

| Comando | Descripción |
|---------|-------------|
| `devmind setup` | Lista perfiles disponibles |
| `devmind setup local-llm` | Chat local: Ollama + OpenWebUI |
| `devmind setup ai-dev` | Entorno AI: Docker + Ollama + Jupyter + dependencias |
| `devmind setup rag-lab` | Stack RAG: Ollama + ChromaDB + FastAPI template |
| `devmind setup <perfil> --dry-run` | Simula sin escribir archivos |
| `devmind setup <perfil> --force` | Sobreescribe archivos existentes |
| `devmind setup <perfil> --dir ./mi-proy` | Output a directorio específico |
| `devmind explain` | Explica warnings del último `devmind doctor` |
| `devmind explain ram` | Deep dive: RAM y modelos de IA |
| `devmind explain gpu` | Deep dive: GPUs para IA, VRAM, presupuesto |
| `devmind explain python` | Deep dive: Versiones Python y compatibilidad |
| `devmind explain ollama` | Deep dive: Ollama, modelos, API |
| `devmind explain docker` | Deep dive: Docker para entornos IA |
| `devmind history` | Muestra historial de actividad reciente |
| `devmind history -b` | Historial de benchmarks con promedios |
| `devmind history -d` | Evolución del health score entre diagnósticos |
| `devmind history -n 50` | Últimos 50 eventos |
| `devmind history --json` | Historial como JSON estructurado |

### Herramientas

| Comando | Descripción |
|---------|-------------|
| `devmind gpu` | Análisis detallado de GPU, drivers CUDA y Vulkan |
| `devmind init` | Scaffolding interactivo de proyectos AI |

## Perfiles de Setup

Los perfiles generan stacks completos adaptados a tu hardware detectado:

### `local-llm` — Chat local con LLM

```
docker-compose.yml   → Ollama + OpenWebUI
.env                 → Variables de entorno (modelo, puertos)
README.md            → Documentación con comandos útiles
```

### `ai-dev` — Entorno completo de desarrollo AI

```
docker-compose.yml          → Ollama + Jupyter
requirements.txt            → PyTorch, transformers, langchain, jupyter...
.env                        → Variables de entorno
notebooks/test-setup.ipynb  → Notebook de verificación
README.md                   → Documentación completa
```

### `rag-lab` — Stack de Retrieval-Augmented Generation

```
docker-compose.yml   → Ollama + ChromaDB
requirements.txt     → langchain, chromadb, fastapi...
rag_engine.py        → Motor RAG (ingest + query) listo para usar
api.py               → API FastAPI con endpoints /query y /ingest
.env                 → Variables de entorno
README.md            → Documentación con ejemplos curl
```

> Los perfiles detectan tu RAM y GPU para recomendar el modelo óptimo automáticamente.

## Features

### Health Score
Puntuación 0-100 que evalúa la preparación de tu sistema para IA, basada en todos los checks realizados. Se visualiza con barra de progreso y etiqueta (Excelente/Bueno/Aceptable/Necesita atención/Crítico).

### Severity Levels
Cada check tiene un nivel de severidad: `INFO`, `WARNING`, `ERROR`, `CRITICAL`. Permite filtrar, colorear y priorizar issues para UIs, APIs y repair engines.

### Recomendaciones inteligentes
El motor analiza tu hardware y software para generar recomendaciones contextuales. Con 7.1 GB RAM recomienda modelos 1B-4B; con GPU NVIDIA recomienda `llama3.1:8b`; detecta Python 3.14 y sugiere 3.12 LTS.

### Auto-repair
Repara automáticamente problemas detectados: instala e inicia Ollama, descarga el modelo óptimo según tu hardware, verifica Docker daemon y Compose.

### Setup Profiles (v0.4.0)
Genera stacks completos de desarrollo AI con un solo comando. Los templates se adaptan a tu hardware (RAM, GPU) para recomendar el modelo óptimo y configurar límites de recursos. Tres perfiles disponibles: `local-llm` para chat, `ai-dev` para desarrollo completo, `rag-lab` para retrieval-augmented generation.

### Explain Mode (v0.4.0)
Explica en profundidad los warnings del doctor y temas clave de IA. Sin argumento, analiza el último diagnóstico y sugiere explicaciones relevantes. Con topic específico (`ram`, `gpu`, `python`, `ollama`, `docker`), muestra guías completas con tablas comparativas, comandos y recomendaciones de hardware con precios.

### History (v0.4.0)
Lee los logs estructurados de `~/.devmind/logs/devmind.log` para mostrar el historial completo de actividad. Filtra por tipo: diagnosticos (`-d`), benchmarks (`-b`), o todos. Muestra tablas con evolución del health score, promedios de throughput y tendencias.

### Snapshot (v0.3.0)
Exporta el estado completo del sistema a JSON o YAML. Incluye hardware (CPU, RAM, GPU, disco), software (OS, Python, Docker, Ollama, Git) y red. Ideal para compartir en issues, comparar antes/después, y debugging remoto.

### Benchmark (v0.3.0)
Mide rendimiento real de modelos Ollama usando la API de streaming: tokens/s (throughput), TTFT (time to first token), RAM pico consumida, duración total. Color coding de rendimiento y tips para optimizar.

### Logs estructurados (v0.3.0)
Todos los comandos registran eventos en JSON en `~/.devmind/logs/devmind.log` con session ID, timestamps, y métricas. Rotación automática a 5MB. Útil para debugging, rollback y audit trail.

### 3 modos de output
Un solo modelo de datos (Pydantic), tres renderizadores:
- **Rich**: Terminal interactiva con colores, paneles y recomendaciones
- **Compact**: 10 líneas para CI, scripts y quick checks
- **JSON**: Estructura completa para APIs, GUIs, telemetry y pipelines

## Arquitectura

```
src/devmind/
├── cli.py                  # Typer entry point (9 comandos)
├── commands/
│   ├── benchmark.py        # Ollama performance benchmark (v0.3.0)
│   ├── doctor.py           # Diagnóstico con severity + health score
│   ├── explain.py          # Deep dive explanations (v0.4.0)
│   ├── gpu_check.py        # Análisis detallado de GPU
│   ├── history.py          # Activity history from logs (v0.4.0)
│   ├── init_cmd.py         # Scaffolding de proyectos AI
│   ├── repair.py           # Auto-repair engine
│   ├── setup.py            # Setup profiles orchestrator (v0.4.0)
│   └── snapshot.py         # System snapshot export (v0.3.0)
├── data/
│   └── profiles/
│       └── __init__.py     # Profile templates + generators (v0.4.0)
├── models/
│   ├── benchmark.py        # Pydantic: BenchmarkResult, BenchmarkReport
│   ├── diagnostic.py       # Pydantic: Severity, Check, Recommendation, Report
│   └── snapshot.py         # Pydantic: SnapshotReport, Hardware, Software
└── utils/
    ├── docker.py           # Docker + Compose detection
    ├── gpu.py              # NVIDIA/AMD, CUDA, Vulkan
    ├── logging.py          # Structured JSON logger with rotation (v0.3.0)
    ├── ollama.py           # Ollama version + model listing
    ├── recommendations.py  # Intelligent recommendation engine
    └── system.py           # OS, CPU, RAM, disk info
```

Todos los datos fluyen a través de modelos Pydantic, lo que permite:
- Renderizado consistente en cualquier formato
- Validación de tipos
- Serialización JSON nativa
- Preparación para FastAPI backend y GUI

## Tech Stack

| Componente | Tecnología |
|-----------|-----------|
| CLI Framework | [Typer](https://typer.tiangolo.com/) |
| Terminal UI | [Rich](https://rich.readthedocs.io/) |
| Data Models | [Pydantic](https://docs.pydantic.dev/) v2 |
| System Info | [psutil](https://psulib.org/) |
| HTTP Client | [httpx](https://www.python-httpx.org/) |
| Build System | [Hatch](https://hatch.pypa.io/) |

## Roadmap

### v0.3.0 — Observabilidad ✅
- ✅ `devmind snapshot` — Exportar estado completo a JSON/YAML
- ✅ `devmind benchmark ollama` — Medir tokens/s, RAM, latencia con streaming
- ✅ Logs estructurados JSON en `~/.devmind/logs/` con rotación

### v0.4.0 — Ecosistema ✅
- ✅ `devmind setup local-llm` — Perfil: Ollama + OpenWebUI
- ✅ `devmind setup ai-dev` — Perfil: Docker + Ollama + Jupyter + deps
- ✅ `devmind setup rag-lab` — Perfil: Ollama + ChromaDB + FastAPI
- ✅ `devmind explain` — Explicaciones en profundidad (ram, gpu, python, ollama, docker)
- ✅ `devmind history` — Historial de actividad con filtro por tipo
- ✅ `--dry-run` para todos los perfiles de setup
- ✅ Templates adaptados al hardware detectado

### v0.5.0 — Plataforma
- FastAPI backend (REST API usando modelos Pydantic existentes)
- Control Center desktop (Tauri + React)
- Health score tracking con gráficos
- Telemetry opcional

### v0.6.0 — Cloud
- DevMind Cloud Dashboard
- Config packs marketplace
- Shared benchmark database

## Requisitos

- Linux (Ubuntu 20.04+, Fedora 38+, Arch Linux, Debian 12+)
- Python 3.11+
- Opcional: NVIDIA GPU + drivers, Docker, Ollama

## Licencia

[Licensed under the Apache License, Version 2.0](LICENSE)

---

<p align="center">
  Hecho con ❤️ para la comunidad Linux/AI
</p>
