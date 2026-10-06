#!/usr/bin/env python3
"""Авто-генерация цифр в документации (раздел 19 промта).

Наука (Д4):
- Раздел 19 промта: цифры должны генерироваться, не вручную.
- DRY (Hunt & Thomas 1999, Pragmatic Programmer).

Запуск: python scripts/update_docs.py
"""
from __future__ import annotations
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def get_agents() -> int:
    r = subprocess.run(
        [sys.executable, "-c",
         "from aura.bootstrap import build_orchestrator; "
         "o=build_orchestrator(); print(len(o.registry.list_names()))"],
        capture_output=True, text=True, cwd=ROOT,
    )
    return int(r.stdout.strip().split("\n")[-1])


def get_tests() -> int:
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "--collect-only", "-q"],
        capture_output=True, text=True, cwd=ROOT,
    )
    m = re.search(r"(\d+)\s+tests? collected", r.stdout)
    return int(m.group(1)) if m else 0


def get_adr() -> int:
    return len(list((ROOT / "docs" / "adr").glob("*.md")))


# Карта: файл → список (pattern, template) для замены
# template: {n} = новая цифра
FILES_TO_UPDATE = {
    "README.md": [
        (r"\b\d+\s+агент(?:ов|а)?\b", "{n} агентов"),
    ],
    "MANIFESTO.md": [
        (r"\b\d+\s+агент(?:ов|а)?\b", "{n} агентов"),
        (r"\b\d+\s+тест(?:ов|а)?\b", "{n} тестов"),
        (r"\b\d+\s+ADR\b", "{n} ADR"),
    ],
    "docs/MANIFESTO.md": [
        (r"\b\d+\s+агент(?:ов|а)?\b", "{n} агентов"),
        (r"\b\d+\s+тест(?:ов|а)?\b", "{n} тестов"),
        (r"\b\d+\s+ADR\b", "{n} ADR"),
    ],
    "docs/architecture.md": [
        (r"\b\d+\s+агент(?:ов|а)?\b", "{n} агентов"),
        (r"\b\d+\s+тест(?:ов|а)?\b", "{n} тестов"),
    ],
    "docs/architecture-diagram.md": [
        (r"Registry\s+\d+\s+агент(?:ов|а)?", "Registry {n} агентов"),
    ],
    "docs/sponsorship.md": [
        (r"\b\d+\s+агент(?:ов|а)?\b", "{n} агентов"),
        (r"\b\d+\s+тест(?:ов|а)?\b", "{n} тестов"),
    ],
    "docs/habr-guide.md": [
        (r"\b\d+\+?\s+тест(?:ов|а)?\b", "{n}+ тестов"),
        (r"\b\d+\s+агент(?:ов|а)?\b", "{n} агентов"),
        (r"\b\d+\s+ADR\b", "{n} ADR"),
    ],
    "docs/release-checklist.md": [
        (r"\b\d+\s+агент(?:ов|а)?\b", "{n} агентов"),
        (r"\b\d+\s+ADR\b", "{n} ADR"),
    ],
}


def update_file(rel_path: str, replacements: list, agents: int, tests: int, adr: int):
    p = ROOT / rel_path
    if not p.exists():
        print(f"  ⏭  {rel_path}: нет файла")
        return
    src = p.read_text(encoding="utf-8")
    orig = src

    for pattern, template in replacements:
        # Заменяем ВСЕ совпадения на актуальное число
        # Определяем {n} по контексту
        def repl(m):
            ctx = m.group(0).lower()
            if "агент" in ctx:
                n = agents
            elif "тест" in ctx:
                n = tests
            elif "adr" in ctx:
                n = adr
            else:
                n = agents  # default
            return template.format(n=n)

        src = re.sub(pattern, repl, src, flags=re.IGNORECASE)

    if src != orig:
        p.write_text(src, encoding="utf-8")
        print(f"  ✅ {rel_path}")
    else:
        print(f"  ⏭  {rel_path}: без изменений")


def main():
    print("Собираю реальные цифры...")
    agents = get_agents()
    tests = get_tests()
    adr = get_adr()
    print(f"  agents: {agents}")
    print(f"  tests:  {tests}")
    print(f"  adr:    {adr}")
    print()
    print("Обновляю документы:")
    for rel_path, replacements in FILES_TO_UPDATE.items():
        update_file(rel_path, replacements, agents, tests, adr)
    print()
    print("✅ Готово")


if __name__ == "__main__":
    main()
