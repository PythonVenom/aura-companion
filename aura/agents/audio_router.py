"""
Агент аудио-маршрутизации.

Определяет, что подключено: jack, USB, Bluetooth.
Автоматически переключает вход и выход PulseAudio.

Мигрирован из agents/audio_router.py (монолит).
Изменения при миграции:
- Убран import __main__ (агент больше не лезет за speaker через глобал)
- Убран метод check_and_route (совмещал детект + голос) —
  вместо него чистый check_route(), возвращающий (profile, message)
- Контракт BaseAgent: can_handle / handle

Наука:
- Агент не знает про оркестратор и про speaker
- Если нужно уведомить пользователя — возвращаем текст, решает вызывающий
"""

from __future__ import annotations

import subprocess
import time

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


class AgentAudioRouter(BaseAgent):
    """
    Аудио-маршрутизатор.

    Обрабатывает запросы:
    - "проверь аудио" / "аудио статус"
    - "какая гарнитура" / "что подключено"
    - "переключи аудио"

    Плюс публичный метод check_route() — для периодического
    вызова из главного цикла (раз в 5 секунд).
    """

    name = "audio_router"
    MODULE_ALWAYS = True

    # Интервал проверки в главном цикле (секунды)
    CHECK_INTERVAL = 5

    # Ключевые слова для can_handle
    KEYWORDS = (
        "проверь аудио",
        "аудио статус",
        "переключи аудио",
        "какая гарнитура",
        "что подключено",
    )

    # Хардкод устройств (Realtek ALC1220 на текущем железе)
    # TODO: вынести в конфиг, когда понадобится кроссплатформенность
    DEFAULT_SOURCE = "alsa_input.pci-0000_00_1f.3.analog-stereo"
    DEFAULT_SINK = "alsa_output.pci-0000_00_1f.3.analog-stereo"

    def __init__(self) -> None:
        self.current_profile: str | None = None
        self.current_source: str | None = None
        self.current_sink: str | None = None
        self.last_check: float = 0.0
        # Первичный детект при создании — как в монолите
        self.detect_and_route()

    # --- Публичный API для главного цикла ---

    def check_route(self) -> tuple[str, str | None]:
        """
        Проверить маршрут (не чаще CHECK_INTERVAL секунд).

        Возвращает (profile, message | None):
        - message=None — ничего не поменялось, молчим
        - message=str — профиль сменился, есть что сказать

        Вызывающий сам решает, озвучивать ли message.
        """
        now = time.time()
        if now - self.last_check < self.CHECK_INTERVAL:
            return (self.current_profile or "unknown", None)
        self.last_check = now

        profile, message = self.detect_and_route()
        return (profile, message)

    def get_status(self) -> dict[str, str | None]:
        """Текущий профиль, вход, выход."""
        return {
            "profile": self.current_profile,
            "source": self.current_source,
            "sink": self.current_sink,
        }

    # --- Контракт BaseAgent ---

    def can_handle(self, request: AgentRequest) -> bool:
        text = request.text.lower()
        return any(kw in text for kw in self.KEYWORDS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        cmd = request.text.lower()

        if "проверь аудио" in cmd or "аудио статус" in cmd:
            status = self.get_status()
            return AgentResponse.ok(
                text=(
                    f"🎧 Аудио: {status['profile']}\n"
                    f"Вход: {status['source']}\n"
                    f"Выход: {status['sink']}"
                ),
                agent_name=self.name,
            )

        if "переключи аудио" in cmd:
            self.current_profile = None
            _, message = self.detect_and_route()
            return AgentResponse.ok(
                text=message or "🔧 Аудио-маршрутизация обновлена.",
                agent_name=self.name,
            )

        if "какая гарнитура" in cmd or "что подключено" in cmd:
            profile = self._detect_profile()
            names = {
                "headset": "🎧 Гарнитура (jack)",
                "internal": "🔊 Встроенные (микрофон и динамики)",
                "usb": "🎙️ USB-аудио",
                "bluetooth": "📡 Bluetooth-аудио",
                "unknown": "❓ Неизвестно",
            }
            return AgentResponse.ok(
                text=names.get(profile, "❓ Неизвестно"),
                agent_name=self.name,
            )

        # can_handle сказал True, но ни одна ветка не сработала
        return AgentResponse.not_handled(agent_name=self.name)

    # --- Внутренние методы (логика pactl, не изменена) ---

    def _run_pactl(self, args: list[str]) -> str:
        try:
            result = subprocess.run(
                ["pactl"] + args,
                capture_output=True,
                text=True,
                timeout=3,
            )
            return result.stdout.strip()
        except Exception:
            return ""

    def _get_active_port(self, source_or_sink: str, name: str) -> str | None:
        try:
            result = subprocess.run(
                ["pactl", "list", source_or_sink],
                capture_output=True,
                text=True,
                timeout=3,
            )
            lines = result.stdout.split("\n")
            for i, line in enumerate(lines):
                if name in line:
                    for j in range(i, min(i + 40, len(lines))):
                        if "Active Port:" in lines[j]:
                            return lines[j].split(":", 1)[1].strip()
            return None
        except Exception:
            return None

    def _detect_profile(self) -> str:
        """
        Определяет профиль по активному ПОРТУ ВЫХОДА.
        headphones = jack вставлен, speaker = jack вынут.
        """
        try:
            output_port = self._get_active_port("sinks", "alsa_output")

            if output_port:
                if "analog-output-headphones" in output_port:
                    return "headset"
                elif "analog-output-speaker" in output_port:
                    return "internal"

            result = self._run_pactl(["list", "sources", "short"])
            if "usb" in result.lower():
                return "usb"
            if "bluez" in result.lower():
                return "bluetooth"

            return "unknown"
        except Exception:
            return "unknown"

    def _set_default_source(self, name: str) -> bool:
        try:
            subprocess.run(
                ["pactl", "set-default-source", name],
                capture_output=True,
                timeout=3,
            )
            return True
        except Exception:
            return False

    def _set_default_sink(self, name: str) -> bool:
        try:
            subprocess.run(
                ["pactl", "set-default-sink", name],
                capture_output=True,
                timeout=3,
            )
            return True
        except Exception:
            return False

    def _fix_speaker_volume(self) -> None:
        """
        Поднимает Speaker на 100%, если он упал в 0.
        Нужно для Realtek ALC1220, который обнуляет Speaker
        при переключении профиля.
        """
        subprocess.run(
            [
                "pactl",
                "set-sink-volume",
                "alsa_output.pci-0000_00_1f.3.analog-stereo",
                "100%",
            ],
            capture_output=True,
            timeout=3,
        )

    def _ensure_real_sink(self) -> None:
        """Bug 10: если default sink = echo-cancel — переключить на реальный.

        echo-cancel-sink даёт троение звука (эхо-дублирование при playback).
        Проверка быстрая (~50 мс), идемпотентная.
        """
        try:
            r = subprocess.run(
                ["pactl", "info"],
                capture_output=True, text=True, timeout=2,
            )
            for line in r.stdout.split("\n"):
                if line.startswith("Default Sink:"):
                    current = line.split(":", 1)[1].strip()
                    if "echo-cancel" in current:
                        # Найти реальный sink
                        r2 = subprocess.run(
                            ["pactl", "list", "short", "sinks"],
                            capture_output=True, text=True, timeout=2,
                        )
                        for s_line in r2.stdout.split("\n"):
                            parts = s_line.split("\t")
                            if len(parts) >= 2 and "echo-cancel" not in parts[1]:
                                subprocess.run(
                                    ["pactl", "set-default-sink", parts[1]],
                                    capture_output=True, timeout=2,
                                )
                                print(f"🔊 Sink: {current} → {parts[1]}")
                                break
                    break
        except Exception as e:
            print(f"⚠️ _ensure_real_sink: {e}")

    def detect_and_route(self) -> tuple[str, str | None]:
        """
        Определить профиль и, если сменился, переключить вход/выход.

        Возвращает (profile, message | None).
        """
        self._ensure_real_sink()
        profile = self._detect_profile()
        old_profile = self.current_profile
        self.current_profile = profile

        if old_profile == profile:
            return (profile, None)
        # Bug 42: при первом вызове (old=None) silent только для default-профилей
        # (internal/headset). USB/Bluetooth — реальная смена → сообщаем.
        if old_profile is None and profile in ("internal", "headset"):
            self.current_source = self.DEFAULT_SOURCE
            self.current_sink = self.DEFAULT_SINK
            return (profile, None)

        if profile in ("headset", "internal"):
            # НЕ трогаем default-source/sink: PipeWire управляет сам,
            # audio_router выбивал echo-cancel-source (AEC слетал).
            # См. ADR-007.
            self.current_source = self.DEFAULT_SOURCE
            self.current_sink = self.DEFAULT_SINK
            self._fix_speaker_volume()

            if profile == "headset":
                return (profile, "🎧 Обнаружена гарнитура. Слушаю через микрофон, говорю в наушники.")
            else:
                return (profile, "🔊 Гарнитура отключена. Использую встроенный микрофон и динамики.")

        if profile == "usb":
            self._fix_speaker_volume()
            return (profile, "🎙️ Обнаружено USB-аудио. Использую его.")

        if profile == "bluetooth":
            self._fix_speaker_volume()
            return (profile, "📡 Обнаружено Bluetooth-аудио. Использую его.")

        return (profile, "🔧 Аудио-маршрутизация обновлена.")


__all__ = ["AgentAudioRouter"]
