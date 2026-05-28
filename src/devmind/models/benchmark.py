"""
Modelos Pydantic para benchmark de Ollama.

Resultados de medicion de rendimiento para modelos locales:
- Tokens por segundo (throughput)
- Time to first token (latencia inicial)
- RAM pico consumida
- Duracion total
- Metadata del modelo y prompt
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


class BenchmarkResult(BaseModel):
    """Resultado de un benchmark individual a un modelo Ollama."""
    model: str = Field(description="Nombre del modelo benchmarkueado")
    prompt: str = Field(description="Prompt enviado al modelo")
    response: str = Field(description="Respuesta generada (truncada)")
    response_tokens: int = Field(description="Tokens en la respuesta")
    prompt_tokens: int = Field(description="Tokens en el prompt")
    total_tokens: int = Field(description="Tokens totales procesados")
    tokens_per_sec: float = Field(description="Throughput: tokens generados por segundo")
    ttft_ms: float = Field(description="Time to first token en milisegundos")
    total_time_ms: float = Field(description="Tiempo total de generacion en milisegundos")
    peak_ram_mb: float = Field(description="RAM pico consumida por Ollama durante benchmark")
    ram_before_mb: Optional[float] = Field(default=None, description="RAM antes del benchmark")
    ram_after_mb: Optional[float] = Field(default=None, description="RAM despues del benchmark")
    success: bool = Field(default=True)
    error: Optional[str] = Field(default=None)


class BenchmarkComparison(BaseModel):
    """Comparacion entre multiples benchmarks (historial)."""
    benchmarks: list[BenchmarkResult] = Field(default_factory=list)
    avg_tokens_per_sec: Optional[float] = Field(default=None, description="Promedio de tokens/s")


class BenchmarkReport(BaseModel):
    """Reporte completo de benchmark de Ollama."""
    version: str = "0.5.0"
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    hostname: str = ""
    hardware_summary: str = Field(default="", description="Resumen del hardware del sistema")
    results: list[BenchmarkResult] = Field(default_factory=list)
    summary: dict = Field(default_factory=dict)

    def compute_summary(self) -> dict:
        """Calcula resumen estadistico de los benchmarks."""
        if not self.results:
            self.summary = {"benchmarks": 0}
            return self.summary

        successful = [r for r in self.results if r.success]
        total = len(self.results)
        ok = len(successful)

        if successful:
            avg_tps = sum(r.tokens_per_sec for r in successful) / ok
            min_tps = min(r.tokens_per_sec for r in successful)
            max_tps = max(r.tokens_per_sec for r in successful)
            avg_ttft = sum(r.ttft_ms for r in successful) / ok
            avg_ram = sum(r.peak_ram_mb for r in successful) / ok
            total_tokens = sum(r.total_tokens for r in successful)
        else:
            avg_tps = min_tps = max_tps = avg_ttft = avg_ram = total_tokens = 0

        self.summary = {
            "benchmarks_total": total,
            "benchmarks_ok": ok,
            "benchmarks_failed": total - ok,
            "avg_tokens_per_sec": round(avg_tps, 2),
            "min_tokens_per_sec": round(min_tps, 2),
            "max_tokens_per_sec": round(max_tps, 2),
            "avg_ttft_ms": round(avg_ttft, 2),
            "avg_peak_ram_mb": round(avg_ram, 1),
            "total_tokens_generated": total_tokens,
            "models_tested": list(set(r.model for r in successful)),
        }
        return self.summary
