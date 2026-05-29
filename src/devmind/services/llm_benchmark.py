"""
LLM Benchmark Service — v0.10.0

Compara rendimiento y calidad de modelos LLM locales (Ollama) vs proveedores API.
Metricas: tokens/s, TTFT, calidad heuristica (0-10), costo estimado.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Optional

import httpx


@dataclass
class QualityMetrics:
    """Metricas de calidad de respuesta (heuristica, 0-10)."""
    score: float = 0.0
    completeness: float = 0.0
    clarity: float = 0.0
    structure: float = 0.0
    vocabulary: float = 0.0


@dataclass
class LLMBenchmarkResult:
    """Resultado individual de un benchmark LLM."""
    provider: str = ""
    model: str = ""
    prompt: str = ""
    response: str = ""
    prompt_tokens: int = 0
    response_tokens: int = 0
    tokens_per_sec: float = 0.0
    ttft_ms: float = 0.0
    total_time_ms: float = 0.0
    quality: QualityMetrics = field(default_factory=QualityMetrics)
    cost_usd: float = 0.0
    success: bool = False
    error: str = ""


# Configuracion de proveedores API (OpenAI-compatible)
API_PROVIDERS = {
    "groq": {
        "base_url": "https://api.groq.com/openai/v1/chat/completions",
        "env_key": "GROQ_API_KEY",
        "models": [
            "llama-3.1-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
            "gemma2-9b-it",
        ],
        "cost_per_1k_input": 0.0,
        "cost_per_1k_output": 0.0,
    },
    "together": {
        "base_url": "https://api.together.xyz/v1/chat/completions",
        "env_key": "TOGETHER_API_KEY",
        "models": [
            "meta-llama/Llama-3.1-70B-Instruct-Turbo",
            "meta-llama/Llama-3.1-8B-Instruct-Turbo",
            "mistralai/Mixtral-8x7B-Instruct-v0.1",
        ],
        "cost_per_1k_input": 0.00088,
        "cost_per_1k_output": 0.00088,
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1/chat/completions",
        "env_key": "OPENROUTER_API_KEY",
        "models": [
            "meta-llama/llama-3.1-70b-instruct",
            "meta-llama/llama-3.1-8b-instruct",
        ],
        "cost_per_1k_input": 0.0004,
        "cost_per_1k_output": 0.0004,
    },
    "fireworks": {
        "base_url": "https://api.fireworks.ai/inference/v1/chat/completions",
        "env_key": "FIREWORKS_API_KEY",
        "models": [
            "accounts/fireworks/models/llama-v3p1-70b-instruct",
            "accounts/fireworks/models/llama-v3p1-8b-instruct",
        ],
        "cost_per_1k_input": 0.0002,
        "cost_per_1k_output": 0.0002,
    },
}

# Prompts de benchmark estandar
BENCHMARK_PROMPTS = [
    "Explain in 3 sentences what machine learning is and how neural networks learn from data.",
    "Write a short paragraph about the benefits of open source software in modern development.",
    "Describe the Linux operating system and why it is popular for AI development.",
    "What are the main differences between CPU and GPU computing? Explain briefly.",
    "List 3 key advantages of containerization with Docker for deployment workflows.",
]


def compute_quality(response: str, prompt: str) -> QualityMetrics:
    """Calcula puntaje de calidad usando heuristicas (0-10).

    Componentes:
    - Completitud (0-3): cobertura de palabras clave del prompt
    - Claridad (0-3): estructura de oraciones, longitud adecuada
    - Estructura (0-2): listas, parrafos, formato
    - Vocabulario (0-2): diversidad lexica
    """
    if not response or len(response) < 20:
        return QualityMetrics()

    # Completitud (0-3): cobertura de palabras clave del prompt
    prompt_words = set(w.lower() for w in prompt.split() if len(w) > 3)
    response_lower = response.lower()
    overlap = sum(1 for w in prompt_words if w in response_lower)
    completeness = min(3.0, round(overlap / max(len(prompt_words), 1) * 3, 1))

    # Claridad (0-3): oraciones bien formadas
    sentences = [s.strip() for s in response.replace("!", ".").replace("?", ".").split(".") if s.strip()]
    if sentences:
        avg_len = sum(len(s.split()) for s in sentences) / len(sentences)
        clarity = 2.0 if 5 < avg_len < 30 else 1.0
        if len(sentences) >= 3:
            clarity = min(3.0, clarity + 1.0)
        else:
            clarity = min(3.0, clarity + 0.5)
    else:
        clarity = 0.0
    clarity = min(3.0, round(clarity, 1))

    # Estructura (0-2): listas, parrafos, headers
    structure = 0.0
    has_lists = any(marker in response for marker in ["-", "*", "1.", "2.", "3."])
    has_paragraphs = len([p for p in response.split("\n") if p.strip()]) > 1
    has_headers = any(line.strip().startswith("#") or line.strip().startswith("**")
                      for line in response.split("\n"))
    if has_lists:
        structure += 0.8
    if has_paragraphs:
        structure += 0.6
    if has_headers:
        structure += 0.6
    structure = min(2.0, round(structure, 1))

    # Vocabulario (0-2): diversidad lexica
    words = response.lower().split()
    if words:
        unique = len(set(words))
        diversity = unique / len(words)
        vocabulary = min(2.0, round(diversity * 2.5, 1))
    else:
        vocabulary = 0.0

    total = round(completeness + clarity + structure + vocabulary, 1)
    return QualityMetrics(
        score=total,
        completeness=completeness,
        clarity=clarity,
        structure=structure,
        vocabulary=vocabulary,
    )


def _get_ollama_ram() -> float:
    """RAM consumido por Ollama en MB (cross-platform)."""
    try:
        import subprocess
        if os.name == "nt":
            r = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq ollama.exe", "/FO", "CSV"],
                capture_output=True, text=True, timeout=5,
            )
            total_kb = 0
            for line in r.stdout.strip().split("\n")[1:]:
                parts = line.strip('"').split('","')
                if len(parts) >= 5:
                    mem_str = parts[4].replace(" K", "").replace(",", "")
                    try:
                        total_kb += int(mem_str)
                    except ValueError:
                        pass
            return round(total_kb / 1024, 1)
        else:
            r = subprocess.run(
                ["sh", "-c", "ps aux | grep '[o]llama' | awk '{sum+=$6} END{print sum}'"],
                capture_output=True, text=True, timeout=5,
            )
            if r.returncode == 0 and r.stdout.strip():
                return round(int(r.stdout.strip()) / 1024, 1)
    except Exception:
        pass
    return 0.0


def benchmark_ollama(
    model: str,
    prompt: str,
    ollama_url: str = "http://localhost:11434",
) -> LLMBenchmarkResult:
    """Benchmark un modelo Ollama local."""
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": True,
        "options": {"num_predict": 200},
    }

    ram_before = _get_ollama_ram()

    try:
        start_time = time.time()
        first_token_time = None
        tokens_generated = 0
        response_text = ""

        with httpx.Client(timeout=120.0) as client:
            with client.stream("POST", f"{ollama_url}/api/generate", json=payload) as resp:
                if resp.status_code != 200:
                    error_body = ""
                    try:
                        error_body = resp.text
                    except Exception:
                        pass
                    return LLMBenchmarkResult(
                        provider="ollama", model=model, prompt=prompt[:100],
                        error="HTTP %d: %s" % (resp.status_code, error_body[:200]),
                    )

                for line in resp.iter_lines():
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                        if "response" in chunk:
                            delta = chunk.get("response", "")
                            response_text += delta
                            tokens_generated += 1
                            if first_token_time is None:
                                first_token_time = time.time()
                        if chunk.get("done", False):
                            break
                    except json.JSONDecodeError:
                        continue

        end_time = time.time()
        total_ms = (end_time - start_time) * 1000
        ttft_ms = (first_token_time - start_time) * 1000 if first_token_time else total_ms

        gen_time = end_time - (first_token_time or start_time)
        tps = tokens_generated / gen_time if gen_time > 0 else 0.0

        ram_after = _get_ollama_ram()
        quality = compute_quality(response_text, prompt)

        return LLMBenchmarkResult(
            provider="ollama",
            model=model,
            prompt=prompt[:100],
            response=response_text[:500],
            prompt_tokens=len(prompt.split()),
            response_tokens=tokens_generated,
            tokens_per_sec=round(tps, 2),
            ttft_ms=round(ttft_ms, 2),
            total_time_ms=round(total_ms, 2),
            quality=quality,
            cost_usd=0.0,
            success=True,
        )

    except httpx.ConnectError:
        return LLMBenchmarkResult(
            provider="ollama", model=model, prompt=prompt[:100],
            error="No se pudo conectar a Ollama (ollama serve no esta ejecutando)",
        )
    except Exception as e:
        return LLMBenchmarkResult(
            provider="ollama", model=model, prompt=prompt[:100],
            error=str(e)[:200],
        )


def benchmark_api(
    provider: str,
    model: str,
    prompt: str,
    api_key: str,
) -> LLMBenchmarkResult:
    """Benchmark un proveedor API (OpenAI-compatible)."""
    if provider not in API_PROVIDERS:
        available = ", ".join(API_PROVIDERS.keys())
        return LLMBenchmarkResult(
            provider=provider, model=model, prompt=prompt[:100],
            error="Proveedor desconocido: %s. Disponibles: %s" % (provider, available),
        )

    config = API_PROVIDERS[provider]
    base_url = config["base_url"]

    headers = {
        "Authorization": "Bearer %s" % api_key,
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 200,
        "stream": True,
    }

    try:
        start_time = time.time()
        first_token_time = None
        tokens_generated = 0
        response_text = ""
        prompt_tokens_estimate = len(prompt.split())

        with httpx.Client(timeout=60.0) as client:
            with client.stream("POST", base_url, json=payload, headers=headers) as resp:
                if resp.status_code != 200:
                    error_body = ""
                    try:
                        error_body = resp.text
                    except Exception:
                        pass
                    return LLMBenchmarkResult(
                        provider=provider, model=model, prompt=prompt[:100],
                        error="HTTP %d: %s" % (resp.status_code, error_body[:200]),
                    )

                for line in resp.iter_lines():
                    if not line:
                        continue
                    line = line.lstrip("data: ").strip()
                    if line == "[DONE]":
                        break
                    try:
                        chunk = json.loads(line)
                        choices = chunk.get("choices", [])
                        if choices:
                            delta = choices[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                response_text += content
                                tokens_generated += max(1, len(content) // 4)
                                if first_token_time is None:
                                    first_token_time = time.time()
                        usage = chunk.get("usage", {})
                        if usage:
                            prompt_tokens_estimate = usage.get("prompt_tokens", prompt_tokens_estimate)
                    except json.JSONDecodeError:
                        continue

        end_time = time.time()
        total_ms = (end_time - start_time) * 1000
        ttft_ms = (first_token_time - start_time) * 1000 if first_token_time else total_ms

        gen_time = end_time - (first_token_time or start_time)
        tps = tokens_generated / gen_time if gen_time > 0 else 0.0

        quality = compute_quality(response_text, prompt)

        cost = (
            config["cost_per_1k_input"] * prompt_tokens_estimate / 1000
            + config["cost_per_1k_output"] * tokens_generated / 1000
        )

        return LLMBenchmarkResult(
            provider=provider,
            model=model,
            prompt=prompt[:100],
            response=response_text[:500],
            prompt_tokens=prompt_tokens_estimate,
            response_tokens=tokens_generated,
            tokens_per_sec=round(tps, 2),
            ttft_ms=round(ttft_ms, 2),
            total_time_ms=round(total_ms, 2),
            quality=quality,
            cost_usd=round(cost, 6),
            success=True,
        )

    except httpx.ConnectError:
        return LLMBenchmarkResult(
            provider=provider, model=model, prompt=prompt[:100],
            error="Error de conexion a %s. Verifica tu conexion." % provider,
        )
    except httpx.TimeoutException:
        return LLMBenchmarkResult(
            provider=provider, model=model, prompt=prompt[:100],
            error="Timeout conectando a %s despues de 60s." % provider,
        )
    except Exception as e:
        return LLMBenchmarkResult(
            provider=provider, model=model, prompt=prompt[:100],
            error=str(e)[:200],
        )


def get_available_providers() -> dict:
    """Detecta proveedores API disponibles buscando API keys en env vars."""
    available = {}
    for name, config in API_PROVIDERS.items():
        key = os.environ.get(config["env_key"])
        available[name] = key
    return available


def run_llm_benchmark(
    providers: Optional[list] = None,
    models: Optional[list] = None,
    prompt: Optional[str] = None,
    runs: int = 1,
    include_local: bool = True,
    ollama_model: Optional[str] = None,
) -> list:
    """Ejecuta benchmarks LLM y retorna lista de LLMBenchmarkResult."""
    results = []
    prompts = [prompt] if prompt else BENCHMARK_PROMPTS

    # Local Ollama
    if include_local:
        ollama_model_name = ollama_model or ""
        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.get("http://localhost:11434/api/tags")
                if resp.status_code == 200:
                    models_data = resp.json().get("models", [])
                    available_models = [m.get("name", "") for m in models_data]
                    if not ollama_model_name and available_models:
                        ollama_model_name = available_models[0]
                    if ollama_model_name:
                        for run_idx in range(runs):
                            run_prompt = prompts[run_idx % len(prompts)]
                            result = benchmark_ollama(ollama_model_name, run_prompt)
                            results.append(result)
        except Exception:
            pass

    # API Providers
    available_providers = get_available_providers()
    target_providers = providers or [p for p, key in available_providers.items() if key]

    for provider_name in target_providers:
        api_key = available_providers.get(provider_name)
        if not api_key:
            results.append(LLMBenchmarkResult(
                provider=provider_name, model="N/A", prompt="",
                error="API key no encontrada. Set %s env var." % API_PROVIDERS[provider_name]["env_key"],
            ))
            continue

        provider_models = models or API_PROVIDERS[provider_name]["models"][:1]
        for model_name in provider_models:
            for run_idx in range(runs):
                run_prompt = prompts[run_idx % len(prompts)]
                result = benchmark_api(provider_name, model_name, run_prompt, api_key)
                results.append(result)

    return results
