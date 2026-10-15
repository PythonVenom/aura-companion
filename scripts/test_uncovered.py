"""Deep test: авто-прогон непокрытых агентов.

Для каждого агента берём его KEYWORDS/TRIGGERS и генерируем тест-фразу.
Цель: увидеть, кто из 72 «непокрытых» реально живой.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

UNCOVERED = [
    "AgentAdaptiveReminders", "AgentAtSpi", "AgentAudioRouter", "AgentBPM",
    "AgentBlind", "AgentBlindReply", "AgentCEC", "AgentCalendar",
    "AgentChecklist", "AgentClipboard", "AgentConstruction", "AgentContextMemory",
    "AgentContextRecall", "AgentDeepSeekWeb", "AgentDictation", "AgentEmotionVoice",
    "AgentEveningRitual", "AgentFDIR", "AgentFederatedAdapter", "AgentFocusSwitch",
    "AgentFunctions", "AgentHandsFree", "AgentHealth", "AgentHealthTwin",
    "AgentHomeAssistant", "AgentKidStructure", "AgentKidTherapy", "AgentMQTT",
    "AgentMassage", "AgentMatter", "AgentMcp", "AgentMediaSearch",
    "AgentMedsOffline", "AgentMessenger", "AgentModules", "AgentMouse",
    "AgentNaptime", "AgentOnboarding", "AgentParallelUniverse", "AgentPlanner",
    "AgentPower", "AgentProactiveAlert", "AgentRAGMemory", "AgentReact",
    "AgentRecon", "AgentRegistry", "AgentReminiscence", "AgentRoutineLearner",
    "AgentRules", "AgentScenes", "AgentScreenReader", "AgentSecurity",
    "AgentSelfCheck", "AgentSelfHeal", "AgentSensors", "AgentSoulTalk",
    "AgentTaskManager", "AgentTelegram", "AgentTextEditor", "AgentTimeAgent",
    "AgentTutorial", "AgentTuyaBLE", "AgentUpdates", "AgentVKMusic",
    "AgentVKWeb", "AgentVisualAnalysis", "AgentWellness", "AgentWindowControl",
    "AgentWineLauncher", "BriefingAgent", "CareAgent", "PluginAgentWrapper",
]


async def main() -> None:
    print("=" * 70)
    print("  DEEP TEST — 72 непокрытых агентов")
    print("=" * 70)

    from aura.bootstrap import build_orchestrator
    from aura.core.protocol import AgentRequest

    orch = build_orchestrator()
    agents_by_name = {type(a).__name__: a for a in orch.registry._agents}

    stats = {"instantiated": 0, "has_keywords": 0, "can_handle_any": 0,
             "missing_class": 0, "no_keywords": 0}

    for name in UNCOVERED:
        agent = agents_by_name.get(name)
        if agent is None:
            print(f"  ❌ {name:30s} НЕ В РЕЕСТРЕ")
            stats["missing_class"] += 1
            continue
        stats["instantiated"] += 1

        # Собираем keywords/triggers
        kws: list[str] = []
        for attr in ("KEYWORDS", "TRIGGERS", "PHRASES", "GREETINGS",
                     "HOW_ARE_YOU", "THANKS", "SOS_PHRASES"):
            v = getattr(agent, attr, None)
            if isinstance(v, (list, tuple)):
                kws.extend([str(k) for k in v if isinstance(k, str)])

        if not kws:
            print(f"  ⚠️  {name:30s} нет KEYWORDS (проверка can_handle)")
            stats["no_keywords"] += 1
            continue
        stats["has_keywords"] += 1

        # Проверяем первый keyword
        test_phrase = kws[0]
        req = AgentRequest(text=test_phrase)
        try:
            if agent.can_handle(req):
                stats["can_handle_any"] += 1
                print(f"  ✅ {name:30s} <- «{test_phrase[:40]}»")
            else:
                print(f"  🟡 {name:30s} can_handle=False на «{test_phrase[:40]}»")
        except Exception as e:
            print(f"  ❌ {name:30s} ERROR: {e}")

    print()
    print("=" * 70)
    print("  ИТОГ")
    print("=" * 70)
    for k, v in stats.items():
        print(f"  {k:20s}: {v}")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
