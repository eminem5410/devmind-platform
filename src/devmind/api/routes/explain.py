"""
Route: GET /api/explain, GET /api/explain/{topic}
Explica topics de IA en profundidad (contenido Markdown como JSON).
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from devmind.commands.explain import EXPLAINATIONS, get_system_info_safe

router = APIRouter(tags=["explain"])


@router.get("/api/explain")
async def api_explain_topics():
    """Lista los topics disponibles para explicar."""
    topics = list(EXPLAINATIONS.keys())
    return {"topics": topics}


@router.get("/api/explain/{topic}")
async def api_explain_topic(topic: str):
    """Retorna la explicacion de un topic."""
    key = topic.lower().strip()

    if key not in EXPLAINATIONS:
        raise HTTPException(
            status_code=404,
            detail=f"Topic desconocido: {topic}. Disponibles: {', '.join(EXPLAINATIONS.keys())}",
        )

    content = EXPLAINATIONS[key]

    # Reemplazar placeholders con datos reales del sistema
    sys_info = get_system_info_safe()
    content = content.replace("{python_version}", sys_info.get("python", "desconocida"))

    return {
        "topic": key,
        "content": content,
    }
