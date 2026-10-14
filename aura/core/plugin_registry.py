"""#146 PluginRegistry — реестр плагинов (marketplace).

Наука:
- App Store (2008) — централизованный реестр
- npm registry (Isaac 2010) — распределённые пакеты + метаданные
- Homebrew (2009) — формула + index

Зачем:
  PluginManager устанавливает локально. Registry — каталог:
  - где искать плагины (URL, локальные пути)
  - метаданные (автор, версия, лицензия, зависимости)
  - поиск по тегам

Формат manifest.json:
  {
    "id": "vk_music",
    "name": "VK Music",
    "version": "1.0.0",
    "author": "PythonVenom",
    "license": "MIT",
    "description": "...",
    "tags": ["music", "vk"],
    "source": "https://github.com/...",
    "requires": ["aura>=8.0"]
  }
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

REGISTRY_PATH = Path.home() / ".config/aura/plugin_registry.json"


@dataclass
class PluginMeta:
    """Метаданные плагина."""
    id: str
    name: str
    version: str
    author: str = ""
    license: str = "MIT"
    description: str = ""
    tags: list[str] = field(default_factory=list)
    source: str = ""
    requires: list[str] = field(default_factory=list)


def load() -> list[PluginMeta]:
    if not REGISTRY_PATH.exists():
        return _default_registry()
    try:
        data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        return [PluginMeta(**p) for p in data.get("plugins", [])]
    except Exception:
        return _default_registry()


def save(plugins: list[PluginMeta]) -> None:
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_PATH.write_text(
        json.dumps({"plugins": [asdict(p) for p in plugins]},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def register(meta: PluginMeta) -> PluginMeta:
    """Добавить/обновить плагин в реестре."""
    plugins = load()
    plugins = [p for p in plugins if p.id != meta.id]
    plugins.append(meta)
    save(plugins)
    return meta


def unregister(plugin_id: str) -> bool:
    plugins = load()
    before = len(plugins)
    plugins = [p for p in plugins if p.id != plugin_id]
    if len(plugins) == before:
        return False
    save(plugins)
    return True


def find(plugin_id: str) -> PluginMeta | None:
    for p in load():
        if p.id == plugin_id:
            return p
    return None


def search(query: str) -> list[PluginMeta]:
    """Поиск по имени/описанию/тегам."""
    q = query.lower()
    if not q:
        return []
    results = []
    for p in load():
        if (q in p.id.lower()
                or q in p.name.lower()
                or q in p.description.lower()
                or any(q in t.lower() for t in p.tags)):
            results.append(p)
    return results


def by_tag(tag: str) -> list[PluginMeta]:
    return [p for p in load() if tag in p.tags]


def format_registry(query: str | None = None) -> str:
    plugins = search(query) if query else load()
    if not plugins:
        return "📋 Плагинов нет."
    lines = [f"🛒 Реестр: {len(plugins)} плагинов"]
    for p in plugins[:20]:
        tag_str = ", ".join(p.tags[:3]) if p.tags else "—"
        lines.append(f"  • {p.name} v{p.version} [{tag_str}] — {p.author}")
    return "\n".join(lines)


def _default_registry() -> list[PluginMeta]:
    """Встроенный стартовый реестр."""
    return [
        PluginMeta(
            id="vk_music", name="VK Music", version="1.0.0",
            author="PythonVenom", license="MIT",
            description="Музыка ВКонтакте",
            tags=["music", "vk"], source="builtin",
        ),
        PluginMeta(
            id="homeassistant", name="Home Assistant", version="1.0.0",
            author="PythonVenom", license="MIT",
            description="Умный дом через Home Assistant",
            tags=["smarthome", "iot"], source="builtin",
        ),
    ]


__all__ = [
    "PluginMeta", "load", "save", "register", "unregister",
    "find", "search", "by_tag", "format_registry",
]
