<p align="center">
  <img width="600" alt="DevMind Platform" src="https://img.shields.io/badge/DevMind-Platform-00d4ff?style=for-the-badge&labelColor=0a0a1a&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0id2hpdGUiPjxwYXRoIGQ9Ik0xMiAyTDIgN2wxMCA1IDEwLTV6TTIgN2wxMCA1IDEwLTUtMTAgNXptMCAwTDIgMTJsMTAtNSAxMCA1LTIgN3ptMCAwTDIgMTdsMTAtNSAxMCA1LTIgN3oiLz48L3N2Zz4=">
  <br/>
  <strong>Linux-first AI environment diagnostics, observability & automation</strong>
  <br/>
  <br/>
  <a href="https://pypi.org/project/devmind/"><img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"></a>
  <a href="https://pypi.org/project/devmind/"><img src="https://img.shields.io/badge/pip_install-devmind-00d4ff?style=flat-square" alt="PyPI"></a>
  <a href="https://github.com/eminem5410/devmind-platform/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-Apache_2.0-blue?style=flat-square" alt="License"></a>
  <a href="https://github.com/eminem5410/devmind-platform/releases"><img src="https://img.shields.io/badge/Version-0.7.0-00d4ff?style=flat-square" alt="Version"></a>
  <img src="https://img.shields.io/badge/Linux-Ready-FCC624?style=flat-square&logo=linux&logoColor=black" alt="Linux">
  <img src="https://img.shields.io/badge/API-FastAPI-009688?style=flat-square" alt="FastAPI">
  <img src="https://img.shields.io/badge/GUI-Pico_CSS-9CF">
</p>

---

> *"Diagnosticar impresiona. Reparar automaticamente enamora. Observar es comprender. Servir es integrar. Visualizar es comprender."*

DevMind es una CLI que **diagnostica, recomienda, repara, observa, configura, explica y expone** tu entorno de desarrollo AI en Linux. Detecta tu hardware, verifica herramientas, calcula un health score, repara problemas automaticamente, exporta snapshots, benchmarkea modelos locales, genera ambientes completos con perfiles predefinidos, explica warnings en profundidad, hace seguimiento de todo tu historial de actividad, expone todo via API REST con persistencia en SQLite, y ahora incluye un **Dashboard Web GUI** con 7 paginas interactivas.

## Demo (v0.7.0 — Diagnostics + Benchmarks + Cost Intelligence)

<a href="https://asciinema.org/a/hAxWIC5ohtFpFXZm" target="_blank"><img src="https://asciinema.org/a/hAxWIC5ohtFpFXZm.svg" width="720" alt="DevMind v0.7.0 Demo"/></a>

## Por que DevMind

Configurar un entorno de IA en Linux es fragmentado: drivers NVIDIA, CUDA, Ollama, Docker, Python versions, RAM limits, modelos... DevMind unifica todo eso en un flujo inteligente:

```
Diagnosticar  →  Recomendar  →  Reparar  →  Observar  →  Configurar  →  Explicar  →  Servir  →  Visualizar
```

## Instalacion

```bash
# Desde PyPI (recomendado)
pip install devmind

# O clonar el repo
git clone https://github.com/eminem5410/devmind-platform.git
cd devmind-platform
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Quick Start

```bash
# Diagnosticar tu sistema completo
devmind doctor

# Levantar el Dashboard Web + API REST
devmind serve
# → Dashboard: http://localhost:8080
# → Swagger UI: http://localhost:8080/docs

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
devmind history -d               # Evolucion del health score

# Exportar estado del sistema a JSON
devmind snapshot -o state.json

# Reparar todo automaticamente
devmind repair all
```

## Dashboard Web (v0.6.0)

DevMind ahora incluye un dashboard web interactivo accesible desde el navegador. Se levanta automaticamente con `devmind serve` y consume los mismos endpoints REST.

```bash
devmind serve
# → http://localhost:8080
```

### Paginas disponibles

| Pagina | URL | Descripcion |
|--------|-----|-------------|
| **Dashboard** | `/` | Vista general: health score, sistema, actividad reciente, quick actions |
| **Doctor** | `/doctor` | Diagnostico completo con checks detallados, recomendaciones y severity |
| **Snapshots** | `/snapshots` | Captura y visualiza estado del hardware, software y red |
| **Benchmarks** | `/benchmarks` | Ejecuta benchmarks Ollama con graficos de rendimiento (Chart.js) |
| **Setup** | `/setup` | Explora y genera perfiles de configuracion con preview de archivos |
| **History** | `/history` | Historial completo con tabs: Doctors, Benchmarks, Snapshots |
| **Explain** | `/explain` | Conceptos de IA explicados en profundidad (5 topics) |

### Stack del Dashboard

| Componente | Tecnologia | Por que |
|-----------|-----------|---------|
| Templates | Jinja2 + herencia | Server-side rendering, sin Node.js |
| Estilos | Pico CSS (CDN) | Dark theme, responsive, sin build step |
| Graficos | Chart.js (CDN) | Barras para benchmarks historicos |
| Interactividad | HTMX + vanilla JS | Actualizaciones parciales sin recarga |

### Capturas

**Dashboard** — Health score, stats del sistema y actividad reciente.

**Benchmarks** — Ejecucion con graficos, tabla de resultados e historial con Chart.js.

**History** — Tabs para filtrar diagnosticos, benchmarks y snapshots.

## API REST (v0.5.0+)

Todos los endpoints JSON siguen disponibles junto con las paginas HTML. Ideal para integraciones, CI/CD, GUIs y herramientas propias.

### Endpoints JSON

| Method | Endpoint | Descripcion |
|--------|----------|-------------|
| GET | `/api/health` | Health check del servicio |
| GET | `/api/version` | Version de la API |
| GET | `/api/doctor` | Diagnostico completo (JSON) |
| GET | `/api/snapshot` | Snapshot del sistema (JSON) |
| POST | `/api/benchmark/ollama` | Benchmark de modelo Ollama |
| GET | `/api/setup/profiles` | Lista perfiles disponibles |
| POST | `/api/setup/{profile}` | Genera archivos de un perfil |
| GET | `/api/history` | Historial completo (SQLite) |
| GET | `/api/history/doctors` | Historial de diagnosticos |
| GET | `/api/history/benchmarks` | Historial de benchmarks |
| GET | `/api/history/snapshots` | Historial de snapshots |
| GET | `/api/explain` | Topics disponibles |
| GET | `/api/explain/{topic}` | Explicacion de un topic |

### Ejemplos con curl

```bash
# Diagnostico completo
curl -s http://localhost:8080/api/doctor | jq '.summary'
# {"total_checks": 15, "health_score": 93, "health_label": "Excelente", ...}

# Benchmark de modelo
curl -X POST http://localhost:8080/api/benchmark/ollama \
  -H "Content-Type: application/json" \
  -d '{"model": "phi3:mini", "runs": 3}'
```

### Opciones del servidor

```bash
devmind serve                     # localhost:8080
devmind serve --port 3000         # Puerto custom
devmind serve --host 0.0.0.0      # Todas las interfaces
devmind serve --reload            # Auto-reload (desarrollo)
```

### Persistencia

Los resultados de `/api/doctor`, `/api/snapshot` y `/api/benchmark/ollama` se guardan automaticamente en **SQLite** (`~/.devmind/devmind.db`). Los endpoints `/api/history/*` leen directamente de SQLite para consultas de historial entre sesiones.

## Output real

### `devmind doctor` — Diagnostico completo

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

### `devmind serve` — Dashboard Web + API

```
DevMind API — Server v0.6.0

  Host: 127.0.0.1
  Port: 8080
  Dashboard: http://127.0.0.1:8080
  Docs: http://127.0.0.1:8080/docs
  Redoc: http://127.0.0.1:8080/redoc

INFO:     Uvicorn running on http://127.0.0.1:8080 (Press CTRL+C to quit)
```

### `devmind benchmark ollama` — Rendimiento de modelos

```
╭──────────────────────────────────────────────────────────────────────────╮
│ DevMind Benchmark — Ollama Performance                                   │
╰──────────────────────────────────────────────────────────────────────────╯

  Run 1 — phi3:mini

  Throughput                4.70 tokens/s (Aceptable)
  TTFT (Time to First Token) 2654 ms
  Total time                26154 ms
  Tokens generados          579
  RAM pico Ollama           3700 MB

Resumen
  Benchmarks OK             3/3
  Avg throughput            4.70 tokens/s
  Avg TTFT                  2654 ms
  Avg RAM pico              3700 MB
```

## Comandos

### Diagnostico y reparacion

| Comando | Descripcion |
|---------|-------------|
| `devmind doctor` | Diagnostico completo con severity, health score y recomendaciones |
| `devmind doctor --compact` | Output de 10 lineas para CI y scripting |
| `devmind doctor --json` | Output JSON estructurado para APIs, GUIs, telemetry |
| `devmind repair ollama` | Instala, inicia Ollama y descarga modelo recomendado |
| `devmind repair docker` | Inicia daemon, instala Compose, verifica permisos |
| `devmind repair all` | Ejecuta todas las reparaciones en secuencia |

### Observabilidad

| Comando | Descripcion |
|---------|-------------|
| `devmind snapshot` | Exporta estado completo del sistema (terminal) |
| `devmind snapshot -o state.json` | Guardar snapshot a archivo JSON |
| `devmind snapshot -o state.yaml` | Guardar snapshot a archivo YAML |
| `devmind snapshot --json` | Snapshot como JSON por stdout |
| `devmind snapshot -c` | Snapshot compacto de 6 lineas |
| `devmind benchmark ollama` | Benchmark de modelos Ollama (tokens/s, TTFT, RAM) |
| `devmind benchmark ollama --runs 3` | 3 runs y promedia resultados |
| `devmind benchmark ollama -m phi3:mini` | Benchmark un modelo especifico |
| `devmind benchmark ollama -c` | Benchmark compacto de 1 linea |
| `devmind benchmark ollama --json` | Benchmark como JSON estructurado |

### Ecosistema

| Comando | Descripcion |
|---------|-------------|
| `devmind setup` | Lista perfiles disponibles |
| `devmind setup local-llm` | Chat local: Ollama + OpenWebUI |
| `devmind setup ai-dev` | Entorno AI: Docker + Ollama + Jupyter + dependencias |
| `devmind setup rag-lab` | Stack RAG: Ollama + ChromaDB + FastAPI template |
| `devmind setup <perfil> --dry-run` | Simula sin escribir archivos |
| `devmind setup <perfil> --force` | Sobreescribe archivos existentes |
| `devmind explain` | Explica warnings del ultimo `devmind doctor` |
| `devmind explain ram` | Deep dive: RAM y modelos de IA |
| `devmind explain gpu` | Deep dive: GPUs para IA, VRAM, presupuesto |
| `devmind explain python` | Deep dive: Versiones Python y compatibilidad |
| `devmind explain ollama` | Deep dive: Ollama, modelos, API |
| `devmind explain docker` | Deep dive: Docker para entornos IA |
| `devmind history` | Muestra historial de actividad reciente |
| `devmind history -b` | Historial de benchmarks con promedios |
| `devmind history -d` | Evolucion del health score entre diagnosticos |
| `devmind history -n 50` | Ultimos 50 eventos |
| `devmind history --json` | Historial como JSON estructurado |

### API REST + Dashboard Web

| Comando | Descripcion |
|---------|-------------|
| `devmind serve` | Levanta Dashboard + API REST en localhost:8080 |
| `devmind serve --port 3000` | Puerto custom |
| `devmind serve --host 0.0.0.0` | Escuchar en todas las interfaces |
| `devmind serve --reload` | Auto-reload para desarrollo |

### Herramientas

| Comando | Descripcion |
|---------|-------------|
| `devmind gpu` | Analisis detallado de GPU, drivers CUDA y Vulkan |
| `devmind init` | Scaffolding interactivo de proyectos AI |

## Features

### Cost Intelligence (v0.7.0)
Compara el costo de inferencia local contra 32 modelos de API en 11 providers. Calcula ROI mensual considerando throughput real (auto-detectado del último benchmark), ratio de output/cache, tokens diarios y costo eléctrico estimado. Soporta exportación a 5 formatos: JSON, CSV, HTML (auto-contenido con tema oscuro), Markdown y YAML.


### Dashboard Web (v0.6.0)
Interfaz grafica accesible desde el navegador con 7 paginas: Dashboard con health score y stats, Doctor con checks detallados y recomendaciones, Snapshots con hardware/software/red, Benchmarks con graficos Chart.js e historial, Setup con preview de perfiles, History con tabs filtrables, y Explain con contenido educativo. Todo server-side con Jinja2 + Pico CSS, sin necesidad de Node.js ni build tools.

### Health Score
Puntuacion 0-100 que evalua la preparacion de tu sistema para IA, basada en todos los checks realizados. Se visualiza con barra de progreso y etiqueta (Excelente/Bueno/Aceptable/Necesita atencion/Critico).

### Severity Levels
Cada check tiene un nivel de severidad: `INFO`, `WARNING`, `ERROR`, `CRITICAL`. Permite filtrar, colorear y priorizar issues para UIs, APIs y repair engines.

### Recomendaciones inteligentes
El motor analiza tu hardware y software para generar recomendaciones contextuales. Con 7.1 GB RAM recomienda modelos 1B-4B; con GPU NVIDIA recomienda `llama3.1:8b`; detecta Python 3.14 y sugiere 3.12 LTS.

### Auto-repair
Repara automaticamente problemas detectados: instala e inicia Ollama, descarga el modelo optimo segun tu hardware, verifica Docker daemon y Compose.

### API REST + SQLite
Servidor FastAPI que expone toda la funcionalidad como endpoints REST. Incluye CORS, Swagger UI, ReDoc y persistencia automatica en SQLite (`~/.devmind/devmind.db`). Cada `/api/doctor`, `/api/snapshot` y `/api/benchmark/ollama` queda grabado para consultas de historial entre sesiones.

### Setup Profiles
Genera stacks completos de desarrollo AI con un solo comando. Los templates se adaptan a tu hardware (RAM, GPU) para recomendar el modelo optimo y configurar limites de recursos. Tres perfiles: `local-llm`, `ai-dev`, `rag-lab`.

### Explain Mode
Explica en profundidad los warnings del doctor y temas clave de IA. Con topic especifico (`ram`, `gpu`, `python`, `ollama`, `docker`), muestra guias completas con tablas comparativas, comandos y recomendaciones de hardware.

### History
Historial completo de actividad desde SQLite. Filtra por tipo: diagnosticos, benchmarks o snapshots. Muestra tablas con evolucion del health score, promedios de throughput y tendencias.

### Snapshot
Exporta el estado completo del sistema a JSON o YAML. Incluye hardware (CPU, RAM, GPU, disco), software (OS, Python, Docker, Ollama, Git) y red. Ideal para compartir en issues, comparar antes/despues, y debugging remoto.

### Benchmark
Mide rendimiento real de modelos Ollama usando la API de streaming: tokens/s (throughput), TTFT (time to first token), RAM pico consumida, duracion total. Color coding de rendimiento y tips para optimizar.

### 3 modos de output
Un solo modelo de datos (Pydantic), tres renderizadores:
- **Rich**: Terminal interactiva con colores, paneles y recomendaciones
- **Compact**: 10 lineas para CI, scripts y quick checks
- **JSON**: Estructura completa para APIs, GUIs, telemetry y pipelines

## Arquitectura

```
src/devmind/
├── cli.py                  # Typer entry point (10 comandos)
├── api/                    # FastAPI REST server + Web GUI
│   ├── main.py             # App con CORS + lifespan + static files
│   ├── routes/
│   │   ├── doctor.py       # GET /api/doctor
│   │   ├── snapshot.py     # GET /api/snapshot
│   │   ├── benchmark.py    # POST /api/benchmark/ollama
│   │   ├── setup.py        # GET /api/setup/profiles, POST /api/setup/{profile}
│   │   ├── history.py      # GET /api/history/*
│   │   ├── explain.py      # GET /api/explain/*
│   │   └── web.py          # HTML pages (Dashboard, Doctor, Snapshots, ...)
│   ├── templates/          # Jinja2 HTML templates (v0.6.0)
│   │   ├── base.html       # Layout base con nav + footer + Pico CSS
│   │   ├── dashboard.html  # Vista general con health score
│   │   ├── doctor.html     # Diagnostico con checks y recomendaciones
│   │   ├── snapshots.html  # Hardware, software, red
│   │   ├── benchmarks.html # Charts Chart.js + historial
│   │   ├── setup.html      # Perfiles con preview de archivos
│   │   ├── history.html    # Tabs filtrables
│   │   └── explain.html    # Topics educativos
│   └── static/             # Archivos estaticos
├── db/                     # SQLAlchemy ORM + SQLite
│   ├── models.py           # DoctorRunRecord, BenchmarkRunRecord, SnapshotRecord
│   └── database.py         # Engine, session factory, init_db
├── commands/
│   ├── benchmark.py        # Ollama performance benchmark
│   ├── doctor.py           # Diagnostico con severity + health score
│   ├── explain.py          # Deep dive explanations
│   ├── gpu_check.py        # Analisis detallado de GPU
│   ├── history.py          # Activity history from logs
│   ├── init_cmd.py         # Scaffolding de proyectos AI
│   ├── repair.py           # Auto-repair engine
│   ├── serve.py            # CLI launcher para API REST
│   ├── setup.py            # Setup profiles orchestrator
│   └── snapshot.py         # System snapshot export
├── data/
│   └── profiles/
│       └── __init__.py     # Profile templates + generators
├── models/
│   ├── benchmark.py        # Pydantic: BenchmarkResult, BenchmarkReport
│   ├── diagnostic.py       # Pydantic: Severity, Check, Recommendation, Report
│   └── snapshot.py         # Pydantic: SnapshotReport, Hardware, Software
└── utils/
    ├── docker.py           # Docker + Compose detection
    ├── gpu.py              # NVIDIA/AMD, CUDA, Vulkan
    ├── logging.py          # Structured JSON logger with rotation
    ├── ollama.py           # Ollama version + model listing
    ├── recommendations.py  # Intelligent recommendation engine
    └── system.py           # OS, CPU, RAM, disk info
```

Todos los datos fluyen a traves de modelos Pydantic, lo que permite:
- Renderizado consistente en cualquier formato (terminal, JSON, HTML)
- Validacion de tipos
- Serializacion JSON nativa
- Reutilizacion directa en la API REST y templates web

## Tech Stack

| Componente | Tecnologia |
|-----------|-----------|
| CLI Framework | [Typer](https://typer.tiangolo.com/) |
| Terminal UI | [Rich](https://rich.readthedocs.io/) |
| Data Models | [Pydantic](https://docs.pydantic.dev/) v2 |
| REST API | [FastAPI](https://fastapi.tiangolo.com/) |
| Database | [SQLAlchemy](https://www.sqlalchemy.org/) + SQLite |
| Web Templates | [Jinja2](https://jinja.palletsprojects.com/) |
| CSS Framework | [Pico CSS](https://picocss.com/) |
| Charts | [Chart.js](https://www.chartjs.org/) |
| Server | [Uvicorn](https://www.uvicorn.org/) |
| System Info | [psutil](https://psulib.org/) |
| HTTP Client | [httpx](https://www.python-httpx.org/) |
| Build System | [Hatch](https://hatch.pypa.io/) |

## Roadmap

### v0.1.0 — Diagnostics ✅
- ✅ `devmind doctor` — Health score, severity, recomendaciones
- ✅ `devmind repair` — Reparacion automatica de Ollama y Docker

### v0.2.0 — Benchmarks ✅
- ✅ `devmind benchmark ollama` — Medir tokens/s, RAM, latencia

### v0.3.0 — Observabilidad ✅
- ✅ `devmind snapshot` — Exportar estado completo a JSON/YAML
- ✅ `devmind benchmark ollama` — Medir tokens/s, RAM, latencia con streaming
- ✅ Logs estructurados JSON en `~/.devmind/logs/` con rotacion

### v0.4.0 — Ecosistema ✅
- ✅ `devmind setup local-llm` — Perfil: Ollama + OpenWebUI
- ✅ `devmind setup ai-dev` — Perfil: Docker + Ollama + Jupyter + deps
- ✅ `devmind setup rag-lab` — Perfil: Ollama + ChromaDB + FastAPI
- ✅ `devmind explain` — Explicaciones en profundidad
- ✅ `devmind history` — Historial de actividad con filtro por tipo

### v0.5.0 — API REST ✅
- ✅ `devmind serve` — Servidor FastAPI en localhost:8080
- ✅ 13 endpoints REST (doctor, snapshot, benchmark, setup, history, explain)
- ✅ Swagger UI + ReDoc
- ✅ Persistencia SQLite (`~/.devmind/devmind.db`)
- ✅ CORS habilitado para desarrollo
- ✅ Publicado en [PyPI](https://pypi.org/project/devmind/)

### v0.6.0 — GUI Dashboard ✅
- ✅ Dashboard Web con 7 paginas interactivas
- ✅ Jinja2 templates + Pico CSS (dark theme)
- ✅ Chart.js para graficos de benchmarks
- ✅ HTMX para interactividad sin recarga
- ✅ Server-side rendering (no Node.js)
- ✅ Publicado en [PyPI](https://pypi.org/project/devmind/0.6.0/)

### v0.7.0 — Cost Intelligence ✅
✅ devmind compare — Comparar costo local vs 32 modelos API
✅ 11 providers: OpenAI, Anthropic, Google, DeepSeek, Groq, Mistral, Cerebras, Together AI, OpenRouter, xAI, Fireworks
✅ ROI calculator: costo eléctrico local vs API más barata
✅ Auto-detección de TPS desde último benchmark (SQLite)
✅ 5 formatos de exportación: JSON, CSV, HTML, Markdown, YAML
✅ API endpoints: /api/compare, /api/compare/providers
✅ Página web /compare con filtros interactivos y sliders

### v0.8.0 — Attention Benchmarks
devmind benchmark attention — Benchmark de ThriftAttention (FP4/FP16 mixed precision)
devmind forecast — Predicción de costo mensual por volumen
Detección de hardware FP4 en devmind doctor
devmind explain attention-precision — Deep dive en precisiones de atención

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
