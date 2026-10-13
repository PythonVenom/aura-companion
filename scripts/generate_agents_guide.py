"""#102 — Генератор AGENTS_GUIDE.md из 96 агентов.

Читает bootstrap.py → список агентов → их KEYWORDS → markdown.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).parent.parent
BOOTSTRAP = REPO / "aura/bootstrap.py"
OUT = REPO / "docs/AGENTS_GUIDE.md"


def extract_agents() -> list[dict]:
    """Парсит bootstrap.py → список агентов с категориями."""
    src = BOOTSTRAP.read_text()
    agents = []

    # Ищем строки _try_register с комментариями уровней
    # Формат: _try_register(orch, AgentX, modules_config)  # комментарий
    # Секция: # --- Уровень N: ...
    current_level = "Прочее"
    for line in src.splitlines():
        level_match = re.search(r"# --- Уровень \d+: (.+?) ---", line)
        if level_match:
            current_level = level_match.group(1).strip()
            continue

        reg_match = re.search(r"_try_register\(orch, (Agent\w+)", line)
        if reg_match:
            cls_name = reg_match.group(1)
            comment = line.split("#", 1)[1].strip() if "#" in line.split("_try_register", 1)[1] else ""
            agents.append({
                "class": cls_name,
                "level": current_level,
                "comment": comment,
            })

    return agents


def extract_keywords(cls_name: str) -> list[str]:
    """Пытается найти KEYWORDS/TRIGGERS в файле агента."""
    # snake_case из CamelCase
    short = cls_name.replace("Agent", "", 1)
    snake = re.sub(r"(?<!^)(?=[A-Z])", "_", short).lower()
    candidates = [
        REPO / f"aura/agents/{snake}.py",
        REPO / f"aura/agents/{snake.replace('_', '')}.py",
    ]
    for f in candidates:
        if not f.exists():
            continue
        src = f.read_text()
        # KEYWORDS = (...) или TRIGGERS = (...)
        m = re.search(r"(?:KEYWORDS|TRIGGERS)\s*=\s*\(([^)]+)\)", src, re.S)
        if m:
            kws = re.findall(r'"([^"]+)"', m.group(1))
            return kws[:6]  # первые 6
    return []


def main() -> None:
    agents = extract_agents()
    print(f"Найдено агентов: {len(agents)}")

    # Группируем по уровню
    by_level: dict[str, list[dict]] = {}
    for a in agents:
        by_level.setdefault(a["level"], []).append(a)

    lines = [
        "# 🤖 Aura — Гид по агентам",
        "",
        f"> Автогенерация: `scripts/generate_agents_guide.py`  ",
        f"> Всего агентов: **{len(agents)}**  ",
        f"> Категорий: **{len(by_level)}**",
        "",
        "---",
        "",
    ]

    for level, items in by_level.items():
        lines.append(f"## {level} ({len(items)})")
        lines.append("")
        lines.append("| Агент | Триггеры | Пример |")
        lines.append("|-------|----------|--------|")
        for a in items:
            cls = a["class"].replace("Agent", "", 1)
            kws = extract_keywords(a["class"])
            trigger = ", ".join(f"«{k}»" for k in kws) if kws else "—"
            example = f"«Аура, {kws[0]}»" if kws else "—"
            lines.append(f"| `{cls}` | {trigger} | {example} |")
        lines.append("")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"✅ {OUT}: {len(lines)} строк")


if __name__ == "__main__":
    main()
