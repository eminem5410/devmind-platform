"""Export manager - CSV, HTML, Markdown, JSON, YAML."""

from __future__ import annotations
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


def export_data(data: Any, fmt: str, output: Optional[Path] = None, prefix: str = "devmind") -> Optional[Path]:
    fmt = fmt.lower().strip()
    exporters = {"json": _export_json, "csv": _export_csv, "html": _export_html, "markdown": _export_markdown, "md": _export_markdown, "yaml": _export_yaml, "yml": _export_yaml}
    if fmt not in exporters:
        return None
    if output is None:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        ext = "md" if fmt in ("markdown", "md") else fmt
        output = Path(f"{prefix}_{timestamp}.{ext}")
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    exporters[fmt](data, output)
    return output


def _export_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str, ensure_ascii=False)


def _export_csv(data, path):
    rows = data if isinstance(data, list) else [data]
    if not rows:
        return
    flat_rows = []
    for row in rows:
        flat = {}
        _flatten(row, "", flat)
        flat_rows.append(flat)
    headers = list(flat_rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(flat_rows)


def _export_html(data, path):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    parts = ["<!DOCTYPE html>", "<html lang='es'>", "<head>", "  <meta charset='UTF-8'>",
        f"  <title>DevMind Report - {now}</title>", "  <style>",
        "    * { margin: 0; padding: 0; box-sizing: border-box; }",
        "    body { font-family: -apple-system, sans-serif; background: #1a1a2e; color: #e0e0e0; padding: 2rem; }",
        "    .container { max-width: 1000px; margin: 0 auto; }",
        "    h1 { color: #00d4ff; margin-bottom: 0.5rem; }",
        "    .timestamp { color: #888; margin-bottom: 2rem; }",
        "    table { width: 100%; border-collapse: collapse; margin: 1rem 0; background: #16213e; }",
        "    th { background: #0f3460; color: #00d4ff; padding: 0.75rem; text-align: left; font-size: 0.85rem; }",
        "    td { padding: 0.65rem; border-bottom: 1px solid #1a1a3e; }",
        "    .positive { color: #4ecca3; } .negative { color: #e94560; }",
        "    .section { margin: 2rem 0; } .section h2 { color: #e94560; }",
        "    .footer { margin-top: 3rem; border-top: 1px solid #333; color: #666; font-size: 0.8rem; }",
        "  </style>", "</head>", "<body>", '  <div class="container">',
        f"    <h1>DevMind Report</h1>", f'    <p class="timestamp">Generado: {now}</p>']
    if isinstance(data, dict):
        for key, value in data.items():
            if key in ("params", "metadata"):
                continue
            if isinstance(value, list) and value and isinstance(value[0], dict):
                parts.append(_render_table(key, value))
            elif isinstance(value, dict):
                parts.append(_render_kv(key, value))
    parts.extend(['    <div class="footer"><p>DevMind</p></div>', "  </div>", "</body>", "</html>"])
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))


def _export_markdown(data, path):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [f"# DevMind Report\n", f"*Generado: {now}*\n"]
    if isinstance(data, dict):
        for key, value in data.items():
            if key in ("params", "metadata"):
                continue
            if isinstance(value, list) and value and isinstance(value[0], dict):
                lines.append(f"## {key}\n")
                headers = list(value[0].keys())
                lines.append("| " + " | ".join(headers) + " |")
                lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
                for row in value:
                    lines.append("| " + " | ".join(str(row.get(h, "")) for h in headers) + " |")
                lines.append("")
            elif isinstance(value, dict):
                lines.append(f"## {key}\n")
                for k, v in value.items():
                    lines.append(f"- **{k}**: {v}")
                lines.append("")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def _export_yaml(data, path):
    lines = [f"# DevMind Export - {datetime.now(timezone.utc).isoformat()}"]
    _to_yaml(data, lines, 0)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def _flatten(obj, prefix, out):
    if isinstance(obj, dict):
        for k, v in obj.items():
            _flatten(v, f"{prefix}.{k}" if prefix else k, out)
    else:
        out[prefix] = obj


def _render_table(title, rows):
    parts = [f'    <div class="section">', f"    <h2>{title}</h2>", "    <table>"]
    if rows:
        headers = list(rows[0].keys())
        parts.append("      <thead><tr>" + "".join(f"        <th>{h}</th>" for h in headers) + "      </tr></thead>")
        parts.append("      <tbody>")
        for row in rows:
            parts.append("        <tr>" + "".join(f"        <td>{row.get(h, '')}</td>" for h in headers) + "        </tr>")
        parts.append("      </tbody>")
    parts.extend(["    </table>", "    </div>"])
    return "\n".join(parts)


def _render_kv(title, data):
    parts = [f'    <div class="section">', f"    <h2>{title}</h2>", "    <table>"]
    for k, v in data.items():
        parts.append(f"      <tr><td><strong>{k}</strong></td><td>{v}</td></tr>")
    parts.extend(["    </table>", "    </div>"])
    return "\n".join(parts)


def _to_yaml(obj, lines, indent):
    prefix = "  " * indent
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, (dict, list)):
                lines.append(f"{prefix}{k}:")
                _to_yaml(v, lines, indent + 1)
            else:
                lines.append(f"{prefix}{k}: {v}")
    elif isinstance(obj, list):
        for item in obj:
            if isinstance(item, (dict, list)):
                lines.append(f"{prefix}-")
                _to_yaml(item, lines, indent + 1)
            else:
                lines.append(f"{prefix}- {item}")
