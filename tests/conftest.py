"""
Shared fixtures for DevMind API tests.

Provides a test SQLite database, DB session with transaction rollback,
and a FastAPI TestClient with dependency overrides.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from devmind.api.main import app
from devmind.db import database
from devmind.db.models import Base

# ── Test database URL ──────────────────────────────────────────────────────

TEST_DB_PATH = "/tmp/test_devmind.db"
TEST_DB_URL = f"sqlite:///{TEST_DB_PATH}"


# ── Session-scoped engine: create tables once ───────────────────────────────

@pytest.fixture(scope="session")
def test_engine():
    """Create a test SQLite engine, build all tables, and tear down at end."""
    # Remove stale DB from a previous run
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

    engine = create_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False},
        echo=False,
    )
    Base.metadata.create_all(bind=engine)
    yield engine

    engine.dispose()
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)


# ── Function-scoped DB session with rollback ────────────────────────────────

@pytest.fixture
def db_session(test_engine):
    """Provide a transactional DB session that rolls back after each test."""
    connection = test_engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


# ── TestClient with dependency overrides ────────────────────────────────────

@pytest.fixture
def client(db_session, monkeypatch):
    """FastAPI TestClient that uses the test DB session.

    Also patches ``devmind.db.database.init_db`` to avoid creating
    ``~/.devmind/devmind.db`` during the app lifespan.
    """
    # Prevent init_db from touching the real filesystem
    monkeypatch.setattr(database, "init_db", lambda: None)

    # Override the get_db dependency to yield the test session
    def override_get_db():
        yield db_session

    app.dependency_overrides[database.get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
