<p align="center">
  <img width="600" alt="DevMind Platform" src="https://img.shields.io/badge/DevMind-Platform-00d4ff?style=for-the-badge&labelColor=0a0a1a&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0id2hpdGUiPjxwYXRoIGQ9Ik0xMiAyTDIgN2wxMCA1IDEwLTV6TTIgN2wxMCA1IDEwLTUtMTAgNXptMCAwTDIgMTJsMTAtNSAxMCA1LTIgN3ptMCAwTDIgMTdsMTAtNSAxMCA1LTIgN3oiLz48L3N2Zz4=">
  <br/>
  <strong>Linux-first AI environment diagnostics, repair & automation</strong>
  <br/>
  <br/>
  <a href="https://pypi.org/project/devmind/"><img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"></a>
  <a href="https://github.com/eminem5410/devmind-platform/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-Apache_2.0-blue?style=flat-square" alt="License"></a>
  <a href="https://github.com/eminem5410/devmind-platform/releases"><img src="https://img.shields.io/badge/Version-0.2.0-00d4ff?style=flat-square" alt="Version"></a>
  <img src="https://img.shields.io/badge/Linux-Ready-FCC624?style=flat-square&logo=linux&logoColor=black" alt="Linux">
</p>

---

> *"Diagnosticar impresiona. Reparar automáticamente enamora."*

DevMind es una CLI que **diagnostica, recomienda y repara** tu entorno de desarrollo AI en Linux. Detecta tu hardware, verifica herramientas, calcula un health score y repara problemas automáticamente con un solo comando.

## Demo

<a href="https://asciinema.org/a/Pao5xWmKrGC3BfRU" target="_blank"><img src="https://asciinema.org/a/Pao5xWmKrGC3BfRU.svg" width="720" alt="DevMind Demo"/></a>

## Por qué DevMind

Configurar un entorno de IA en Linux es fragmentado: drivers NVIDIA, CUDA, Ollama, Docker, Python versions, RAM limits, modelos... DevMind unifica todo eso en un flujo inteligente:

```
Diagnosticar  →  Recomendar  →  Reparar  →  Verificar
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
  [WARN]   RAM                   3.3 / 7.1 GB (46%)  RAM limitada para modelos grandes
  [INFO]   Disco libre           287.2 GB

GPU / Aceleracion
  [WARN]   GPU Dedicada          N/A  No se detectaron GPUs — CPU-only
  [INFO]   Vulkan                libvulkan detectada

Docker
  [INFO]   Docker                29.4.3
  [INFO]   Docker Daemon         ejecutando
  [INFO]   Docker Compose        v5.1.3

Ollama
  [INFO]   Ollama                0.24.0
  [INFO]   Ollama Server         ejecutando
  [INFO]   Ollama Modelos        phi3:mini

Recomendaciones

  [!] RAM limitada (7.1 GB)
      Con 7.1 GB de RAM, hay restricciones importantes para modelos de IA.
      Se recomienda usar modelos pequenos (1B-4B) como llama3.2:1b, phi3:mini.
      Accion: Considerar upgrade de RAM o usar quantization para modelos grandes

  [!] Python 3.14.4 (version muy reciente)
      PyTorch, TensorFlow y scikit-learn pueden no tener compatibilidad aun.
      Accion: Considerar usar Python 3.12 como version principal para IA

  [i] Vulkan detectado (GPU integrada)
      Vulkan compute shaders disponibles pero rendimiento limitado vs CUDA.

╭──────────────────────────────────────────────────────────────────────────╮
│ 3 advertencia(s) encontradas                                            │
│ 0 reparable(s) automaticamente con 'devmind repair'                     │
╰──────────────────────────────────────────────────────────────────────────╯
```

### `devmind doctor --compact` — CI / Scripting

```
DevMind v0.2.0 | Health: 93/100 (Excelente) | W:3 | E:0
OS: Linux x86_64 | Python: 3.14.4 | CPU: Intel(R) Core(TM) i5-7400 (4c)
RAM: 3.3 / 7.1 GB (46%) | Disk: 287.2 GB
GPU: WARN | CUDA: -- | Vulkan: OK
Docker: OK (29.4.3) | Compose: v5.1.3
Ollama: OK (0.24.0) | Models: phi3:mini
Git: OK | pip: OK
Repairable: 0
Warnings: No se detecto GPU dedicada | RAM limitada (7.1 GB) | Python 3.14.4
```

### `devmind repair ollama` — Auto-repair

```
╭──────────────────────────────────────────────────────────────────────────╮
│ DevMind Repair — Ollama                                                 │
╰──────────────────────────────────────────────────────────────────────────╯

  >>> Verificando instalacion de Ollama...
  OK Ollama 0.24.0 detectado
  >>> Verificando servidor de Ollama...
  OK Servidor de Ollama ejecutando

  No hay modelos instalados.
  Modelo recomendado: phi3:mini
  (Basado en 7.1 GB RAM)

  Modelo a descargar (phi3:mini): ✓
  Descargar phi3:mini? [y/n] (y): y
  >>> Descargando phi3:mini (esto puede tardar minutos)...

pulling manifest
pulling 633fc5be925f: 100% ▕████████████████████████████▏ 2.2 GB
success

  OK Modelo phi3:mini descargado correctamente
  Para probarlo ejecuta: ollama run phi3:mini
```

## Comandos

| Comando | Descripción |
|---------|-------------|
| `devmind` | Lista todos los comandos disponibles |
| `devmind doctor` | Diagnóstico completo con severity, health score y recomendaciones |
| `devmind doctor --compact` | Output de 10 líneas para CI y scripting |
| `devmind doctor --json` | Output JSON estructurado para APIs, GUIs, telemetry |
| `devmind gpu` | Análisis detallado de GPU, drivers CUDA y Vulkan |
| `devmind init` | Scaffolding interactivo de proyectos AI |
| `devmind repair ollama` | Instala, inicia Ollama y descarga modelo recomendado |
| `devmind repair docker` | Inicia daemon, instala Compose, verifica permisos |
| `devmind repair all` | Ejecuta todas las reparaciones en secuencia |

## Features

### Health Score
Puntuación 0-100 que evalúa la preparación de tu sistema para IA, basada en todos los checks realizados. Se visualiza con barra de progreso y etiqueta (Excelente/Bueno/Aceptable/Necesita atención/Crítico).

### Severity Levels
Cada check tiene un nivel de severidad: `INFO`, `WARNING`, `ERROR`, `CRITICAL`. Permite filtrar, colorear y priorizar issues para UIs, APIs y repair engines.

### Recomendaciones inteligentes
El motor analiza tu hardware y software para generar recomendaciones contextuales. Ejemplo: con 7.1 GB RAM recomienda modelos 1B-4B; con GPU NVIDIA recomienda `llama3.1:8b`; detecta Python 3.14 y sugiere 3.12 LTS.

### Auto-repair
Repara automáticamente problemas detectados: instala e inicia Ollama, descarga el modelo óptimo según tu hardware, verifica Docker daemon y Compose.

### 3 modos de output
Un solo modelo de datos (Pydantic), tres renderizadores:
- **Rich**: Terminal interactiva con colores, paneles y recomendaciones
- **Compact**: 10 líneas para CI, scripts y quick checks
- **JSON**: Estructura completa para APIs, GUIs, telemetry y pipelines

## Arquitectura

```
src/devmind/
├── cli.py                  # Typer entry point
├── commands/
│   ├── doctor.py           # Diagnóstico con severity + health score
│   ├── gpu_check.py        # Análisis detallado de GPU
│   ├── init_cmd.py         # Scaffolding de proyectos AI
│   ├── repair.py           # Auto-repair engine
│   └── setup.py            # Setup profiles (upcoming)
├── models/
│   └── diagnostic.py       # Pydantic: Severity, Check, Recommendation, Report
└── utils/
    ├── docker.py           # Docker + Compose detection
    ├── gpu.py              # NVIDIA/AMD, CUDA, Vulkan
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

### v0.3.0 — Observabilidad
- `devmind snapshot` — Exportar estado completo a JSON/YAML
- `devmind benchmark ollama` — Medir tokens/s, RAM, latencia
- Logs estructurados para debugging y rollback

### v0.4.0 — Ecosistema
- `devmind setup ai-dev` / `devmind setup rag-lab` / `devmind setup local-llm` — Perfiles de setup
- `devmind explain` — Explain mode para warnings
- `devmind import env` — Reproducir environments

### v0.5.0 — Plataforma
- FastAPI backend (usando `--json` existente)
- Control Center desktop (Tauri + React)
- Telemetry opcional

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
