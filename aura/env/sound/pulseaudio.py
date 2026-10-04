"""PulseAudio — тот же pactl API."""
from .pipewire import PipeWireAdapter


class PulseAudioAdapter(PipeWireAdapter):
    name = "pulseaudio"
