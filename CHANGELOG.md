# Changelog

All notable changes to DevMind are documented in this file.

## [0.15.0] — Real-time AI Monitor

### Added
- `devmind monitor` — Real-time AI environment dashboard with live refresh
- `devmind monitor --once` — Single snapshot mode (for scripts)
- `devmind monitor --json` — Structured JSON output
- `devmind monitor --ai` — AI-specific metrics (Ollama RAM, active model, tokens today, system pressure)
- `devmind monitor -i N` — Configurable refresh interval
- Health score (0-100) with color-coded visual bar
- Color-coded resource pressure indicators (green/yellow/red)

### Reuses
- psutil for CPU/RAM/Disk, gpu.py for GPU info, ollama.py for status, docker.py for containers, db/manager.py for daily tokens

## [0.14.0] — Configuration Management + Session Export

### Added
- `devmind config show` — View current configuration (API keys masked)
- `devmind config set` — Change provider, model, API keys, base URLs
- `devmind config reset` — Restore defaults (with confirmation)
- `devmind config validate` — Check Ollama, API keys, Docker status
- `devmind config path` — Show configuration file location
- `devmind export --session N` — Export session as Markdown or JSON
- `devmind export --all` — Export all sessions
- `devmind export --provider` / `--model` — Filter by provider or model
- `devmind export -f md` / `-f json` — Output format selection

## [0.13.0] — Analytics Dashboard + FTS5 Search

### Added
- `devmind stats` — Analytics dashboard (tokens, sessions, providers, models, daily activity)
- `devmind stats -c` — Compact single-line output for scripts
- `devmind stats -d N` — Configurable activity window
- `devmind search "query"` — Full-text search in chat history via SQLite FTS5
- `devmind search -e md -o file.md` — Markdown export with metadata
- FTS5 virtual table with auto-sync triggers (insert/update/delete)
- Auto-backfill of existing messages on first init

### Fixed
- `init_db()` now creates FTS5 table + triggers for existing databases
- FTS5 creation fixed: removed `rowid` from explicit columns (reserved keyword)

## [0.12.0] — Interactive LLM Chat + Setup Wizard

### Added
- `devmind chat` — Interactive streaming chat with Ollama + 4 API providers (Groq, Together, OpenRouter, Fireworks)
- Slash commands: `/model`, `/provider`, `/clear`, `/sessions`, `/info`, `/help`, `/quit`
- Multi-turn conversations with cumulative context
- SQLite persistence: sessions and messages
- `devmind chat --session N` — Resume previous sessions
- `devmind chat --prompt "text"` — Non-interactive mode
- Auto-title from first user message
- `devmind init --interactive` — Setup wizard for API keys, provider, and model
- `~/.devmind/config.toml` — Persistent configuration with API keys
- `config/settings.py` — TOML config management module

## [0.11.0] — SQLite Benchmark History + CI/CD

### Added
- SQLite storage for LLM benchmarks (`devmind/db/manager.py`)
- `devmind llm-benchmark run` — Auto-save results to `~/.devmind/devmind.db`
- `devmind history --llm` — Benchmark history with statistics
- CI/CD: GitHub Actions (Ubuntu + Windows + macOS, Python 3.11-3.13)

## [0.10.0] — LLM Benchmark Suite + Cost Intelligence

### Added
- `devmind llm-benchmark` — Comprehensive LLM benchmarking (local + API)
- `devmind forecast` — 12-month cost projection (API vs local)
- `devmind optimize` — Hardware-aware model/provider recommendations
- Quality scoring system (completeness, clarity, structure, vocabulary)
- TTFT (time to first token) measurement

## [0.9.0] — Web Dashboard GUI

### Added
- FastAPI-based web dashboard with 9 interactive pages
- Pico CSS styling, no Node.js dependency
- Real-time system metrics, benchmark charts, GPU monitoring

## [0.6.0] — API REST Platform

### Added
- `devmind serve` — FastAPI + Uvicorn REST API
- 17 endpoints with SQLite persistence
- Docker and GPU monitoring endpoints

## [0.5.0] — Benchmark Suite

### Added
- `devmind benchmark ollama` — Measure tokens/s, RAM, latency with streaming
- Structured JSON logging with rotation

## [0.4.0] — Ecosystem Detection

### Added
- `devmind snapshot` — Export full system state to JSON/YAML
- `devmind setup` — Predefined environment profiles

## [0.3.0] — Observability

### Added
- Structured JSON logs in `~/.devmind/logs/` with rotation

## [0.2.0] — Benchmarks

### Added
- `devmind benchmark ollama` — Measure tokens/s, RAM, latency

## [0.1.0] — Diagnostics

### Added
- `devmind doctor` — Health score, severity, recommendations
- `devmind repair` — Automatic repair of Ollama and Docker
- `devmind gpu` — GPU, CUDA, and Vulkan detection
- `devmind explain` — In-depth AI topic explanations
