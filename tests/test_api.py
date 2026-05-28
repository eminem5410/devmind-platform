"""
Comprehensive API tests for DevMind Platform.

All external dependencies (Ollama, Docker, system info collectors) are
mocked so tests run in any CI environment without real services.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from devmind.models.diagnostic import (
    DiagnosticCheck,
    Severity,
    SystemData,
)
from devmind.models.snapshot import (
    SnapshotHardware,
    SnapshotNetwork,
    SnapshotReport,
    SnapshotSoftware,
)


# ── Health & Version ────────────────────────────────────────────────────────


def test_health(client):
    """GET /api/health returns expected health payload."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "devmind-api"


def test_version(client):
    """GET /api/version returns version information."""
    response = client.get("/api/version")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert data["version"] == "0.7.0"
    assert "api_version" in data


# ── Explain endpoints ───────────────────────────────────────────────────────


def test_explain_topics(client):
    """GET /api/explain returns the five available topics."""
    response = client.get("/api/explain")
    assert response.status_code == 200
    data = response.json()
    topics = data["topics"]
    for expected in ("ram", "gpu", "python", "ollama", "docker"):
        assert expected in topics, f"Expected topic '{expected}' not found"


def test_explain_topic_ram(client):
    """GET /api/explain/ram returns content about RAM."""
    response = client.get("/api/explain/ram")
    assert response.status_code == 200
    data = response.json()
    assert data["topic"] == "ram"
    assert "content" in data
    assert len(data["content"]) > 0


def test_explain_topic_invalid(client):
    """GET /api/explain/nonexistent returns 404."""
    response = client.get("/api/explain/nonexistent")
    assert response.status_code == 404


# ── History endpoints (empty database) ───────────────────────────────────────


def test_history_doctors_empty(client):
    """GET /api/history/doctors returns empty list when DB is fresh."""
    response = client.get("/api/history/doctors")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["entries"] == []


def test_history_benchmarks_empty(client):
    """GET /api/history/benchmarks returns empty list when DB is fresh."""
    response = client.get("/api/history/benchmarks")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["entries"] == []


def test_history_snapshots_empty(client):
    """GET /api/history/snapshots returns empty list when DB is fresh."""
    response = client.get("/api/history/snapshots")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["entries"] == []


def test_history_all_empty(client):
    """GET /api/history returns combined empty history."""
    response = client.get("/api/history")
    assert response.status_code == 200
    data = response.json()
    assert "doctors" in data
    assert "benchmarks" in data
    assert "snapshots" in data
    for section in ("doctors", "benchmarks", "snapshots"):
        assert data[section]["total"] == 0
        assert data[section]["entries"] == []


# ── Setup profiles ───────────────────────────────────────────────────────────


def test_setup_profiles(client):
    """GET /api/setup/profiles returns the three known profiles."""
    response = client.get("/api/setup/profiles")
    assert response.status_code == 200
    data = response.json()
    profiles = data["profiles"]
    profile_names = [p["name"] for p in profiles]
    for expected in ("local-llm", "ai-dev", "rag-lab"):
        assert expected in profile_names, f"Expected profile '{expected}' not found"
    assert len(profiles) == 3


# ── Doctor endpoint (mocked collectors) ───────────────────────────────────────


@patch("devmind.api.routes.doctor.generate_recommendations", return_value=[])
@patch("devmind.api.routes.doctor.logger")
def test_doctor_endpoint(mock_logger, mock_recs, client):
    """GET /api/doctor returns a diagnostic report with mocked collectors."""
    mock_system = SystemData(
        os_name="Linux",
        os_version="22.04",
        kernel="5.15",
        arch="x86_64",
        python_version="3.12.0",
        ram_total_gb=16.0,
        ram_used_gb=4.0,
        cpu_name="Test CPU",
        cpu_cores=8,
        disk_free_gb=200.0,
    )

    mock_checks = [
        DiagnosticCheck(
            name="OS",
            category="system",
            severity=Severity.INFO,
            status="ok",
            value="Linux 22.04",
        ),
        DiagnosticCheck(
            name="Python",
            category="system",
            severity=Severity.INFO,
            status="ok",
            value="3.12.0",
        ),
        DiagnosticCheck(
            name="RAM",
            category="system",
            severity=Severity.INFO,
            status="ok",
            value="4.0 / 16.0 GB (25%)",
        ),
    ]

    with (
        patch(
            "devmind.api.routes.doctor._collect_system_data",
            return_value=mock_system,
        ),
        patch(
            "devmind.api.routes.doctor._collect_checks",
            return_value=mock_checks,
        ),
    ):
        response = client.get("/api/doctor")

    assert response.status_code == 200
    data = response.json()
    assert "checks" in data
    assert "summary" in data
    assert "health_score" in data["summary"]
    # All INFO severity -> health_score == 100
    assert data["summary"]["health_score"] == 100
    assert data["summary"]["total_checks"] == 3


# ── Snapshot endpoint (mocked collector) ─────────────────────────────────────


@patch("devmind.api.routes.snapshot.logger")
def test_snapshot_endpoint(mock_logger, client):
    """GET /api/snapshot returns a snapshot report with mocked collector."""
    mock_snapshot = SnapshotReport(
        hostname="test-machine",
        hardware=SnapshotHardware(
            cpu_name="Test CPU",
            cpu_cores=4,
            ram_total_gb=16.0,
            ram_used_gb=8.0,
            ram_usage_pct=50.0,
            disk_total_gb=500.0,
            disk_free_gb=200.0,
            disk_usage_pct=60.0,
            gpu=None,
        ),
        software=SnapshotSoftware(
            os_name="Linux",
            os_version="22.04",
            kernel="5.15",
            arch="x86_64",
            python_version="3.12.0",
        ),
        network=SnapshotNetwork(
            hostname="test-machine",
            ip_local="192.168.1.100",
        ),
    )

    with patch(
        "devmind.api.routes.snapshot._collect_snapshot",
        return_value=mock_snapshot,
    ):
        response = client.get("/api/snapshot")

    assert response.status_code == 200
    data = response.json()
    assert data["hostname"] == "test-machine"
    assert data["hardware"]["cpu_name"] == "Test CPU"
    assert data["software"]["python_version"] == "3.12.0"
