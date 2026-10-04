from abc import ABC, abstractmethod


class SoundAdapter(ABC):
    name: str = "unknown"

    @abstractmethod
    def get_default_source(self) -> str:
        pass

    @abstractmethod
    def set_volume(self, pct: int) -> bool:
        pass

    @abstractmethod
    def list_sinks(self) -> list:
        pass
