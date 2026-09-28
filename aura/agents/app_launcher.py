"""
Агент запуска приложений.

Ищет .desktop-файлы, запускает через gtk-launch / прямой exec.
Закрывает через pkill / flatpak kill.

По науке:
- Изолирован (os, subprocess, glob)
- Тестируем (mock для subprocess)
- Не знает про AuraCore
"""

from __future__ import annotations

import glob
import os
import subprocess
from difflib import get_close_matches

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


class AgentAppLauncher(BaseAgent):
    """
    Агент управления приложениями.

    Обрабатывает:
    - "открой X" / "запусти X" → open_app
    - "закрой X" → close_app
    - "список приложений" / "какие приложения" → list_apps
    """

    name = "app_launcher"
    MODULE_ALWAYS = True

    OPEN_KEYWORDS = ("открой", "запусти", "открыть", "запустить")
    CLOSE_KEYWORDS = ("закрой", "закрыть", "выключи приложение")
    LIST_KEYWORDS = ("список приложений", "какие приложения")

    APP_DIRS = [
        "/usr/share/applications",
        "/usr/local/share/applications",
        os.path.expanduser("~/.local/share/applications"),
        "/var/lib/flatpak/exports/share/applications",
        os.path.expanduser("~/.local/share/flatpak/exports/share/applications"),
    ]

    BLACKLIST = (
        "flatpak",
        "telegram-desktop",
        "chrome",
        "browser",
        "java",
        "python",
        "sh",
        "bash",
    )

    def __init__(self) -> None:
        super().__init__()
        self._apps_cache: dict[str, dict] = {}
        self._scan_apps()

    def _scan_apps(self) -> None:
        """Сканировать .desktop-файлы."""
        for d in self.APP_DIRS:
            if not os.path.exists(d):
                continue
            for f in glob.glob(f"{d}/*.desktop"):
                try:
                    name = None
                    exec_cmd = None
                    with open(f, "r", encoding="utf-8", errors="ignore") as fh:
                        for line in fh:
                            if line.startswith("Name=") and not name:
                                name = line.split("=", 1)[1].strip()
                            elif line.startswith("Exec=") and not exec_cmd:
                                exec_cmd = line.split("=", 1)[1].strip()
                                exec_cmd = exec_cmd.split("%")[0].strip()
                    if name and exec_cmd:
                        key = name.lower()
                        if key not in self._apps_cache:
                            self._apps_cache[key] = {
                                "name": name,
                                "exec": exec_cmd,
                                "file": f,
                            }
                except Exception:
                    pass

    def can_handle(self, request: AgentRequest) -> bool:
        text = request.text.lower()
        keywords = self.OPEN_KEYWORDS + self.CLOSE_KEYWORDS + self.LIST_KEYWORDS
        return any(kw in text for kw in keywords)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        text = request.text.lower()

        if any(kw in text for kw in self.LIST_KEYWORDS):
            return AgentResponse.ok(self.list_apps(), self.name)

        if any(kw in text for kw in self.CLOSE_KEYWORDS):
            name = self._extract_name(text, self.CLOSE_KEYWORDS)
            if not name:
                return AgentResponse.ok("Что закрыть?", self.name)
            return AgentResponse.ok(self.close_app(name), self.name, silent=True)

        if any(kw in text for kw in self.OPEN_KEYWORDS):
            name = self._extract_name(text, self.OPEN_KEYWORDS)
            if not name:
                return AgentResponse.ok("Что открыть?", self.name)
            return AgentResponse.ok(self.open_app(name), self.name, silent=True)

        return AgentResponse.not_handled(self.name)

    # --- Внутренние методы ---

    @staticmethod
    def _extract_name(text: str, keywords: tuple[str, ...]) -> str:
        for kw in keywords:
            if kw in text:
                return text.replace(kw, "").strip()
        return ""

    # Bug 35: алиасы для ASR-ошибок и русских названий
    ALIASES = {
        "фаерфокс": "firefox", "файрфакс": "firefox",
        "файрфокс": "firefox", "эрфокс": "firefox",
        "фэйфокс": "firefox", "файфокс": "firefox",
        "файэфокс": "firefox", "браузер": "firefox",
        "фокс": "firefox",
        "телеграм": "telegram", "тг": "telegram",
        "телега": "telegram",
        "хром": "chromium", "хромиум": "chromium",
        "код": "code", "вскод": "code", "вс код": "code",
        "калька": "libreoffice", "офис": "libreoffice",
        "музыка": "vlc",
    }

    def find_app(self, query: str) -> dict | None:
        query_lower = query.lower().strip()
        if not query_lower:
            return None
        # Bug 35: сначала алиасы
        if query_lower in self.ALIASES:
            query_lower = self.ALIASES[query_lower]
        if query_lower in self._apps_cache:
            return self._apps_cache[query_lower]
        for name, info in self._apps_cache.items():
            if query_lower in name or name in query_lower:
                return info
        matches = get_close_matches(query_lower, list(self._apps_cache.keys()), n=1, cutoff=0.5)
        if matches:
            return self._apps_cache[matches[0]]
        return None

    def open_app(self, name: str) -> str:
        app = self.find_app(name)
        if not app:
            return f"❌ Приложение '{name}' не найдено"
        try:
            subprocess.Popen(
                app["exec"].split(),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return f"✅ Открыл: {app['name']}"
        except Exception as e:
            return f"❌ Не удалось открыть '{app['name']}': {e}"

    def close_app(self, name: str) -> str:
        # Flatpak
        try:
            result = subprocess.run(
                ["flatpak", "list", "--app", "--columns=application,name"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            name_lower = name.lower()
            for line in result.stdout.split("\n"):
                if not line.strip():
                    continue
                parts = line.split("\t")
                if len(parts) >= 2:
                    app_id, app_name = parts[0], parts[1]
                    if name_lower in app_name.lower() or name_lower in app_id.lower():
                        subprocess.run(["flatpak", "kill", app_id], check=False)
                        return f"✅ Закрыл: {app_name}"
        except Exception:
            pass

        # Native
        candidates = [name]
        app = self.find_app(name)
        if app:
            exec_first = app["exec"].split()[0]
            candidates.insert(0, os.path.basename(exec_first))

        for cand in candidates:
            if not cand or cand.lower() in self.BLACKLIST:
                continue
            try:
                result = subprocess.run(
                    ["pkill", "-ix", cand], check=False, capture_output=True
                )
                if result.returncode == 0:
                    return f"✅ Закрыл: {cand}"
                result = subprocess.run(
                    ["pkill", "-if", cand], check=False, capture_output=True
                )
                if result.returncode == 0:
                    return f"✅ Закрыл: {cand}"
            except Exception:
                pass

        return f"❌ Процесс '{name}' не найден"

    def list_apps(self, filter_text: str = "") -> str:
        filter_lower = filter_text.lower().strip()
        apps = []
        for name, info in self._apps_cache.items():
            if not filter_lower or filter_lower in name:
                apps.append(info["name"])
        apps.sort()
        if not apps:
            return f"❌ Не найдено приложений по '{filter_text}'"
        result = f"📱 Приложений: {len(apps)}\n\n"
        for i, name in enumerate(apps[:50], 1):
            result += f"{i}. {name}\n"
        if len(apps) > 50:
            result += f"\n... и ещё {len(apps) - 50}"
        return result


__all__ = ["AgentAppLauncher"]
