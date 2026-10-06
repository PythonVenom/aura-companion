"""PluginManager — загрузка и управление плагинами (ADR-090).

Плагины живут в ~/.local/share/aura/plugins/<id>/.
Каждый плагин — manifest.json + plugin.py (опционально).
Эфемерные агенты (subprocess) — позже (Phase 7).
"""
from __future__ import annotations

import shutil
from pathlib import Path

from aura.core.plugin_manifest import PluginManifest, load_manifest

DEFAULT_PLUGINS_DIR = Path.home() / ".local/share/aura/plugins"


class PluginManager:
    def __init__(self, root: Path | None = None):
        self.root = Path(root) if root else DEFAULT_PLUGINS_DIR
        self.root.mkdir(parents=True, exist_ok=True)

    def list_plugins(self) -> list:
        """Список PluginManifest установленных плагинов."""
        out = []
        for d in sorted(self.root.iterdir()):
            if not d.is_dir():
                continue
            try:
                out.append(load_manifest(d))
            except Exception:
                continue
        return out

    def get(self, plugin_id: str) -> PluginManifest | None:
        d = self.root / plugin_id
        if not d.is_dir():
            return None
        try:
            return load_manifest(d)
        except Exception:
            return None

    def install(self, source: Path, *, force: bool = False) -> PluginManifest:
        """Скопировать плагин из source в root/<id>/."""
        source = Path(source)
        manifest = load_manifest(source)
        dst = self.root / manifest.id
        if dst.exists() and not force:
            raise FileExistsError(f"plugin {manifest.id} already installed")
        if dst.exists() and force:
            shutil.rmtree(dst)
        shutil.copytree(source, dst)
        return manifest

    def remove(self, plugin_id: str) -> bool:
        d = self.root / plugin_id
        if not d.is_dir():
            return False
        shutil.rmtree(d)
        return True

    def enabled(self, plugin_id: str) -> bool:
        # MVP: наличие manifest.json = включён.
        # Позже: enabled.json / config.
        return self.get(plugin_id) is not None


__all__ = ["DEFAULT_PLUGINS_DIR", "PluginManager"]
