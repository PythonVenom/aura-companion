"""Агент Steam: Deck Verified, Workshop, запуск."""
from __future__ import annotations

import json
import subprocess
import urllib.parse
import urllib.request

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


class AgentSteam(BaseAgent):
    name = "steam"
    MODULE_ALWAYS = True

    KEYWORDS = (
        "steam", "стим", "deck verified", "верифицирован",
        "workshop", "воркшоп", "мастерская",
    )

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower()
        return any(kw in t for kw in self.KEYWORDS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        t = request.text.lower()

        if "deck verified" in t or "верифицирован" in t:
            game = self._extract_game(request.text)
            if not game:
                return AgentResponse.ok("Укажи игру: 'проверь deck verified для <игра>'.", self.name)
            return AgentResponse.ok(self.check_deck_verified(game), self.name)

        if "workshop" in t or "воркшоп" in t or "мастерская" in t:
            app_id = self._extract_app_id(request.text)
            if not app_id:
                return AgentResponse.ok("Укажи AppID: 'скачай воркшоп <app_id>'.", self.name)
            return AgentResponse.ok(self.download_workshop(app_id), self.name)

        if "запусти steam" in t or "открой steam" in t or "включи steam" in t:
            return AgentResponse.ok(self.launch_steam(), self.name)

        return AgentResponse.not_handled(self.name)

    def _extract_game(self, text: str) -> str:
        for prep in (" для ", " про ", " игры "):
            if prep in text.lower():
                return text.split(prep, 1)[1].strip()
        return ""

    def _extract_app_id(self, text: str) -> str:
        import re
        m = re.search(r"\b(\d{3,10})\b", text)
        return m.group(1) if m else ""

    def check_deck_verified(self, game: str) -> str:
        """Проверка Deck Verified через Steam Store API."""
        try:
            search_url = (
                "https://store.steampowered.com/api/storesearch/"
                f"?term={urllib.parse.quote(game)}&l=russian&cc=RU"
            )
            req = urllib.request.Request(search_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read().decode("utf-8"))
            items = data.get("items", [])
            if not items:
                return f"❌ Игра «{game}» не найдена в Steam."
            app_id = items[0]["id"]
            name = items[0]["name"]

            details_url = (
                f"https://store.steampowered.com/api/appdetails?appids={app_id}&l=russian&cc=RU"
            )
            req = urllib.request.Request(details_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as r:
                details = json.loads(r.read().decode("utf-8"))
            app_data = details.get(str(app_id), {}).get("data", {})
            deck = app_data.get("deck_compatibility", "unknown")
            mapping = {
                "verified": "✅ Verified (идеально для Deck)",
                "playable": "🟡 Playable (играбельно, но с нюансами)",
                "unsupported": "❌ Unsupported (не поддерживается)",
                "unknown": "⚪ Неизвестно (нет данных)",
            }
            return f"🎮 {name} (AppID {app_id}): {mapping.get(deck, deck)}"
        except Exception as e:
            return f"❌ Ошибка Steam API: {e}"

    def download_workshop(self, app_id: str) -> str:
        """Скачивание Workshop-контента через steamcmd."""
        try:
            r = subprocess.run(["which", "steamcmd"], capture_output=True, text=True)
            if r.returncode != 0:
                return "❌ steamcmd не установлен. Установи: sudo pacman -S steamcmd"
            cmd = [
                "steamcmd", "+login", "anonymous",
                "+workshop_download_item", app_id, "all",
                "+quit",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                return f"✅ Workshop для AppID {app_id} скачан (см. ~/.steam/steamcmd/workshop)."
            return f"⚠️ steamcmd вернул код {result.returncode}: {result.stderr[:200]}"
        except subprocess.TimeoutExpired:
            return "⚠️ steamcmd выполнялся слишком долго (>2 мин)."
        except Exception as e:
            return f"❌ Ошибка Workshop: {e}"

    def launch_steam(self) -> str:
        try:
            subprocess.Popen(["steam"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return "🎮 Steam запущен."
        except FileNotFoundError:
            return "❌ Steam не установлен. Установи: sudo pacman -S steam"
        except Exception as e:
            return f"❌ Ошибка запуска Steam: {e}"


__all__ = ["AgentSteam"]
