"""#Блок 6 — модули Aura: красивый вывод агентов по категориям.

Категории = 10 уровней регистрации в bootstrap.py:
  1. Простые и точные (time, power, vault)
  2. Узкий ducking (music_ducker — до audio_pult)
  3. audio_pult — широкие «громче/тише»
  4. Дневник, память, реестр, функции, обновления, security
  5. Аудио-маршрутизация
  6. X11 (vision, focus_switch, window_manager, context_memory, text_editor)
  7. Специфичные «открой X» (vk_music, browser_tabs)
  8. Опасные, но широкие (app_launcher, window_control, screen_reader)
  9. Медиа (media_search — перехватывает «включи»)
 10. Internet — последний (общий «найди»)

Категория агента определяется по эвристике (имя класса → группа).
"""
from __future__ import annotations

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent

# Категории: эвристика по префиксам/именам классов
CATEGORIES = {
    "🕐 Простые": ("Time", "Power", "Vault", "Capabilities"),
    "🎵 Ducking": ("MusicDucker",),
    "🔊 Audio": ("AudioPult", "AudioRouter"),
    "📓 Память/Журнал": ("Journal", "Registry", "Functions", "Updates",
                         "Security", "Captain", "Checklist", "VoiceJournal"),
    "🎤 Голос": ("Voice", "Listener", "Speaker", "Dictation", "BargeIn"),
    "🖥️  X11": ("Vision", "FocusSwitch", "WindowManager", "ContextMemory",
                "TextEditor", "AtSpi", "ScreenReader", "WindowControl"),
    "🌐  Специфичные": ("VKMusic", "VKWeb", "BrowserTabs", "Telegram",
                        "Messenger", "Email", "WhatsApp", "SMS", "MediaSearch"),
    "🛠️  Опасные": ("AppLauncher", "HandsFree", "Mouse", "PCControl",
                    "DesktopControl", "UnifiedRouter", "ToolRouter"),
    "🏥 Elder-care": ("SOS", "Meds", "MedsOffline", "Fall", "Call",
                      "FinElder", "Blind", "BlindReply", "ProactiveAlert",
                      "AdaptiveReminders", "KidStructure", "KidTherapy",
                      "HealthTwin", "Onboarding", "RoutineLearner",
                      "EmotionVoice", "SoulTalk", "Reminiscence"),
    "🏠 Smart Home": ("HomeAssistant", "Matter", "Sensors", "CEC"),
    "🎮 Игры/Космос": ("ParallelUniverse", "Construction", "BPM",
                       "Greeting", "Predictor", "React", "Knowledge",
                       "Planner", "TaskManager", "Calendar", "DeepCheck",
                       "DeepSeekWeb", "RecentActivity", "FocusMode"),
    "🔧 Наши новые": ("WineLauncher", "TuyaBLE", "OBDScanner", "SelfCheck"),
    "❓ Прочее": (),  # fallback
}


def _category(name: str) -> str:
    """Определить категорию по имени класса (без префикса Agent)."""
    short = name.replace("Agent", "", 1)
    for cat, names in CATEGORIES.items():
        if short in names:
            return cat
    # Fallback: поиск по подстроке
    for cat, names in CATEGORIES.items():
        for n in names:
            if n and (n.lower() in short.lower()):
                return cat
    return "❓ Прочее"


class AgentModules(BaseAgent):
    """Вывод списка агентов Aura по категориям."""

    name = "modules"

    KEYWORDS = (
        "список модулей", "список агентов", "какие агенты", "какие модули",
        "аура модули", "аура агенты", "покажи модули", "покажи агентов",
        "сколько агентов", "сколько модулей",
    )

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower()
        return any(kw in t for kw in self.KEYWORDS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        # Пытаемся получить orchestrator (он внедряется в self)
        orch = getattr(self, "orchestrator", None)
        if orch is None or not hasattr(orch, "registry"):
            return AgentResponse.ok(
                text="⚠️ Orchestrator не подключён к AgentModules.",
                agent_name=self.name,
            )
        try:
            names = orch.registry.list_names()
        except Exception as e:
            return AgentResponse.ok(
                text=f"❌ Не удалось получить список: {e}",
                agent_name=self.name,
            )

        # Исключаем плагины (plugin_*) и служебные
        names = [n for n in names if not n.startswith("plugin_")]

        # Группируем
        by_cat: dict[str, list[str]] = {}
        for n in sorted(names):
            cat = _category(n)
            by_cat.setdefault(cat, []).append(n)

        # Формируем вывод
        total = sum(len(v) for v in by_cat.values())
        lines = [f"🤖 Aura: {total} агентов в {len(by_cat)} категориях", ""]
        for cat in sorted(by_cat.keys()):
            items = by_cat[cat]
            lines.append(f"{cat} ({len(items)})")
            for n in items:
                lines.append(f"  • {n}")
            lines.append("")

        return AgentResponse.ok(
            text="\n".join(lines).rstrip(),
            agent_name=self.name,
        )


__all__ = ["CATEGORIES", "AgentModules", "_category"]
