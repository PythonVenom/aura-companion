"""HAL base — абстрактный интерфейс платформы.

Наука:
- Hardware Abstraction Layer (Tanenbaum, «Modern OS»)
- POSIX (IEEE 1003.1) — базовые примитивы
- Design by contract (Meyer 1986) — интерфейс = контракт

Все платформы (Linux, Windows, macOS, BSD, Android) реализуют этот
интерфейс. Aura ядро знает только BasePlatform — не платформу.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable


class BasePlatform(ABC):
    """Абстрактный HAL. Каждая ОС реализует эти методы."""

    name: str = "base"

    # --- Пути ---
    @abstractmethod
    def config_dir(self) -> Path:
        """Каталог конфигов (XDG_CONFIG_HOME или аналог)."""

    @abstractmethod
    def data_dir(self) -> Path:
        """Каталог данных (XDG_DATA_HOME или аналог)."""

    @abstractmethod
    def cache_dir(self) -> Path:
        """Каталог кэша."""

    # --- Аудио ---
    @abstractmethod
    def audio_play(self, path: Path) -> None:
        """Проиграть аудиофайл через системный плеер."""

    @abstractmethod
    def audio_record(self, seconds: int, out: Path) -> bool:
        """Записать с микрофона. True если успешно."""

    # --- Уведомления ---
    @abstractmethod
    def notify(self, title: str, body: str) -> bool:
        """Показать системное уведомление."""

    # --- TTS ---
    @abstractmethod
    def speak(self, text: str) -> bool:
        """Произнести текст через системный TTS."""

    # --- Clipboard ---
    @abstractmethod
    def clipboard_get(self) -> str:
        """Получить содержимое буфера обмена."""

    @abstractmethod
    def clipboard_set(self, text: str) -> bool:
        """Установить содержимое буфера обмена."""

    # --- Запуск ---
    @abstractmethod
    def open_url(self, url: str) -> bool:
        """Открыть URL в браузере по умолчанию."""

    @abstractmethod
    def open_file(self, path: Path) -> bool:
        """Открыть файл ассоциированным приложением."""

    # --- Дополнительно: с автофолбэком ---
    def safe(self, fn: Callable, default=None):
        """Выполнить fn, при ошибке вернуть default. Для graceful degradation."""
        try:
            return fn()
        except Exception:
            return default


__all__ = ["BasePlatform"]
