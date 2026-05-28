"""
DevMind API — FastAPI application.

Endpoints:
  GET  /api/health         Health check
  GET  /api/version        Version info
  GET  /api/doctor         Diagnostico completo del sistema
  GET  /api/snapshot       Snapshot del sistema
  POST /api/benchmark/ollama   Benchmark de modelo Ollama
  GET  /api/setup/profiles     Lista perfiles disponibles
  POST /api/setup/{profile}    Genera un perfil de setup
  GET  /api/history            Historial de eventos
  GET  /api/history/benchmarks Historial de benchmarks
  GET  /api/history/doctors    Historial de diagnosticos
  GET  /api/history/snapshots  Historial de snapshots
  GET  /api/explain            Topics disponibles
  GET  /api/explain/{topic}    Explicacion de un topic
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from devmind.db.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan: inicializa la DB al arrancar."""
    init_db()
    yield


app = FastAPI(
    title="DevMind API",
    description="API REST para DevMind Platform — Herramientas CLI para desarrollo de IA",
    version="0.5.0",
    lifespan=lifespan,
)

# CORS: permitir todas las origines para desarrollo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health & Version ────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    """Health check de la API."""
    return {
        "status": "ok",
        "service": "devmind-api",
        "version": "0.5.0",
    }


@app.get("/api/version")
async def version():
    """Version info."""
    return {
        "name": "DevMind Platform",
        "version": "0.5.0",
        "api_version": "v1",
    }


# ── Importar y registrar rutas ──────────────────────────────────────────────

from devmind.api.routes.doctor import router as doctor_router
from devmind.api.routes.snapshot import router as snapshot_router
from devmind.api.routes.benchmark import router as benchmark_router
from devmind.api.routes.setup import router as setup_router
from devmind.api.routes.history import router as history_router
from devmind.api.routes.explain import router as explain_router

app.include_router(doctor_router)
app.include_router(snapshot_router)
app.include_router(benchmark_router)
app.include_router(setup_router)
app.include_router(history_router)
app.include_router(explain_router)
