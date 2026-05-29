# devmind/config/settings.py
"""Configuration management for DevMind.

Stores API keys, default provider/model, and aliases in ~/.devmind/config.toml
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

DEVMIND_HOME = Path.home() / ".devmind"
CONFIG_PATH = DEVMIND_HOME / "config.toml"

DEFAULT_CONFIG: dict[str, Any] = {
    "default_provider": "ollama",
    "default_model": "phi3:mini",
    "providers": {
        "ollama": {
            "base_url": "http://localhost:11434",
            "api_key": "",
        },
        "groq": {
            "base_url": "https://api.groq.com/openai/v1",
            "api_key": "",
        },
        "together": {
            "base_url": "https://api.together.xyz/v1",
            "api_key": "",
        },
        "openrouter": {
            "base_url": "https://openrouter.ai/api/v1",
            "api_key": "",
        },
        "fireworks": {
            "base_url": "https://api.fireworks.ai/inference/v1",
            "api_key": "",
        },
    },
    "aliases": {},
}

PROVIDERS = ["ollama", "groq", "together", "openrouter", "fireworks"]


def _ensure_dir() -> None:
    """Ensure ~/.devmind/ directory exists."""
    DEVMIND_HOME.mkdir(parents=True, exist_ok=True)


def load_config() -> dict[str, Any]:
    """Load configuration from config.toml, creating defaults if missing."""
    _ensure_dir()
    if not CONFIG_PATH.exists():
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

    try:
        with open(CONFIG_PATH, "rb") as f:
            data = tomllib.load(f)
    except (tomllib.TOMLDecodeError, OSError):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

    # Merge with defaults to fill missing keys
    merged = DEFAULT_CONFIG.copy()
    merged.update(data)
    if "providers" not in merged:
        merged["providers"] = DEFAULT_CONFIG["providers"]
    for prov in PROVIDERS:
        if prov not in merged["providers"]:
            merged["providers"][prov] = DEFAULT_CONFIG["providers"][prov]
    return merged


def save_config(config: dict[str, Any]) -> None:
    """Save configuration to config.toml."""
    _ensure_dir()
    # Strip empty API keys for cleaner output
    output = _clean_config(config)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        f.write(_dict_to_toml(output))


def get_api_key(provider: str) -> str:
    """Get API key for a provider. Returns empty string if not set."""
    config = load_config()
    return config.get("providers", {}).get(provider, {}).get("api_key", "")


def get_base_url(provider: str) -> str:
    """Get base URL for a provider."""
    config = load_config()
    return config.get("providers", {}).get(provider, {}).get("base_url", "")


def get_default_provider() -> str:
    """Get default provider name."""
    return load_config().get("default_provider", "ollama")


def get_default_model() -> str:
    """Get default model name."""
    return load_config().get("default_model", "phi3:mini")


def set_default_provider(provider: str) -> None:
    """Set default provider."""
    config = load_config()
    config["default_provider"] = provider
    save_config(config)


def set_default_model(model: str) -> None:
    """Set default model."""
    config = load_config()
    config["default_model"] = model
    save_config(config)


def set_api_key(provider: str, key: str) -> None:
    """Set API key for a provider."""
    config = load_config()
    if "providers" not in config:
        config["providers"] = {}
    if provider not in config["providers"]:
        config["providers"][provider] = DEFAULT_CONFIG["providers"][provider]
    config["providers"][provider]["api_key"] = key
    save_config(config)


def resolve_alias(name: str) -> str:
    """Resolve a model alias to its actual name."""
    config = load_config()
    aliases = config.get("aliases", {})
    return aliases.get(name, name)


# ── TOML Serializer (simple, no external dep) ──

def _dict_to_toml(d: dict[str, Any], prefix: str = "") -> str:
    """Convert dict to TOML string (supports nested dicts)."""
    lines: list[str] = []
    for key, value in d.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            lines.append(f"[{full_key}]")
            for k2, v2 in value.items():
                if isinstance(v2, dict):
                    lines.append(f"[{full_key}.{k2}]")
                    for k3, v3 in v2.items():
                        lines.append(f"{k3} = {_toml_value(v3)}")
                    lines.append("")
                else:
                    lines.append(f"{k2} = {_toml_value(v2)}")
            lines.append("")
        else:
            lines.append(f"{full_key} = {_toml_value(value)}")
    return "\n".join(lines).strip() + "\n"


def _toml_value(v: Any) -> str:
    """Convert a Python value to TOML representation."""
    if isinstance(v, str):
        return f'"{v}"'
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int | float):
        return str(v)
    if isinstance(v, list):
        items = ", ".join(_toml_value(i) for i in v)
        return f"[{items}]"
    return f'"{v}"'


def _clean_config(config: dict[str, Any]) -> dict[str, Any]:
    """Clean config for output: strip empty strings but keep structure."""
    out: dict[str, Any] = {"default_provider": config.get("default_provider", "ollama")}
    out["default_model"] = config.get("default_model", "phi3:mini")
    out["providers"] = {}
    for prov, pdata in config.get("providers", {}).items():
        out["providers"][prov] = {
            "base_url": pdata.get("base_url", DEFAULT_CONFIG["providers"][prov]["base_url"]),
            "api_key": pdata.get("api_key", ""),
        }
    aliases = config.get("aliases", {})
    if aliases:
        out["aliases"] = aliases
    return out
