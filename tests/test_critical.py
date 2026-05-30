"""Critical tests for DevMind commands.

Tests: config, export, stats, search, monitor.
Run: pytest tests/test_critical.py -v
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


# ── Config Tests ──

class TestConfig:
    """Tests for devmind.config module."""

    def test_load_config_returns_dict(self):
        from devmind.config.settings import load_config, DEFAULT_CONFIG
        config = load_config()
        assert isinstance(config, dict)
        assert "default_provider" in config
        assert "providers" in config

    def test_load_config_has_all_providers(self):
        from devmind.config.settings import load_config, PROVIDERS
        config = load_config()
        for prov in PROVIDERS:
            assert prov in config["providers"]

    def test_config_path_exists(self):
        from devmind.config.settings import CONFIG_PATH
        assert str(CONFIG_PATH).endswith("config.toml")

    def test_get_api_key_empty(self):
        from devmind.config.settings import get_api_key
        # groq should be empty by default unless user set it
        key = get_api_key("groq")
        assert isinstance(key, str)

    def test_get_base_url_ollama(self):
        from devmind.config.settings import get_base_url
        url = get_base_url("ollama")
        assert "localhost" in url or "11434" in url

    def test_mask_key_short(self):
        from devmind.commands.config_cmd import _mask_key
        assert _mask_key("") == "[dim]not set[/]"
        assert _mask_key("abc") == "****"

    def test_mask_key_long(self):
        from devmind.commands.config_cmd import _mask_key
        result = _mask_key("sk-1234567890abcdef")
        assert "sk-1" in result
        assert "cdef" in result
        assert "..." in result

    def test_toml_serializer_basic(self):
        from devmind.config.settings import _dict_to_toml, _toml_value
        toml = _toml_value("hello")
        assert toml == '"hello"'
        assert _toml_value(42) == "42"
        assert _toml_value(True) == "true"

    def test_toml_serializer_dict(self):
        from devmind.config.settings import _dict_to_toml
        result = _dict_to_toml({"key": "value", "num": 3})
        assert 'key = "value"' in result
        assert "num = 3" in result

    def test_toml_serializer_nested(self):
        from devmind.config.settings import _dict_to_toml
        result = _dict_to_toml({"providers": {"ollama": {"base_url": "http://localhost:11434"}}})
        assert "[providers.ollama]" in result
        assert 'base_url = "http://localhost:11434"' in result


# ── Database Tests ──

class TestDatabase:
    """Tests for SQLite database operations."""

    def test_init_db_no_error(self):
        from devmind.db.manager import init_db
        init_db()  # Should not raise

    def test_get_connection(self):
        from devmind.db.manager import get_connection
        conn = get_connection()
        assert conn is not None
        conn.close()

    def test_fts_table_exists(self):
        from devmind.db.manager import get_connection
        conn = get_connection()
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        conn.close()
        assert "chat_fts" in tables

    def test_chat_stats_returns_dict(self):
        from devmind.db.manager import get_chat_stats
        stats = get_chat_stats()
        assert isinstance(stats, dict)
        assert "total_sessions" in stats
        assert "total_messages" in stats
        assert "total_tokens" in stats

    def test_daily_activity_returns_list(self):
        from devmind.db.manager import get_daily_activity
        rows = get_daily_activity(days=7)
        assert isinstance(rows, list)

    def test_list_sessions_returns_list(self):
        from devmind.db.manager import list_chat_sessions
        sessions = list_chat_sessions()
        assert isinstance(sessions, list)


# ── Monitor Tests ──

class TestMonitor:
    """Tests for monitor data collection."""

    def test_collect_data_returns_dict(self):
        from devmind.commands.monitor import _collect_data
        data = _collect_data(ai_mode=False)
        assert isinstance(data, dict)
        assert "cpu" in data
        assert "ram_used" in data
        assert "ram_total" in data
        assert "health" in data
        assert "timestamp" in data

    def test_collect_data_ai_mode(self):
        from devmind.commands.monitor import _collect_data
        data = _collect_data(ai_mode=True)
        assert "tokens_today" in data
        assert "pressure" in data
        assert "ollama_ram_gb" in data

    def test_health_score_range(self):
        from devmind.commands.monitor import _collect_data
        data = _collect_data()
        assert 0 <= data["health"] <= 100

    def test_pressure_color(self):
        from devmind.commands.monitor import _pressure_color
        assert _pressure_color(50) == "green"
        assert _pressure_color(75) == "yellow"
        assert _pressure_color(95) == "red"

    def test_render_dashboard(self):
        from devmind.commands.monitor import _collect_data, _render_dashboard
        data = _collect_data()
        panel = _render_dashboard(data)
        assert panel is not None

    def test_render_dashboard_ai(self):
        from devmind.commands.monitor import _collect_data, _render_dashboard
        data = _collect_data(ai_mode=True)
        panel = _render_dashboard(data, ai_mode=True)
        assert panel is not None


# ── Export Tests ──

class TestExport:
    """Tests for export module."""

    def test_session_to_markdown_empty(self):
        from devmind.commands.export import _session_to_markdown
        md = _session_to_markdown(99999)
        assert "Session not found" in md

    def test_session_to_json_empty(self):
        from devmind.commands.export import _session_to_json
        result = _session_to_json(99999)
        assert result["error"] == "Session not found"
        assert result["session_id"] == 99999
