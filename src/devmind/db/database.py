"""
Database engine, session factory e init para DevMind.

La base de datos SQLite se almacena en ~/.devmind/devmind.db
Se inicializa automaticamente al levantar la API.
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from devmind.db.models import Base

# ── Path ────────────────────────────────────────────────────────────────────

DEVMIND_HOME = Path.home() / ".devmind"
DB_PATH = DEVMIND_HOME / "devmind.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"


# ── Engine + Session ────────────────────────────────────────────────────────

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite requiere esto para multithreading
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency para FastAPI: retorna un generador de sesion."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Crea todas las tablas si no existen."""
    DEVMIND_HOME.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
