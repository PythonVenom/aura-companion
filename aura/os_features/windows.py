"""Windows — OS feature adapters (T-os-4).

Наука:
- SAPI 5.4 (Microsoft 2006) — Speech API
- Windows.Media.SpeechRecognition (UWP 2015) — modern ASR
- Windows Hello (Microsoft 2015) — биометрия (FIDO2)
- .NET System.Speech — программный TTS
- Microsoft Learn 2020 — Win32 / PowerShell API

Доступ:
- SAPI TTS через PowerShell: Add-Type + System.Speech.Synthesis.SpeechSynthesizer
- ASR через Windows.Media.SpeechRecognition (WinRT)
- Hello через Windows.Security.Credentials.UI
- Registry через winreg (Python stdlib)
"""
from __future__ import annotations
import platform
import shutil
import subprocess
from pathlib import Path


def _is_windows() -> bool:
    return platform.system().lower() == "windows"


def _has_powershell() -> bool:
    return shutil.which("powershell") is not None or \
           shutil.which("pwsh") is not None


class SAPIAdapter:
    """SAPI 5.4 — TTS через .NET System.Speech.

    Использование:
        a = SAPIAdapter()
        if a.available():
            a.speak("Привет", voice="Irina")
    """

    name = "sapi"

    def available(self) -> bool:
        return _is_windows() and _has_powershell()

    def speak(self, text: str, voice: str = "Irina") -> bool:
        """Произнести текст. voice — имя голоса (Irina = ru-RU)."""
        if not self.available():
            return False
        try:
            ps = (
                'Add-Type -AssemblyName System.Speech; '
                '$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; '
                f'$s.SelectVoice("{voice}"); '
                f'$s.Speak("{text.replace(chr(34), chr(39))}");'
            )
            r = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps],
                timeout=60, check=False,
                capture_output=True, text=True,
            )
            return r.returncode == 0
        except Exception:
            return False

    def list_voices(self) -> list[str]:
        """Список установленных TTS-голосов."""
        if not self.available():
            return []
        try:
            ps = (
                'Add-Type -AssemblyName System.Speech; '
                '$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; '
                '$s.GetInstalledVoices() | ForEach-Object '
                '{ $_.VoiceInfo.Name }'
            )
            r = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps],
                timeout=15, check=False,
                capture_output=True, text=True,
            )
            if r.returncode != 0:
                return []
            return [v.strip() for v in r.stdout.splitlines() if v.strip()]
        except Exception:
            return []


class WSRAdapter:
    """Windows Speech Recognition (WinRT). ASR.

    Placeholder — WinRT требует особого биндинга.
    Реализация через speech_recognition + Windows.Media.
    """

    name = "wsr"

    def available(self) -> bool:
        return _is_windows()

    def listen(self, timeout: int = 5) -> str | None:
        """Слушать и вернуть текст. Placeholder — None."""
        return None


class HelloAdapter:
    """Windows Hello — биометрия (FIDO2 / PIN / face).

    Placeholder. Через Windows.Security.Credentials.UI.
    """

    name = "hello"

    def available(self) -> bool:
        return _is_windows()

    def verify(self, message: str = "Aura: подтверди доступ") -> bool:
        """Проверить биометрию. Placeholder — False."""
        return False


class RegistryAdapter:
    """winreg — реестр Windows (Python stdlib).

    Наука: Microsoft Registry API.
    Используется для autostart (CurrentVersion\\Run).
    """

    name = "registry"

    def available(self) -> bool:
        if not _is_windows():
            return False
        try:
            import winreg  # noqa: F401
            return True
        except ImportError:
            return False

    def set_autostart(self, name: str, exe_path: Path | str) -> bool:
        """Добавить в автозагрузку (HKCU\\...\\Run)."""
        if not self.available():
            return False
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_SET_VALUE,
            )
            winreg.SetValueEx(key, name, 0, winreg.REG_SZ, str(exe_path))
            winreg.CloseKey(key)
            return True
        except Exception:
            return False

    def get_autostart(self, name: str) -> str | None:
        """Прочитать значение автозагрузки."""
        if not self.available():
            return None
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_READ,
            )
            try:
                val, _ = winreg.QueryValueEx(key, name)
                return str(val)
            finally:
                winreg.CloseKey(key)
        except FileNotFoundError:
            return None
        except Exception:
            return None


class DefenderAdapter:
    """Windows Defender — cooperative scan (placeholder).

    Не блокирует Aura: Aura может запросить проверку через
    MpCmdRun.exe, но не автоматически.
    """

    name = "defender"

    def available(self) -> bool:
        if not _is_windows():
            return False
        return shutil.which("MpCmdRun.exe") is not None or \
               Path(r"C:\Program Files\Windows Defender\MpCmdRun.exe").exists()

    def scan(self, path: Path | str) -> bool:
        """Запросить проверку файла. Placeholder — False."""
        return False


__all__ = [
    "SAPIAdapter", "WSRAdapter", "HelloAdapter",
    "RegistryAdapter", "DefenderAdapter",
]
