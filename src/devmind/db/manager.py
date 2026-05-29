"""
SQLite Database Manager for DevMind.

Stores benchmark results and command history in ~/.devmind/devmind.db
"""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

DEVMIND_HOME = Path.home() / ".devmind"
DB_PATH = DEVMIND_HOME / "devmind.db"


def _ensure_dir() -> None:
    """Creates ~/.devmind if needed."""
    DEVMIND_HOME.mkdir(parents=True, exist_ok=True)


def get_connection() -> sqlite3.Connection:
    """Returns a connection to the DevMind SQLite database."""
    _ensure_dir()
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db() -> None:
    """Creates all tables if they do not exist."""
    _ensure_dir()
    conn = get_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS llm_benchmarks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL DEFAULT (datetime('now')),
            provider TEXT NOT NULL,
            model TEXT NOT NULL,
            prompt TEXT DEFAULT '',
            prompt_tokens INTEGER DEFAULT 0,
            response_tokens INTEGER DEFAULT 0,
            tokens_per_sec REAL DEFAULT 0.0,
            ttft_ms REAL DEFAULT 0.0,
            total_time_ms REAL DEFAULT 0.0,
            quality_score REAL DEFAULT 0.0,
            quality_completeness REAL DEFAULT 0.0,
            quality_clarity REAL DEFAULT 0.0,
            quality_structure REAL DEFAULT 0.0,
            quality_vocabulary REAL DEFAULT 0.0,
            cost_usd REAL DEFAULT 0.0,
            success INTEGER DEFAULT 1,
            error TEXT DEFAULT ''
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS command_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL DEFAULT (datetime('now')),
            command TEXT NOT NULL,
            duration_s REAL DEFAULT 0.0,
            success INTEGER DEFAULT 1,
            metadata TEXT DEFAULT '{}'
        )
    """)

    conn.commit()
    conn.close()


def save_llm_benchmark(
    provider: str,
    model: str,
    prompt: str = "",
    prompt_tokens: int = 0,
    response_tokens: int = 0,
    tokens_per_sec: float = 0.0,
    ttft_ms: float = 0.0,
    total_time_ms: float = 0.0,
    quality_score: float = 0.0,
    quality_completeness: float = 0.0,
    quality_clarity: float = 0.0,
    quality_structure: float = 0.0,
    quality_vocabulary: float = 0.0,
    cost_usd: float = 0.0,
    success: bool = True,
    error: str = "",
) -> int:
    """Saves an LLM benchmark result to SQLite. Returns the row ID."""
    init_db()
    conn = get_connection()
    cursor = conn.execute(
        """INSERT INTO llm_benchmarks
           (timestamp, provider, model, prompt, prompt_tokens, response_tokens,
            tokens_per_sec, ttft_ms, total_time_ms,
            quality_score, quality_completeness, quality_clarity,
            quality_structure, quality_vocabulary, cost_usd, success, error)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            datetime.now(timezone.utc).isoformat(),
            provider, model, prompt[:200],
            prompt_tokens, response_tokens,
            tokens_per_sec, ttft_ms, total_time_ms,
            quality_score, quality_completeness, quality_clarity,
            quality_structure, quality_vocabulary, cost_usd,
            1 if success else 0, error,
        ),
    )
    row_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return row_id


def get_llm_benchmarks(
    limit: int = 50,
    provider: Optional[str] = None,
    model: Optional[str] = None,
) -> list[dict]:
    """Retrieves LLM benchmarks from SQLite."""
    init_db()
    conn = get_connection()

    query = "SELECT * FROM llm_benchmarks"
    params = []

    conditions = []
    if provider:
        conditions.append("provider = ?")
        params.append(provider)
    if model:
        conditions.append("model LIKE ?")
        params.append("%" + model + "%")

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)

    rows = conn.execute(query, params).fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_llm_benchmark_stats() -> dict:
    """Returns aggregate stats for LLM benchmarks."""
    init_db()
    conn = get_connection()

    row = conn.execute("""
        SELECT
            COUNT(*) as total_runs,
            COUNT(CASE WHEN success = 1 THEN 1 END) as successful,
            AVG(tokens_per_sec) as avg_tps,
            MAX(tokens_per_sec) as max_tps,
            MIN(tokens_per_sec) as min_tps,
            AVG(ttft_ms) as avg_ttft,
            AVG(quality_score) as avg_quality,
            COUNT(DISTINCT provider) as providers,
            COUNT(DISTINCT model) as models
        FROM llm_benchmarks
        WHERE success = 1
    """).fetchone()

    conn.close()

    if row and row["total_runs"] > 0:
        return dict(row)
    return {}


def save_command_history(
    command: str,
    duration_s: float = 0.0,
    success: bool = True,
    metadata: Optional[dict] = None,
) -> int:
    """Saves a command execution to history."""
    init_db()
    conn = get_connection()
    cursor = conn.execute(
        """INSERT INTO command_history (timestamp, command, duration_s, success, metadata)
           VALUES (?, ?, ?, ?, ?)""",
        (
            datetime.now(timezone.utc).isoformat(),
            command, duration_s,
            1 if success else 0,
            json.dumps(metadata or {}, default=str),
        ),
    )
    row_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return row_id
