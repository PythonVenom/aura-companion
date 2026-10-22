"""#34 WineLauncher — запуск .exe через wine.

По науке:
- Изолирован (os, subprocess, glob, shutil)
- Тестируем (mock для subprocess, monkeypatch для which)
- Graceful degradation: если wine нет — сообщить как поставить

Паттерн: как app_launcher.py, но для .exe и wine.
"""
from __future__ import annotations

import shutil
import subprocess
from difflib import get_close_matches
from pathlib import Path

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


class AgentWineLauncher(BaseAgent):
    """
    Агент запуска .exe через wine.

    Обрабатывает:
    - "запусти <exe>" / "открой <игру>"     → run
    - "закрой wine" / "убей wine"           → kill
    - "список exe" / "какие exe есть"       → list_exe
    """

    name = "wine_launcher"

    RUN_KEYWORDS = ("запусти wine", "запусти exe", "открой exe",
                    "включи виндовс", "запусти виндовс")
    KILL_KEYWORDS = ("закрой wine", "убей wine", "убей exe", "стоп wine")
    LIST_KEYWORDS = ("список exe", "какие exe", "что за exe")

    SEARCH_DIRS = [
        Path.home() / "Games",
        Path.home() / ".wine/drive_c",
        Path.home() / "Загрузки",
        Path.home() / "Downloads",
        Path("/mnt/aura_hdd"),
        Path("/mnt"),
    ]

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower()
        return any(kw in t for kw in self.RUN_KEYWORDS + self.KILL_KEYWORDS + self.LIST_KEYWORDS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        t = request.text.lower()
        if not shutil.which("wine"):
            return AgentResponse.ok(
                text="⚠️ wine не установлен. Установи: sudo pacman -S wine",
                agent_name=self.name,
            )
        if any(kw in t for kw in self.KILL_KEYWORDS):
            return self._kill()
        if any(kw in t for kw in self.LIST_KEYWORDS):
            return self._list()
        return self._run(request.text)

    def _run(self, text: str) -> AgentResponse:
        # Пытаемся извлечь имя из "запусти X.exe"
        query = text.lower()
        for kw in self.RUN_KEYWORDS:
            if kw in query:
                query = query.split(kw, 1)[1].strip()
                break

        found = self._find_exe(query)
        if not found:
            return AgentResponse.ok(
                text=f"❌ Не нашёл .exe по запросу «{query}». Скажи точнее.",
                agent_name=self.name,
            )

        try:
            subprocess.Popen(
                ["wine", str(found)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return AgentResponse.ok(
                text=f"🚀 Запускаю через wine: {found.name}",
                agent_name=self.name,
            )
        except Exception as e:
            return AgentResponse.ok(
                text=f"❌ Ошибка wine: {e}",
                agent_name=self.name,
            )

    def _kill(self) -> AgentResponse:
        try:
            subprocess.run(["wineserver", "-k"], check=False, timeout=5)
            return AgentResponse.ok(text="🛑 wine закрыт (wineserver -k)", agent_name=self.name)
        except Exception as e:
            return AgentResponse.ok(text=f"❌ {e}", agent_name=self.name)

    def _list(self) -> AgentResponse:
        exes = self._scan_exes()
        if not exes:
            return AgentResponse.ok(
                text="❌ .exe не найдено в стандартных папках.",
                agent_name=self.name,
            )
        # Берём первые 20
        lines = [f"  • {p.name}" for p in exes[:20]]
        return AgentResponse.ok(
            text=f"📂 Найдено {len(exes)} .exe:\n" + "\n".join(lines),
            agent_name=self.name,
        )

    def _find_exe(self, query: str) -> Path | None:
        """Fuzzy-поиск .exe по имени."""
        query = query.replace(".exe", "").strip()
        if not query:
            return None
        exes = self._scan_exes()
        names = {p.name.lower().replace(".exe", ""): p for p in exes}
        # Точное совпадение
        if query in names:
            return names[query]
        # Fuzzy
        matches = get_close_matches(query, list(names.keys()), n=1, cutoff=0.5)
        return names[matches[0]] if matches else None

    def _scan_exes(self) -> list[Path]:
        """Сканирует SEARCH_DIRS на *.exe (max 500)."""
        result: list[Path] = []
        for base in self.SEARCH_DIRS:
            if not base.exists():
                continue
            try:
                for p in base.rglob("*.exe"):
                    result.append(p)
                    if len(result) >= 500:
                        return result
            except (PermissionError, OSError):
                continue
        return result


__all__ = ["AgentWineLauncher"]
