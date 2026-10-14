"""#143 Rules Engine — IFTTT-правила для Aura.

Наука:
- ECA (Event-Condition-Action, McCarthy 1993) — стандарт reactive systems
- IFTTT (Linden 2011) — «если X → то Y»
- Reactive Manifesto (2014) — event-driven, resilient

Правило: {"name", "event", "conditions", "action"}
Пример: {"name": "утро", "event": "sunrise",
         "conditions": {}, "action": {"agent": "scenes", "cmd": "доброе утро"}}

Хранение: ~/.config/aura/rules.json
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

RULES_PATH = Path.home() / ".config/aura/rules.json"


@dataclass
class Rule:
    name: str
    event: str
    action: dict
    conditions: dict = field(default_factory=dict)
    enabled: bool = True


def load() -> list[Rule]:
    if not RULES_PATH.exists():
        return []
    try:
        data = json.loads(RULES_PATH.read_text(encoding="utf-8"))
        return [Rule(**r) for r in data.get("rules", [])]
    except Exception:
        return []


def save(rules: list[Rule]) -> None:
    RULES_PATH.parent.mkdir(parents=True, exist_ok=True)
    RULES_PATH.write_text(
        json.dumps({"rules": [asdict(r) for r in rules]},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def add(name: str, event: str, action: dict, conditions: dict | None = None) -> Rule:
    rules = load()
    rules = [r for r in rules if r.name != name]
    r = Rule(name=name, event=event, action=action,
             conditions=conditions or {})
    rules.append(r)
    save(rules)
    return r


def remove(name: str) -> bool:
    rules = load()
    before = len(rules)
    rules = [r for r in rules if r.name != name]
    if len(rules) == before:
        return False
    save(rules)
    return True


def match(event: str) -> list[Rule]:
    """Правила для события."""
    return [r for r in load() if r.enabled and r.event == event]


def format_rules() -> str:
    rules = load()
    if not rules:
        return "📋 Правил нет."
    lines = [f"📋 Правил: {len(rules)}"]
    for r in rules:
        status = "✅" if r.enabled else "❌"
        act = r.action.get("cmd") or r.action.get("agent", "?")
        lines.append(f"  {status} {r.name}: on {r.event} → {act}")
    return "\n".join(lines)


__all__ = ["RULES_PATH", "Rule", "add", "format_rules", "load", "match", "remove", "save"]
