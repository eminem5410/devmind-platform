"""
Routes: Paginas HTML del dashboard web.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader

router = APIRouter(tags=["web"])

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=True)


def render(name: str, request: Request) -> HTMLResponse:
    template = env.get_template(name)
    html = template.render(request=request)
    return HTMLResponse(html)


@router.get("/", response_class=HTMLResponse)
async def page_dashboard(request: Request):
    return render("dashboard.html", request)


@router.get("/doctor", response_class=HTMLResponse)
async def page_doctor(request: Request):
    return render("doctor.html", request)


@router.get("/snapshots", response_class=HTMLResponse)
async def page_snapshots(request: Request):
    return render("snapshots.html", request)


@router.get("/benchmarks", response_class=HTMLResponse)
async def page_benchmarks(request: Request):
    return render("benchmarks.html", request)


@router.get("/setup", response_class=HTMLResponse)
async def page_setup(request: Request):
    return render("setup.html", request)


@router.get("/history", response_class=HTMLResponse)
async def page_history(request: Request):
    return render("history.html", request)


@router.get("/explain", response_class=HTMLResponse)
async def page_explain(request: Request):
    return render("explain.html", request)
