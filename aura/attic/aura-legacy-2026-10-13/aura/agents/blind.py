"""Blind accessibility agent. T047 — озвучка уведомлений.

Наука:
- D-Bus: org.freedesktop.Notifications (freedesktop.org spec)
- TTS: speech-dispatcher (spd-say) → espeak-ng fallback
- dbus-monitor подпроцессом, парсинг Notify
"""
from __future__ import annotations

import re
import shutil
import subprocess
import threading

from aura.agents.base import MicroAgent
from aura.core.protocol import AgentRequest, AgentResponse


class AgentBlind(MicroAgent):
    name = "blind"

    TRIGGERS = ("уведомлени", "озвучь", "слепые", "незряч", "голосом читай")

    _monitor_proc = None
    _monitor_thread = None

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower()
        return any(kw in t for kw in self.TRIGGERS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        t = request.text.lower()
        if any(k in t for k in ("включи", "запусти", "начни")):
            return self._start()
        if any(k in t for k in ("выключи", "стоп", "останови")):
            return self._stop()
        if "статус" in t:
            return self._status()
        return AgentResponse.ok(
            text="Слепые: 'включи озвучку уведомлений' / 'выключи' / 'статус'.",
            agent_name=self.name,
        )

    def _tts_cmd(self):
        if shutil.which("spd-say"):
            return ["spd-say", "-w"]
        if shutil.which("espeak-ng"):
            return ["espeak-ng", "-v", "ru"]
        if shutil.which("espeak"):
            return ["espeak", "-v", "ru"]
        return None

    def _speak(self, text: str) -> None:
        cmd = self._tts_cmd()
        if not cmd:
            return
        try:
            subprocess.run([*cmd, text], timeout=30, check=False)
        except Exception as e:
            # F-006: не глотать (раздел 17 промта)
            import logging
            logging.getLogger('aura.blind').debug(
                'blind error: %s', e)

    def _start(self) -> AgentResponse:
        if self._monitor_proc and self._monitor_proc.poll() is None:
            return AgentResponse.ok(text="🔔 Озвучка уже включена.", agent_name=self.name)
        if not shutil.which("dbus-monitor"):
            return AgentResponse.ok(
                text="⚠️ Нет dbus-monitor (пакет dbus).",
                agent_name=self.name,
            )
        if not self._tts_cmd():
            return AgentResponse.ok(
                text="⚠️ Нет TTS: поставь speech-dispatcher или espeak-ng.",
                agent_name=self.name,
            )

        self._monitor_proc = subprocess.Popen(
            ["dbus-monitor", "interface='org.freedesktop.Notifications'"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1,
        )
        speak = self._speak

        def _loop(proc):
            summary = None
            body = None
            in_notify = False
            for line in proc.stdout:
                line = line.strip()
                if "member=Notify" in line:
                    in_notify = True
                    summary = body = None
                    continue
                if not in_notify:
                    continue
                m = re.search(r'string "([^"]+)"', line)
                if not m:
                    continue
                val = m.group(1)
                if val in ("", "Aura", "notify-send"):
                    continue
                if summary is None:
                    summary = val
                elif body is None:
                    body = val
                    in_notify = False
                    msg = summary if not body else f"{summary}. {body}"
                    speak(msg[:300])

        self._monitor_thread = threading.Thread(target=_loop, args=(self._monitor_proc,), daemon=True)
        self._monitor_thread.start()
        self._speak("Озвучка уведомлений включена")
        return AgentResponse.ok(text="🔔 Озвучка уведомлений включена.", agent_name=self.name)

    def _stop(self) -> AgentResponse:
        if self._monitor_proc and self._monitor_proc.poll() is None:
            self._monitor_proc.terminate()
            try:
                self._monitor_proc.wait(timeout=2)
            except Exception:
                self._monitor_proc.kill()
        self._monitor_proc = None
        return AgentResponse.ok(text="🔕 Озвучка выключена.", agent_name=self.name)

    def _status(self) -> AgentResponse:
        running = self._monitor_proc is not None and self._monitor_proc.poll() is None
        tts = self._tts_cmd()
        return AgentResponse.ok(
            text=f"🔔 Озвучка: {'включена' if running else 'выключена'}. "
                 f"TTS: {tts[0] if tts else 'нет'}.",
            agent_name=self.name,
        )
