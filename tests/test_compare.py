"""Tests for v0.7.0 - Compare and Export."""

import json
from devmind.services.pricing import get_pricing, calculate_api_cost, calculate_local_cost, PRICING_TABLE
from devmind.services.export import export_data
from pathlib import Path


class TestPricing:
    def test_pricing_table_not_empty(self):
        assert len(PRICING_TABLE) >= 30

    def test_get_all_pricing(self):
        result = get_pricing()
        assert len(result) == len(PRICING_TABLE)

    def test_filter_by_provider(self):
        result = get_pricing(provider="openai")
        assert all(p.provider == "openai" for p in result)
        assert len(result) >= 5

    def test_filter_by_model(self):
        result = get_pricing(model="gpt-4o")
        assert all("gpt-4o" in p.model for p in result)

    def test_filter_not_found(self):
        result = get_pricing(provider="nonexistent")
        assert result == []

    def test_calculate_api_cost(self):
        pricing = get_pricing(model="gpt-4o-mini")[0]
        cost = calculate_api_cost(pricing, 100000, 40000, 0.5)
        assert cost["monthly_cost"] > 0
        assert cost["daily_cost"] > 0
        assert cost["model_id"] == "openai/gpt-4o-mini"

    def test_calculate_api_cost_no_cache(self):
        pricing = get_pricing(model="gpt-4o-mini")[0]
        cost_no_cache = calculate_api_cost(pricing, 100000, 40000, 0.0)
        cost_full_cache = calculate_api_cost(pricing, 100000, 40000, 1.0)
        assert cost_full_cache["daily_cost"] < cost_no_cache["daily_cost"]

    def test_calculate_local_cost(self):
        result = calculate_local_cost(tokens_per_second=4.7)
        assert result["daily_electricity_cost"] > 0
        assert result["monthly_electricity_cost"] > result["daily_electricity_cost"]
        assert result["daily_tokens"] == int(4.7 * 8 * 3600)

    def test_local_cost_zero_tps(self):
        result = calculate_local_cost(tokens_per_second=0)
        assert result["daily_tokens"] == 0
        assert result["daily_electricity_cost"] > 0  # GPU still uses power


class TestExport:
    def test_export_json(self, tmp_path):
        data = {"test": "value", "num": 42}
        out = export_data(data, "json", output=tmp_path / "test.json")
        assert out.exists()
        loaded = json.loads(out.read_text())
        assert loaded["test"] == "value"

    def test_export_csv(self, tmp_path):
        data = [{"model": "gpt-4o", "cost": 8.81}, {"model": "claude", "cost": 11.47}]
        out = export_data(data, "csv", output=tmp_path / "test.csv")
        assert out.exists()
        content = out.read_text()
        assert "model" in content
        assert "gpt-4o" in content

    def test_export_html(self, tmp_path):
        data = {"local": {"monthly": 7.20}, "api": [{"model": "gpt-4o", "cost": 8.81}]}
        out = export_data(data, "html", output=tmp_path / "test.html")
        assert out.exists()
        content = out.read_text()
        assert "DevMind Report" in content
        assert "<table" in content

    def test_export_markdown(self, tmp_path):
        data = {"section": [{"key": "value"}]}
        out = export_data(data, "markdown", output=tmp_path / "test.md")
        assert out.exists()
        content = out.read_text()
        assert "# DevMind Report" in content

    def test_export_yaml(self, tmp_path):
        data = {"key": "value"}
        out = export_data(data, "yaml", output=tmp_path / "test.yaml")
        assert out.exists()
        content = out.read_text()
        assert "key: value" in content

    def test_export_unsupported(self, tmp_path):
        result = export_data({"a": 1}, "xml", output=tmp_path / "test.xml")
        assert result is None


class TestCompareService:
    def test_run_compare_no_local(self):
        from devmind.services.compare import run_compare
        from rich.console import Console
        import io
        console = Console(file=io.StringIO(), force_terminal=False)
        result = run_compare(console=console)
        assert "api" in result
        assert len(result["api"]) > 0
        assert result["local"] is None

    def test_run_compare_with_local(self):
        from devmind.services.compare import run_compare
        from rich.console import Console
        import io
        console = Console(file=io.StringIO(), force_terminal=False)
        result = run_compare(local_tokens_per_second=4.7, console=console)
        assert result["local"] is not None
        assert result["local"]["tokens_per_second"] == 4.7

    def test_run_compare_filter_provider(self):
        from devmind.services.compare import run_compare
        from rich.console import Console
        import io
        console = Console(file=io.StringIO(), force_terminal=False)
        result = run_compare(vs_provider="anthropic", console=console)
        assert all(r["provider"] == "anthropic" for r in result["api"])
