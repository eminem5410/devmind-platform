# devmind/services/chat.py
"""Multi-provider Chat Service — v0.12.0

Streaming chat with Ollama local + 4 API providers (Groq, Together, OpenRouter, Fireworks).
Reutiliza la infraestructura de httpx/streaming del benchmark.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Generator, Optional

import httpx

from devmind.config.settings import get_api_key, get_base_url, resolve_alias


@dataclass
class ChatMessage:
    """A single chat message."""
    role: str
    content: str
    tokens: int = 0


@dataclass
class ChatResponse:
    """Result of a chat completion."""
    content: str = ""
    tokens: int = 0
    ttft_ms: float = 0.0
    total_ms: float = 0.0
    success: bool = False
    error: str = ""


@dataclass
class StreamChunk:
    """A single streaming chunk."""
    token: str = ""
    done: bool = False
    tokens_so_far: int = 0
    error: str = ""


def _build_messages(history: list[ChatMessage]) -> list[dict]:
    """Convert ChatMessage list to API format."""
    return [{"role": m.role, "content": m.content} for m in history]


def stream_ollama_chat(
    model: str,
    messages: list[ChatMessage],
    ollama_url: Optional[str] = None,
) -> Generator[StreamChunk, None, None]:
    """Stream chat from local Ollama.

    Uses /api/chat endpoint with messages array.
    Yields StreamChunk for each token.
    """
    if ollama_url is None:
        ollama_url = get_base_url("ollama").rstrip("/")

    url = ollama_url + "/api/chat"
    payload = {
        "model": model,
        "messages": _build_messages(messages),
        "stream": True,
    }

    try:
        with httpx.Client(timeout=120.0) as client:
            with client.stream("POST", url, json=payload) as resp:
                if resp.status_code != 200:
                    error_body = ""
                    try:
                        error_body = resp.text
                    except Exception:
                        pass
                    yield StreamChunk(
                        error="HTTP %d: %s" % (resp.status_code, error_body[:300])
                    )
                    return

                total_tokens = 0
                for line in resp.iter_lines():
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                        msg = chunk.get("message", {})
                        content = msg.get("content", "")
                        if content:
                            total_tokens += 1
                            yield StreamChunk(
                                token=content,
                                tokens_so_far=total_tokens,
                            )
                        if chunk.get("done", False):
                            yield StreamChunk(done=True, tokens_so_far=total_tokens)
                            return
                    except json.JSONDecodeError:
                        continue

                # Stream ended without done signal
                yield StreamChunk(done=True, tokens_so_far=total_tokens)

    except httpx.ConnectError:
        yield StreamChunk(error="No se pudo conectar a Ollama. Verifica que 'ollama serve' este ejecutando.")
    except httpx.TimeoutException:
        yield StreamChunk(error="Timeout conectando a Ollama (120s).")
    except Exception as e:
        yield StreamChunk(error=str(e)[:300])


def stream_api_chat(
    provider: str,
    model: str,
    messages: list[ChatMessage],
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> Generator[StreamChunk, None, None]:
    """Stream chat from an API provider (OpenAI-compatible).

    Supports: Groq, Together AI, OpenRouter, Fireworks.
    Yields StreamChunk for each token.
    """
    if api_key is None:
        api_key = get_api_key(provider)
    if base_url is None:
        base_url = get_base_url(provider)

    if not api_key:
        yield StreamChunk(
            error="API key no configurada para %s. Ejecuta 'devmind init' para configurar." % provider
        )
        return

    url = base_url.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": "Bearer %s" % api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": _build_messages(messages),
        "stream": True,
    }

    try:
        with httpx.Client(timeout=60.0) as client:
            with client.stream("POST", url, json=payload, headers=headers) as resp:
                if resp.status_code != 200:
                    error_body = ""
                    try:
                        error_body = resp.text
                    except Exception:
                        pass
                    yield StreamChunk(
                        error="HTTP %d: %s" % (resp.status_code, error_body[:300])
                    )
                    return

                total_tokens = 0
                for line in resp.iter_lines():
                    if not line:
                        continue
                    line = line.lstrip("data: ").strip()
                    if line == "[DONE]":
                        yield StreamChunk(done=True, tokens_so_far=total_tokens)
                        return
                    try:
                        chunk = json.loads(line)
                        choices = chunk.get("choices", [])
                        if choices:
                            delta = choices[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                # Estimate tokens: ~4 chars per token
                                total_tokens += max(1, len(content) // 4)
                                yield StreamChunk(
                                    token=content,
                                    tokens_so_far=total_tokens,
                                )
                            finish = choices[0].get("finish_reason", "")
                            if finish == "stop":
                                usage = chunk.get("usage", {})
                                if usage:
                                    total_tokens = usage.get("completion_tokens", total_tokens)
                                yield StreamChunk(done=True, tokens_so_far=total_tokens)
                                return
                    except json.JSONDecodeError:
                        continue

                yield StreamChunk(done=True, tokens_so_far=total_tokens)

    except httpx.ConnectError:
        yield StreamChunk(error="Error de conexion a %s. Verifica tu conexion." % provider)
    except httpx.TimeoutException:
        yield StreamChunk(error="Timeout conectando a %s (60s)." % provider)
    except Exception as e:
        yield StreamChunk(error=str(e)[:300])


def stream_chat(
    provider: str,
    model: str,
    messages: list[ChatMessage],
    api_key: Optional[str] = None,
) -> Generator[StreamChunk, None, None]:
    """Unified streaming chat interface.

    Automatically routes to Ollama or API provider based on provider name.
    """
    model = resolve_alias(model)
    provider_lower = provider.lower()

    if provider_lower == "ollama":
        yield from stream_ollama_chat(model, messages)
    elif provider_lower in ("groq", "together", "openrouter", "fireworks"):
        yield from stream_api_chat(provider_lower, model, messages, api_key=api_key)
    else:
        yield StreamChunk(
            error="Proveedor desconocido: %s. Proveedores: ollama, groq, together, openrouter, fireworks" % provider
        )


def chat_complete(
    provider: str,
    model: str,
    messages: list[ChatMessage],
    api_key: Optional[str] = None,
) -> ChatResponse:
    """Non-streaming chat completion. Collects all chunks into a ChatResponse."""
    start_time = time.time()
    first_token_time = None
    content_parts = []
    total_tokens = 0
    error = ""

    for chunk in stream_chat(provider, model, messages, api_key=api_key):
        if chunk.error:
            error = chunk.error
            break
        if chunk.token:
            content_parts.append(chunk.token)
            if first_token_time is None:
                first_token_time = time.time()
        if chunk.done:
            total_tokens = chunk.tokens_so_far

    end_time = time.time()
    total_ms = (end_time - start_time) * 1000
    ttft_ms = (first_token_time - start_time) * 1000 if first_token_time else total_ms

    if error:
        return ChatResponse(error=error)

    return ChatResponse(
        content="".join(content_parts),
        tokens=total_tokens,
        ttft_ms=round(ttft_ms, 1),
        total_ms=round(total_ms, 1),
        success=True,
    )
