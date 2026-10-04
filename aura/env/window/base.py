"""Абстрактный WindowManager."""
from abc import ABC, abstractmethod


class WindowManager(ABC):
    name: str = "unknown"

    @abstractmethod
    def list_windows(self) -> list:
        pass

    @abstractmethod
    def focus(self, window_id: str) -> bool:
        pass

    @abstractmethod
    def switch_desktop(self, n: int) -> bool:
        pass

    @abstractmethod
    def close(self, window_id: str) -> bool:
        pass
