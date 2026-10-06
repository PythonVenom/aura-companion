"""Windows: WASAPI + WinAPI + MPRIS (через pywin32).

Зависимости:
- pycaw (WASAPI)
- pywin32 (WinAPI)
- winsdk (уведомления)
"""
from __future__ import annotations


class WindowsAudio:
    """WASAPI через pycaw (если установлен)."""

    def __init__(self):
        self.ready = False
        try:
            from pycaw.pycaw import AudioUtilities
            self.AudioUtilities = AudioUtilities
            self.ready = True
        except ImportError:
            pass

    def list_sinks(self) -> list[str]:
        if not self.ready:
            return []
        try:
            devices = self.AudioUtilities.GetAllDevices()
            return [str(d.FriendlyName) for d in devices]
        except Exception:
            return []

    def list_sources(self) -> list[str]:
        return []

    def get_default_sink(self) -> str:
        if not self.ready:
            return ""
        try:
            return str(self.AudioUtilities.GetSpeakers().FriendlyName)
        except Exception:
            return ""

    def set_default_sink(self, name: str) -> bool:
        # Требует nircmd или SoundVolumeView
        return False

    def duck(self, level: float = 0.2) -> None:
        if not self.ready:
            return
        try:
            speakers = self.AudioUtilities.GetSpeakers()
            volume = speakers.EndpointVolume
            volume.SetMasterVolumeLevelScalar(level, None)
        except Exception:
            pass

    def unduck(self) -> None:
        if not self.ready:
            return
        try:
            speakers = self.AudioUtilities.GetSpeakers()
            volume = speakers.EndpointVolume
            volume.SetMasterVolumeLevelScalar(1.0, None)
        except Exception:
            pass


class WindowsService:
    def enable_autostart(self) -> bool:
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\\Microsoft\\Windows\\CurrentVersion\\Run",
                0, winreg.KEY_SET_VALUE,
            )
            winreg.SetValueEx(key, "Aura", 0, winreg.REG_SZ,
                              "pythonw.exe -m aura_main")
            winreg.CloseKey(key)
            return True
        except Exception:
            return False

    def disable_autostart(self) -> bool:
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\\Microsoft\\Windows\\CurrentVersion\\Run",
                0, winreg.KEY_SET_VALUE,
            )
            winreg.DeleteValue(key, "Aura")
            winreg.CloseKey(key)
            return True
        except Exception:
            return False

    def notify(self, title: str, body: str) -> None:
        try:
            from win10toast import ToastNotifier
            ToastNotifier().show_toast(title, body, duration=5)
        except Exception:
            pass


class WindowsMedia:
    """MPRIS через WMI или SMTC (pywin32)."""

    def list_players(self) -> list[str]:
        # Windows: через GlobalSystemMediaTransportControls
        return []

    def pause_all(self) -> bool:
        try:
            import winsdk.windows.media.control as wmc
            return False  # TODO: async
        except ImportError:
            return False

    def resume_all(self) -> bool:
        return False

    def get_last_active(self) -> str | None:
        from aura.agents import media_state
        return media_state.get_active()


__all__ = ["WindowsAudio", "WindowsMedia", "WindowsService"]
