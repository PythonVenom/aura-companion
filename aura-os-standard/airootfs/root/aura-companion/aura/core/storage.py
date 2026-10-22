"""Storage routing (ADR-XXX): HDD vs SSD fallback."""
import os
from pathlib import Path

HDD_MOUNT = Path("/mnt/aura_hdd")

def get_storage_root() -> Path:
    """Возвращает корень для тяжелых данных (HDD или fallback)."""
    if HDD_MOUNT.exists() and os.access(HDD_MOUNT, os.W_OK):
        return HDD_MOUNT
    # Fallback на домашнюю директорию, если HDD нет
    fallback = Path.home() / ".cache" / "aura"
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback

def get_rag_db_path() -> Path:
    """Путь для ChromaDB."""
    path = get_storage_root() / "rag_db"
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_ollama_models_path() -> Path:
    """Путь для моделей Ollama."""
    path = get_storage_root() / "ollama"
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_media_path() -> Path:
    """Путь для медиа (музыка, видео)."""
    path = get_storage_root() / "media"
    path.mkdir(parents=True, exist_ok=True)
    return path
