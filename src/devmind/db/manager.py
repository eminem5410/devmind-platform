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


    conn.execute("""
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            provider TEXT NOT NULL DEFAULT 'ollama',
            model TEXT NOT NULL DEFAULT 'phi3:mini',
            title TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            tokens INTEGER DEFAULT 0,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
        )
    """)

    # ── FTS5 Full-Text Search ──
    try:
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS chat_fts USING fts5(
                session_id, role, content,
                content=chat_messages, content_rowid=id
            )
        """)
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS chat_fts_ai AFTER INSERT ON chat_messages BEGIN
                INSERT INTO chat_fts(rowid, session_id, role, content)
                VALUES (new.id, new.session_id, new.role, new.content);
            END
        """)
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS chat_fts_ad AFTER DELETE ON chat_messages BEGIN
                INSERT INTO chat_fts(chat_fts, rowid, session_id, role, content)
                VALUES('delete', old.id, old.session_id, old.role, old.content);
            END
        """)
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS chat_fts_au AFTER UPDATE ON chat_messages BEGIN
                INSERT INTO chat_fts(chat_fts, rowid, session_id, role, content)
                VALUES('delete', old.id, old.session_id, old.role, old.content);
                INSERT INTO chat_fts(rowid, session_id, role, content)
                VALUES (new.id, new.session_id, new.role, new.content);
            END
        """)
        # Backfill existing messages if FTS is empty
        fts_count = conn.execute("SELECT COUNT(*) FROM chat_fts").fetchone()[0]
        msg_count = conn.execute("SELECT COUNT(*) FROM chat_messages").fetchone()[0]
        if msg_count > 0 and fts_count == 0:
            conn.execute("""
                INSERT INTO chat_fts(rowid, session_id, role, content)
                SELECT id, session_id, role, content FROM chat_messages
            """)
    except Exception:
        pass  # FTS5 not available (rare)
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

    conn.execute("""
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            provider TEXT NOT NULL DEFAULT 'ollama',
            model TEXT NOT NULL DEFAULT 'phi3:mini',
            title TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            tokens INTEGER DEFAULT 0,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
        )
    """)
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

    conn.execute("""
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            provider TEXT NOT NULL DEFAULT 'ollama',
            model TEXT NOT NULL DEFAULT 'phi3:mini',
            title TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            tokens INTEGER DEFAULT 0,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    conn.close()
    return row_id

# ── Chat Session & Message Functions ──

def create_chat_session(
    provider: str = "ollama",
    model: str = "phi3:mini",
    title: str = "",
) -> int:
    """Creates a new chat session. Returns the session ID."""
    init_db()
    conn = get_connection()
    cursor = conn.execute(
        """INSERT INTO chat_sessions (session_id, provider, model, title, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            __import__("uuid").uuid4().hex[:12],
            provider, model, title,
            datetime.now(timezone.utc).isoformat(),
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    row_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return row_id


def get_chat_session(session_id: int) -> Optional[dict]:
    """Get a chat session by its row ID."""
    init_db()
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM chat_sessions WHERE id = ?", (session_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def list_chat_sessions(limit: int = 20) -> list[dict]:
    """List recent chat sessions."""
    init_db()
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM chat_sessions ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_chat_session(session_id: int, title: str = "", model: str = "") -> None:
    """Update a chat session title or model."""
    init_db()
    conn = get_connection()
    if title:
        conn.execute(
            "UPDATE chat_sessions SET title = ?, updated_at = ? WHERE id = ?",
            (title, datetime.now(timezone.utc).isoformat(), session_id),
        )
    if model:
        conn.execute(
            "UPDATE chat_sessions SET model = ?, updated_at = ? WHERE id = ?",
            (model, datetime.now(timezone.utc).isoformat(), session_id),
        )
    conn.commit()
    conn.close()


def delete_chat_session(session_id: int) -> None:
    """Delete a chat session and all its messages."""
    init_db()
    conn = get_connection()
    conn.execute("DELETE FROM chat_messages WHERE session_id = ?", (session_id,))
    conn.execute("DELETE FROM chat_sessions WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()


def save_chat_message(
    session_id: int,
    role: str,
    content: str,
    tokens: int = 0,
) -> int:
    """Save a chat message. Role: user, assistant, or system."""
    init_db()
    conn = get_connection()
    cursor = conn.execute(
        """INSERT INTO chat_messages (session_id, role, content, tokens, timestamp)
           VALUES (?, ?, ?, ?, ?)""",
        (session_id, role, content[:50000], tokens, datetime.now(timezone.utc).isoformat()),
    )
    row_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return row_id


def get_chat_messages(session_id: int, limit: int = 100) -> list[dict]:
    """Get all messages for a chat session."""
    init_db()
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM chat_messages WHERE session_id = ? ORDER BY id ASC LIMIT ?",
        (session_id, limit),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_chat_message_count(session_id: int) -> int:
    """Count messages in a session."""
    init_db()
    conn = get_connection()
    row = conn.execute(
        "SELECT COUNT(*) as cnt FROM chat_messages WHERE session_id = ?",
        (session_id,),
    ).fetchone()
    conn.close()
    return row["cnt"] if row else 0

# ── Search Functions (FTS5) ──

def search_chat_messages(
    query: str,
    limit: int = 20,
    provider: Optional[str] = None,
    role: Optional[str] = None,
) -> list[dict]:
    """Search chat messages using FTS5 full-text search."""
    init_db()
    conn = get_connection()
    where_clauses = ["chat_fts MATCH ?"]
    params = [query]
    if provider:
        where_clauses.append("s.provider = ?")
        params.append(provider)
    if role:
        where_clauses.append("chat_fts.role = ?")
        params.append(role)
    where_sql = " AND ".join(where_clauses)
    params.append(limit)
    sql = f"""
        SELECT chat_fts.*, s.provider, s.model, s.title as session_title
        FROM chat_fts
        LEFT JOIN chat_sessions s ON chat_fts.session_id = s.id
        WHERE {where_sql}
        ORDER BY rank
        LIMIT ?
    """
    try:
        rows = conn.execute(sql, params).fetchall()
    except Exception:
        rebuild_fts()
        try:
            rows = conn.execute(sql, params).fetchall()
        except Exception:
            rows = []
    conn.close()
    return [dict(row) for row in rows]


def rebuild_fts() -> None:
    """Rebuild FTS5 index from existing chat_messages."""
    init_db()
    conn = get_connection()
    try:
        conn.execute("INSERT INTO chat_fts(chat_fts) VALUES('rebuild')")
        conn.commit()
    except Exception:
        pass
    conn.close()


# ── Stats Functions ──

def get_chat_stats() -> dict:
    """Get aggregate chat statistics."""
    init_db()
    conn = get_connection()
    stats = {}
    row = conn.execute("""
        SELECT
            COUNT(*) as total_sessions,
            COUNT(DISTINCT provider) as providers,
            COUNT(DISTINCT model) as models,
            SUM(
                (SELECT COUNT(*) FROM chat_messages WHERE chat_messages.session_id = chat_sessions.id)
            ) as total_messages
        FROM chat_sessions
    """).fetchone()
    stats["total_sessions"] = row["total_sessions"] or 0
    stats["providers"] = row["providers"] or 0
    stats["models"] = row["models"] or 0
    stats["total_messages"] = row["total_messages"] or 0
    row = conn.execute("""
        SELECT
            COALESCE(SUM(tokens), 0) as total_tokens,
            COALESCE(SUM(CASE WHEN role = 'assistant' THEN tokens ELSE 0 END), 0) as assistant_tokens,
            COALESCE(SUM(CASE WHEN role = 'user' THEN tokens ELSE 0 END), 0) as user_tokens,
            COALESCE(AVG(CASE WHEN role = 'assistant' THEN tokens ELSE 0 END), 0) as avg_response_tokens
        FROM chat_messages
    """).fetchone()
    stats["total_tokens"] = row["total_tokens"] or 0
    stats["assistant_tokens"] = row["assistant_tokens"] or 0
    stats["user_tokens"] = row["user_tokens"] or 0
    stats["avg_response_tokens"] = round(row["avg_response_tokens"], 1) if row["avg_response_tokens"] else 0
    stats["provider_breakdown"] = {}
    rows = conn.execute("""
        SELECT provider, COUNT(*) as sessions
        FROM chat_sessions GROUP BY provider ORDER BY sessions DESC
    """).fetchall()
    for r in rows:
        stats["provider_breakdown"][r["provider"]] = r["sessions"]
    stats["top_models"] = []
    rows = conn.execute("""
        SELECT model, COUNT(*) as sessions
        FROM chat_sessions GROUP BY model ORDER BY sessions DESC LIMIT 5
    """).fetchall()
    for r in rows:
        stats["top_models"].append({"model": r["model"], "sessions": r["sessions"]})
    row = conn.execute("""
        SELECT COUNT(*) as cnt,
               COALESCE(SUM((SELECT COUNT(*) FROM chat_messages WHERE chat_messages.session_id = chat_sessions.id)), 0) as msgs,
               COALESCE(SUM((SELECT SUM(tokens) FROM chat_messages WHERE chat_messages.session_id = chat_sessions.id)), 0) as tokens
        FROM chat_sessions
        WHERE created_at >= datetime('now', '-7 days')
    """).fetchone()
    stats["sessions_7d"] = row["cnt"] or 0
    stats["messages_7d"] = row["msgs"] or 0
    stats["tokens_7d"] = row["tokens"] or 0
    row = conn.execute("""
        SELECT session_id, provider, model, title, created_at
        FROM chat_sessions ORDER BY id DESC LIMIT 1
    """).fetchone()
    if row:
        stats["latest_session"] = dict(row)
    conn.close()
    return stats


def get_daily_activity(days: int = 7) -> list[dict]:
    """Get daily message/token counts for the last N days."""
    init_db()
    conn = get_connection()
    rows = conn.execute("""
        SELECT DATE(timestamp) as date, COUNT(*) as messages,
               SUM(tokens) as tokens, COUNT(DISTINCT session_id) as sessions
        FROM chat_messages
        WHERE timestamp >= datetime('now', '-' || ? || ' days')
        GROUP BY DATE(timestamp) ORDER BY date DESC
    """, (days,)).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_session_detail(session_id: int) -> Optional[dict]:
    """Get detailed stats for a single session."""
    init_db()
    conn = get_connection()
    session = conn.execute("SELECT * FROM chat_sessions WHERE id = ?", (session_id,)).fetchone()
    if not session:
        conn.close()
        return None
    row = conn.execute("""
        SELECT COUNT(*) as messages,
               SUM(CASE WHEN role = 'user' THEN 1 ELSE 0 END) as user_messages,
               SUM(CASE WHEN role = 'assistant' THEN 1 ELSE 0 END) as assistant_messages,
               COALESCE(SUM(tokens), 0) as total_tokens,
               MIN(timestamp) as first_message, MAX(timestamp) as last_message
        FROM chat_messages WHERE session_id = ?
    """, (session_id,)).fetchone()
    conn.close()
    result = dict(session)
    result.update({k: row[k] for k in row.keys()})
    return result
