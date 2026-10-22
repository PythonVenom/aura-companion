"""Plugin SDK — единый контракт для разработчиков плагинов AURA.

Наука: Plugin Architecture (Fowler 2002), MCP-совместимость.
Плагин — папка с manifest.json + plugin.py + __init__.py.
"""
from __future__ import annotations

import contextlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

PLUGINS_DIR = Path.home() / ".local" / "share" / "aura" / "plugins"


@dataclass
class PluginManifest:
    """Манифест плагина (manifest.json)."""
    name: str
    version: str = "0.1.0"
    author: str = "unknown"
    description: str = ""
    license: str = "MIT"
    mcp_compatible: bool = False
    requires: list[str] = field(default_factory=list)
    agents: list[str] = field(default_factory=list)

    @classmethod
    def load(cls, path: Path) -> PluginManifest:
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            name=data.get("name", path.parent.name),
            version=data.get("version", "0.1.0"),
            author=data.get("author", "unknown"),
            description=data.get("description", ""),
            license=data.get("license", "MIT"),
            mcp_compatible=data.get("mcp_compatible", False),
            requires=data.get("requires", []),
            agents=data.get("agents", []),
        )


class PluginSDK:
    """SDK для работы с плагинами."""

    def __init__(self, plugins_dir: Path | None = None) -> None:
        self.dir = plugins_dir or PLUGINS_DIR
        self.dir.mkdir(parents=True, exist_ok=True)

    def list_plugins(self) -> list[PluginManifest]:
        """Список всех плагинов."""
        out: list[PluginManifest] = []
        for d in self.dir.iterdir():
            if d.is_dir():
                manifest_path = d / "manifest.json"
                if manifest_path.exists():
                    with contextlib.suppress(Exception):
                        out.append(PluginManifest.load(manifest_path))
        return out

    def install_template(self, name: str, author: str = "unknown") -> Path:
        """Создать шаблон плагина."""
        plugin_dir = self.dir / name
        plugin_dir.mkdir(exist_ok=True)
        # manifest.json
        (plugin_dir / "manifest.json").write_text(
            json.dumps({
                "name": name,
                "version": "0.1.0",
                "author": author,
                "description": "TODO",
                "license": "MIT",
                "mcp_compatible": False,
                "agents": [],
            }, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        # plugin.py
        (plugin_dir / "plugin.py").write_text('''"""Plugin entry point."""
from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


class MyAgent(BaseAgent):
    name = "my_agent"
    MODULE_ALWAYS = True

    def can_handle(self, request: AgentRequest) -> bool:
        return "hello" in request.text.lower()

    async def handle(self, request: AgentRequest) -> AgentResponse:
        if not self.can_handle(request):
            return AgentResponse.not_handled(self.name)
        return AgentResponse.ok("Hello from plugin!", agent_name=self.name)
''', encoding="utf-8")
        # __init__.py
        (plugin_dir / "__init__.py").write_text('from .plugin import MyAgent\n', encoding="utf-8")
        # README.md
        (plugin_dir / "README.md").write_text(f"# {name}\n\nAuthor: {author}\n", encoding="utf-8")
        return plugin_dir

    def stats(self) -> dict[str, Any]:
        return {
            "dir": str(self.dir),
            "count": len(self.list_plugins()),
            "plugins": [p.name for p in self.list_plugins()],
        }


_SDK: PluginSDK | None = None


def get_sdk() -> PluginSDK:
    global _SDK
    if _SDK is None:
        _SDK = PluginSDK()
    return _SDK


__all__ = ["PLUGINS_DIR", "PluginManifest", "PluginSDK", "get_sdk"]
