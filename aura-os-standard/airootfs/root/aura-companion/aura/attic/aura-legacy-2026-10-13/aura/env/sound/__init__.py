"""Sound adapters."""
from .base import SoundAdapter
from .pipewire import PipeWireAdapter
from .pulseaudio import PulseAudioAdapter

__all__ = ["PipeWireAdapter", "PulseAudioAdapter", "SoundAdapter", "get_sound"]


def get_sound():
    from aura.env.detect import detect
    if detect()["sound"] == "pipewire":
        return PipeWireAdapter()
    return PulseAudioAdapter()
