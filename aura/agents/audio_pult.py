"""
Агент аудио-пульта.

Управляет громкостью через pactl.
Поддерживает: громкость 0-100, громче/тише, mute/unmute.

По науке:
- Изолирован (только subprocess)
- Тестируем (mock для pactl)
- Не знает про AuraCore
"""

from __future__ import annotations

import re
import subprocess

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


class AgentAudioPult(BaseAgent):
    """
    Агент управления громкостью.

    Обрабатывает:
    - "громкость 5" / "громкость 50" → установить
    - "громче" / "прибавь" → +10%
    - "тише" / "убавь" → -10%
    - "выключи звук" / "mute" → mute
    - "включи звук" / "unmute" → unmute
    """

    name = "audio_pult"
    MODULE_ALWAYS = True

    VOLUME_KEYWORDS = ("громкость", "громко", "звук")
    LOUDER_KEYWORDS = ("громче", "прибавь", "плюс", "увеличь", "добавь")
    QUIETER_KEYWORDS = ("тише", "убавь", "минус", "уменьши", "сделай меньше")
    MUTE_KEYWORDS = ("выключи звук", "звук на ноль", "mute")
    UNMUTE_KEYWORDS = ("включи звук", "unmute", "верни звук")

    DIGIT_WORDS = {
        "один": 1, "одна": 1, "одну": 1,
        "два": 2, "две": 2, "двух": 2,
        "три": 3, "трех": 3, "трёх": 3,
        "четыре": 4, "четырех": 4, "четырёх": 4,
        "пять": 5, "пяти": 5,
        "шесть": 6, "шести": 6,
        "семь": 7, "семи": 7,
        "восемь": 8, "восьми": 8,
        "девять": 9, "девяти": 9,
        "десять": 10, "десяти": 10,
    }

    def can_handle(self, request: AgentRequest) -> bool:
        text = request.text.lower()
        keywords = (
            self.VOLUME_KEYWORDS
            + self.LOUDER_KEYWORDS
            + self.QUIETER_KEYWORDS
            + self.MUTE_KEYWORDS
            + self.UNMUTE_KEYWORDS
        )
        return any(kw in text for kw in keywords)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        text = request.text.lower()

        if any(kw in text for kw in self.MUTE_KEYWORDS):
            return AgentResponse.ok(self._mute(), self.name)

        if any(kw in text for kw in self.UNMUTE_KEYWORDS):
            return AgentResponse.ok(self._unmute(), self.name)

        # Громче
        if any(kw in text for kw in self.LOUDER_KEYWORDS):
            delta = self._extract_delta(text, default=10)
            return AgentResponse.ok(self._change_volume_by(delta), self.name)

        # Тише
        if any(kw in text for kw in self.QUIETER_KEYWORDS):
            delta = self._extract_delta(text, default=10)
            return AgentResponse.ok(self._change_volume_by(-delta), self.name)

        # Установить громкость
        target = self._extract_volume(text)
        if target is not None:
            return AgentResponse.ok(self._set_volume(target), self.name)

        return AgentResponse.not_handled(self.name)

    # --- Внутренние методы ---

    def _extract_volume(self, text: str) -> int | None:
        """Извлечь громкость. 'громкость 5' -> 50, 'громкость 50' -> 50"""
        nums = re.findall(r"\b(\d{1,3})\b", text)
        if nums:
            v = int(nums[0])
            if v >= 100:
                return 100
            return v if v > 10 else v * 10

        for word, num in self.DIGIT_WORDS.items():
            if word in text:
                return num * 10
        return None

    def _extract_delta(self, text: str, default: int = 10) -> int:
        """Извлечь дельту. 'громче на 3' -> 30, 'громче на 30' -> 30"""
        nums = re.findall(r"\b(\d{1,3})\b", text)
        if nums:
            v = int(nums[0])
            return v if v > 10 else v * 10

        for word, num in self.DIGIT_WORDS.items():
            if word in text:
                return num * 10

        return default

    def _get_current_volume(self) -> int:
        try:
            result = subprocess.run(
                ["pactl", "get-sink-volume", "@DEFAULT_SINK@"],
                capture_output=True,
                text=True,
                check=False,
            )
            return int(result.stdout.split()[4].strip("%"))
        except Exception:
            return 50

    def _set_volume(self, target_percent: int) -> str:
        try:
            target_percent = max(0, min(100, target_percent))
            subprocess.run(
                ["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{target_percent}%"],
                check=False,
            )
            return f"🔊 Громкость: {target_percent // 10} из 10 ({target_percent}%)"
        except Exception:
            return "🔊 Не удалось установить громкость"

    def _change_volume_by(self, delta_percent: int) -> str:
        try:
            current = self._get_current_volume()
            target = max(0, min(100, current + delta_percent))
            subprocess.run(
                ["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{target}%"],
                check=False,
            )
            return f"🔊 Громкость: {target // 10} из 10 ({target}%)"
        except Exception:
            return "🔊 Не удалось изменить громкость"

    def _mute(self) -> str:
        try:
            subprocess.run(
                ["pactl", "set-sink-mute", "@DEFAULT_SINK@", "1"],
                check=False,
            )
            return "🔇 Звук выключен"
        except Exception:
            return "🔇 Не удалось выключить звук"

    def _unmute(self) -> str:
        try:
            subprocess.run(
                ["pactl", "set-sink-mute", "@DEFAULT_SINK@", "0"],
                check=False,
            )
            return "🔊 Звук включен"
        except Exception:
            return "🔊 Не удалось включить звук"


__all__ = ["AgentAudioPult"]
