"""PluginManifest — ADR-090.

Формат манифеста плагина:
{
  "id": "deepseek",
  "name": "DeepSeek AI",
  "version": "1.0.0",
  "author": "community",
  "risk_level": "cloud" | "local" | "hybrid",
  "data_leaves_device": true/false,
  "endpoint": "https://...",
  "warns": ["...", "..."],
  "requires": ["api_key"],
  "user_consent_required": true/false
}
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class PluginManifest:
    id: str
    name: str
    version: str = "0.1.0"
    author: str = "unknown"
    risk_level: str = "local"          # local | cloud | hybrid
    data_leaves_device: bool = False
    endpoint: str | None = None
    warns: list = field(default_factory=list)
    requires: list = field(default_factory=list)
    user_consent_required: bool = False

    @property
    def is_cloud(self) -> bool:
        return self.risk_level == "cloud" or self.data_leaves_device

    @property
    def needs_consent(self) -> bool:
        return self.user_consent_required or self.is_cloud

    @property
    def requires_api_key(self) -> bool:
        return "api_key" in self.requires


def load_manifest(plugin_dir: Path) -> PluginManifest:
    plugin_dir = Path(plugin_dir)
    manifest_path = plugin_dir / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"manifest.json not found in {plugin_dir}")
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"invalid manifest.json: {e}")
    if "id" not in data:
        raise ValueError("manifest.json missing 'id'")
    return PluginManifest(
        id=data["id"],
        name=data.get("name", data["id"]),
        version=data.get("version", "0.1.0"),
        author=data.get("author", "unknown"),
        risk_level=data.get("risk_level", "local"),
        data_leaves_device=bool(data.get("data_leaves_device", False)),
        endpoint=data.get("endpoint"),
        warns=list(data.get("warns", [])),
        requires=list(data.get("requires", [])),
        user_consent_required=bool(data.get("user_consent_required", False)),
    )


__all__ = ["PluginManifest", "load_manifest"]
