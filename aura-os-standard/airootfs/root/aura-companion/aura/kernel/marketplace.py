"""Marketplace — установка агентов из репо."""
import json
import logging
from pathlib import Path

log = logging.getLogger("aura.marketplace")
LOCAL_DIR = Path.home() / ".local/share/aura/agents"


class Marketplace:
    def __init__(self):
        LOCAL_DIR.mkdir(parents=True, exist_ok=True)

    def list_installed(self) -> list:
        return [json.loads(f.read_text()) for f in LOCAL_DIR.glob("*.json")]

    def install(self, agent_id: str, source: str) -> bool:
        try:
            meta = {"id": agent_id, "source": source, "version": "0.1.0"}
            (LOCAL_DIR / f"{agent_id}.json").write_text(
                json.dumps(meta, ensure_ascii=False, indent=2))
            return True
        except Exception as e:
            log.warning("install failed: %s", e)
            return False

    def uninstall(self, agent_id: str) -> bool:
        path = LOCAL_DIR / f"{agent_id}.json"
        if path.exists():
            path.unlink()
            return True
        return False
