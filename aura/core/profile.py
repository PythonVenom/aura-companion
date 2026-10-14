"""#12 User Profile — агрегатор разбросанных JSON-файлов.

Проблема:
  Профиль размазан по 5+ файлам:
    ~/.config/aura/profile          (имя)
    ~/.config/aura/settings.json    (persona, wake_word, sos_phrases)
    ~/.config/aura/sos.json         (контакт SOS: имя + телефон)
    ~/.config/aura/fin_elder.json   (пенсия, ЖКХ)
    ~/.config/aura/safety.json      (proactive_alert, sos.enabled)

Решение:
  Единый объект UserProfile, который АГРЕГИРУЕТ существующие файлы.
  Не дублирует, не перемещает — только читает.
  save() пишет только новые поля в ~/.config/aura/profile.json.

Наука:
  Single Source of Truth (Fowler 2002) — один канонический источник.
  Aggregator Pattern — сборка разрозненных данных в один интерфейс.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

CONFIG_DIR = Path.home() / ".config/aura"
PROFILE_TXT = CONFIG_DIR / "profile"           # legacy: только имя
PROFILE_JSON = CONFIG_DIR / "profile.json"     # новый: полный профиль
SETTINGS = CONFIG_DIR / "settings.json"
SOS = CONFIG_DIR / "sos.json"
FIN_ELDER = CONFIG_DIR / "fin_elder.json"
SAFETY = CONFIG_DIR / "safety.json"


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


@dataclass
class UserProfile:
    name: str = "captain"
    age: int | None = None
    city: str | None = None
    persona: dict[str, Any] = field(default_factory=dict)
    sos_contact: dict[str, Any] = field(default_factory=dict)
    fin_elder: dict[str, Any] = field(default_factory=dict)
    safety: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    signature: bytes | None = None

    # --- Загрузка ---
    @classmethod
    def load(cls) -> UserProfile:
        """Агрегирует данные из 5 файлов. Приоритет: profile.json > legacy."""
        # Новый профиль (если уже создан)
        if PROFILE_JSON.exists():
            data = _read_json(PROFILE_JSON)
            return cls(
                name=data.get("name", "captain"),
                age=data.get("age"),
                city=data.get("city"),
                persona=data.get("persona", {}),
                sos_contact=data.get("sos_contact", {}),
                fin_elder=data.get("fin_elder", {}),
                safety=data.get("safety", {}),
                created_at=data.get("created_at", datetime.now().isoformat()),
                signature=bytes.fromhex(data["signature"]) if data.get("signature") else None,
            )

        # Legacy: агрегируем из разрозненных файлов
        name = "captain"
        if PROFILE_TXT.exists():
            name = PROFILE_TXT.read_text(encoding="utf-8").strip() or "captain"

        settings = _read_json(SETTINGS)
        sos = _read_json(SOS)
        fin = _read_json(FIN_ELDER)
        safety = _read_json(SAFETY)

        return cls(
            name=name,
            persona=settings.get("persona", {}),
            sos_contact=sos,
            fin_elder=fin,
            safety=safety,
        )

    # --- Сохранение ---
    def save(self) -> None:
        """Пишет полный профиль в profile.json (не трогает legacy-файлы)."""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        data = self.to_dict()
        PROFILE_JSON.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    # --- Сериализация ---
    def _payload(self) -> dict[str, Any]:
        """Данные БЕЗ signature — то, что подписывается."""
        d = asdict(self)
        d.pop("signature", None)
        return d

    def sign(self) -> bytes:
        """Подписать профиль через ledger. Возвращает 64-байтную подпись."""
        from aura.core.ledger import sign as ledger_sign
        self.signature = ledger_sign(self._payload(), agent="profile")
        return self.signature

    def verify(self) -> bool:
        """Проверить подпись профиля. False если signature отсутствует."""
        if not self.signature:
            return False
        from aura.core.ledger import verify as ledger_verify
        return ledger_verify(self._payload(), self.signature)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["signature"] = self.signature.hex() if self.signature else None
        return d

    def __str__(self) -> str:
        return f"UserProfile(name={self.name}, city={self.city}, sos={'✅' if self.sos_contact.get('contact') else '❌'})"


__all__ = ["CONFIG_DIR", "PROFILE_JSON", "UserProfile"]
