#!/usr/bin/env python3
"""
АУРА — новая точка входа (модульная архитектура).

Переиспользует слух (AgentListener) и голос (AgentSpeaker) из старой папки agents/.
Роутинг команд — через aura.bootstrap.build_orchestrator().

Запускается только если AURA_USE_ORCHESTRATOR=1 (см. run_aura.sh).
Старый aura_core.py остаётся fallback.

По науке:
- Голос/слух не переизобретаем — берём проверенные классы
- Роутинг — через Orchestrator (модульный)
- Опасные действия (power, window_control, app_launcher) — как в монолите
- Легко откатить: убрать флаг в run_aura.sh
"""

import asyncio
import subprocess
import sys
import time

# Слух и голос — из старой папки agents/ (проверенные, работают)
from agents.listener import AgentListener
from agents.speaker import AgentSpeaker

# Новая модульная сборка
from aura.bootstrap import build_orchestrator


class AuraOrchestrator:
    """
    Новая Аура: слух + голос (старые) + Orchestrator (новый).
    """

    def __init__(self) -> None:
        self.listener = AgentListener()
        self.speaker = AgentSpeaker()
        self.orch = build_orchestrator()
        self.running = True

    def run(self) -> None:
        """Главный цикл — как в монолите, но process() через Orchestrator."""
        print("\n" + "=" * 60)
        print("🦾 АУРА — ORCHESTRATOR v0.8")
        print("🔴 Скажи 'Аура' для активации")
        print(f"📦 Агентов в Orchestrator: {len(self.orch)}")
        print("=" * 60)
        print(f"\n✅ Загружено: {self.orch.registry.list_names()}\n")

        self.listener.active = True
        self.speaker.active = True

        while self.running:
            try:
                # Анти-эхо: не слушаем, пока говорим
                if self.speaker.is_speaking:
                    time.sleep(0.1)
                    continue

                # Слушаем (timeout 5 секунд)
                heard = self.listener.listen(timeout=5)

                if not heard:
                    time.sleep(0.1)
                    continue

                if 'аура' not in heard.lower() and 'aura' not in heard.lower():
                    time.sleep(0.1)
                    continue

                print("🔔 Активация!")
                cmd = heard.replace('аура', '').replace('aura', '').strip()
                cmd = cmd.replace('Аура', '').replace('Aura', '').strip()

                # Понижаем громкость во время обработки (как в монолите)
                try:
                    subprocess.run(
                        ['pactl', 'set-sink-volume', '@DEFAULT_SINK@', '30%'],
                        check=False,
                    )
                except Exception:
                    pass

                if not cmd:
                    time.sleep(0.3)
                    continue

                print(f"📝 Команда: {cmd}")

                # === ГЛАВНОЕ ОТЛИЧИЕ: process через Orchestrator ===
                self.speaker.active = True
                response = asyncio.run(self.orch.process(cmd))
                print(f"🤖 {response}")
                self.speaker.say(response)

                # Ждём окончания речи
                if self.speaker.aplay_process:
                    self.speaker.aplay_process.wait()

                # Пауза между командами
                if "\n" in response:
                    time.sleep(1.5)
                else:
                    time.sleep(0.5)
                self.speaker.active = False

                # Возвращаем громкость
                try:
                    subprocess.run(
                        ['pactl', 'set-sink-volume', '@DEFAULT_SINK@', '100%'],
                        check=False,
                    )
                except Exception:
                    pass

                time.sleep(0.1)

            except KeyboardInterrupt:
                print("\n🦾 Аура: До свидания! 👋")
                break
            except Exception as e:
                print(f"❌ Ошибка: {e}")
                time.sleep(0.5)


def main() -> int:
    aura = AuraOrchestrator()
    aura.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
