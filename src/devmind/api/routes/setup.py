"""
Route: GET /api/setup/profiles, POST /api/setup/{profile}
Lista perfiles disponibles y genera un perfil de setup.
"""

from __future__ import annotations

import time
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from devmind.data.profiles import get_available_profiles, generate_profile
from devmind.utils.docker import check_docker
from devmind.utils.ollama import check_ollama
from devmind.utils.system import get_system_info
from devmind.utils.logging import logger

router = APIRouter(tags=["setup"])


class SetupRequest(BaseModel):
    """Request body para generar un perfil."""
    force: bool = False
    dry_run: bool = False


@router.get("/api/setup/profiles")
async def api_setup_profiles():
    """Lista los perfiles disponibles con metadata."""
    return {"profiles": get_available_profiles()}


@router.post("/api/setup/{profile_name}")
async def api_setup_profile(profile_name: str, req: SetupRequest = SetupRequest()):
    """Genera un perfil de setup y retorna los archivos como JSON."""
    start_time = time.time()

    # 1. Verificar perfil existe
    profiles = get_available_profiles()
    profile_names = [p["name"] for p in profiles]
    if profile_name not in profile_names:
        raise HTTPException(
            status_code=404,
            detail=f"Perfil desconocido: {profile_name}. Disponibles: {', '.join(profile_names)}",
        )

    # 2. Verificar prerequisitos
    issues = _check_prerequisites(profile_name)
    if issues:
        raise HTTPException(status_code=400, detail={"issues": issues})

    # 3. Obtener datos del sistema
    sys_info = get_system_info()
    ollama = check_ollama()
    ram_gb = sys_info.ram_total_gb or 4.0
    has_gpu = False  # Se detectaria con GPU utils

    # 4. Generar perfil
    try:
        profile = generate_profile(
            name=profile_name,
            ram_gb=ram_gb,
            has_gpu=has_gpu,
            ollama_version=ollama.version if ollama.installed else None,
        )
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

    # 5. Preparar respuesta
    files = {}
    for filename, content in profile.files.items():
        files[filename] = {
            "content": content,
            "size_bytes": len(content),
        }

    result = {
        "profile": profile_name,
        "description": profile.description,
        "hardware": {
            "cpu": sys_info.cpu_name,
            "cpu_cores": sys_info.cpu_cores,
            "ram_gb": ram_gb,
        },
        "files": files,
        "post_setup_commands": profile.post_setup_commands,
        "dry_run": req.dry_run,
    }

    duration = time.time() - start_time
    logger.command_end("api_setup", duration)

    return result


def _check_prerequisites(profile_name: str) -> list[str]:
    """Verifica prerequisitos y retorna lista de issues."""
    issues = []
    docker = check_docker()
    ollama = check_ollama()

    if not docker.installed:
        issues.append("Docker no esta instalado")
    elif not docker.running:
        issues.append("Docker daemon no esta ejecutando")

    if profile_name in ("ai-dev", "rag-lab"):
        if not ollama.installed:
            issues.append("Ollama no esta instalado")
        elif not ollama.running:
            issues.append("Ollama no esta ejecutando")

    return issues
