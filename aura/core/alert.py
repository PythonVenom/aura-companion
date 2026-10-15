"""Alert — отправка boot-report в Telegram (если есть ключ).

Наука: Alerting Best Practices (SRE Book, Google).
Только для статуса != ok. Иначе тишина.
"""
from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path

ALERT_LOG = Path.home() / ".cache" / "aura" / "alerts.log"


def _telegram_send(text: str) -> bool:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        return False
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = json.dumps({"chat_id": chat_id, "text": text}).encode()
        req = urllib.request.Request(url, data=data,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status == 200
    except Exception:
        return False


def send_boot_alert() -> str:
    """Отправить boot-report если статус != ok."""
    try:
        from aura.core.boot_report import run_boot_report
        rep = run_boot_report()
        if rep.status == "ok":
            return "ok (no alert)"
        text = f"🛸 AURA Boot Report\n{rep.to_text()}"
        if _telegram_send(text):
            return "sent to telegram"
        # Fallback: лог
        ALERT_LOG.parent.mkdir(parents=True, exist_ok=True)
        with ALERT_LOG.open("a", encoding="utf-8") as f:
            f.write(text + "\n---\n")
        return "logged locally"
    except Exception as e:
        return f"error: {e}"


def main() -> None:
    print(send_boot_alert())


if __name__ == "__main__":
    main()


__all__ = ["send_boot_alert"]
