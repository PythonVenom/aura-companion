"""Avatar — виртуальное тело AURA (Godot/Live2D/VRM).

Наука: Embodiment Spectrum (Pfeifer 2007).
Формат: VRM 0.x (совместим с Godot, Unity, Three.js).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Avatar:
    """Виртуальное тело AURA."""
    name: str = "Aura"
    model_path: Path | None = None
    format: str = "vrm"  # vrm | live2d | mmd | pngtuber
    emotion: str = "neutral"
    speaking: bool = False
    _loaded: bool = field(default=False, init=False)

    def load(self) -> bool:
        """Загрузить модель."""
        if self.model_path and self.model_path.exists():
            self._loaded = True
            return True
        return False

    @property
    def ready(self) -> bool:
        return self._loaded

    def set_emotion(self, emotion: str) -> None:
        """Установить эмоцию (neutral, happy, sad, thinking)."""
        self.emotion = emotion

    def speak(self, text: str) -> None:
        """Проиграть анимацию речи (задел)."""
        self.speaking = True

    def stop_speak(self) -> None:
        self.speaking = False

    def status(self) -> dict:
        return {
            "name": self.name,
            "format": self.format,
            "loaded": self._loaded,
            "emotion": self.emotion,
            "speaking": self.speaking,
        }


_AVATAR: Avatar | None = None


def get_avatar() -> Avatar:
    global _AVATAR
    if _AVATAR is None:
        _AVATAR = Avatar()
    return _AVATAR


__all__ = ["Avatar", "get_avatar"]
