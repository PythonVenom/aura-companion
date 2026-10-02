"""Единые пути проекта (ADR-106)."""
from pathlib import Path
import os

PROJECT_DIR = Path(os.environ.get("AURA_PROJECT_DIR", Path(__file__).parent.parent))
HOME = Path.home()
CACHE_DIR = Path(os.environ.get("AURA_CACHE_DIR", HOME / ".cache/aura"))
CONFIG_DIR = Path(os.environ.get("AURA_CONFIG_DIR", HOME / ".config/aura"))
DATA_DIR = CACHE_DIR
MODELS_DIR = PROJECT_DIR

def ensure():
    for d in (CACHE_DIR, CONFIG_DIR):
        d.mkdir(parents=True, exist_ok=True)

__all__ = ["PROJECT_DIR", "HOME", "CACHE_DIR", "CONFIG_DIR", "DATA_DIR", "MODELS_DIR", "ensure"]
