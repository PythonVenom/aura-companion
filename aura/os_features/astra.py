"""Astra Linux — OS feature adapters (T-os-1).

Наука:
- Bell & LaPadula 1973 — Mandatory Access Control (MAC)
- Приказ ФСТЭК №17 (2009) — требования к защите
- Parsec (Astra Linux) — реализация MAC
- pdpl-file (Astra) — утилита метки доступа
- ГОСТ Р 51141 — классификация документов

Идея: медицинские данные бати получают MAC-метку (уровень 2-4).
Aura может повышать/понижать уровень через pdpl-file.
Если Astra нет → graceful degradation (None).
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

# Уровни MAC Parsec (Astra docs)
# 0 = несекретно, 1 = ДСП, 2 = секретно, 3 = сов. секретно, 4 = особой важности
MAC_LEVELS = {
    0: "0",  # Несекретно
    1: "1",  # ДСП (для служебного пользования)
    2: "2",  # Секретно
    3: "3",  # Совершенно секретно
    4: "4",  # Особой важности
}


def _is_astra() -> bool:
    """Определить, работаем ли на Astra Linux."""
    try:
        release = Path("/etc/os-release").read_text(encoding="utf-8")
        return "astra" in release.lower()
    except Exception:
        return False


def _has_parsec() -> bool:
    """Проверить наличие Parsec (pdpl-file, pdp-id)."""
    return shutil.which("pdpl-file") is not None or \
           shutil.which("pdp-id") is not None


class ParsecAdapter:
    """MAC Parsec adapter. Управление метками доступа.

    Использование:
        a = ParsecAdapter()
        if a.available():
            a.set_label(Path("~/meds.db"), level=2)  # секретно
            level = a.get_label(Path("~/meds.db"))
    """

    name = "parsec"
    mac_levels = MAC_LEVELS

    def available(self) -> bool:
        """Доступен ли Parsec на этой системе."""
        return _is_astra() and _has_parsec()

    def set_label(self, path: Path | str, level: int,
                  categories: list[int] | None = None) -> bool:
        """Установить MAC-метку на файл.

        level: 0-4 (см. MAC_LEVELS)
        categories: опционально — категории (0-63 в Parsec)

        Использует `pdpl-file -l <level>` (Astra docs).
        """
        if not self.available():
            return False
        if level not in MAC_LEVELS:
            return False
        path = Path(path).expanduser()
        if not path.exists():
            return False
        try:
            # pdpl-file <level> <path>
            cmd = ["pdpl-file", "-l", MAC_LEVELS[level], str(path)]
            r = subprocess.run(cmd, timeout=5, check=False,
                               capture_output=True, text=True)
            return r.returncode == 0
        except Exception:
            return False

    def get_label(self, path: Path | str) -> dict | None:
        """Прочитать MAC-метку файла.

        Возвращает {"level": int, "raw": str} или None.
        """
        if not self.available():
            return None
        path = Path(path).expanduser()
        if not path.exists():
            return None
        try:
            # pdpl-file -i <path>
            r = subprocess.run(
                ["pdpl-file", "-i", str(path)],
                timeout=5, check=False, capture_output=True, text=True,
            )
            if r.returncode != 0:
                return None
            raw = r.stdout.strip()
            # Парсим "level: N" или просто "N"
            level = None
            for line in raw.splitlines():
                if "level" in line.lower():
                    try:
                        level = int(line.split(":")[-1].strip())
                    except ValueError:
                        pass
            return {"level": level, "raw": raw}
        except Exception:
            return None

    def elevate_for(self, path: Path | str, level: int = 2) -> bool:
        """Повысить уровень файла (например, для медкарты).

        Используется, когда Aura сохраняет медицинские данные:
        они сразу получают уровень "секретно".
        """
        return self.set_label(path, level)

    def declassify(self, path: Path | str) -> bool:
        """Понизить уровень до 0 (несекретно) — для экспорта/удаления."""
        return self.set_label(path, level=0)

    def status(self) -> dict:
        """Публичный API: статус Parsec."""
        return {
            "is_astra": _is_astra(),
            "has_parsec": _has_parsec(),
            "available": self.available(),
            "levels": MAC_LEVELS,
        }


class GOSTAdapter:
    """ГОСТ Р 34.10-2012 — электронная подпись (T-os-2).

    Placeholder. Реализация — отдельная задача.
    """

    def available(self) -> bool:
        return _is_astra() and shutil.which("cryptcp") is not None

    def sign(self, path: Path | str) -> Path | None:
        """Подписать файл (ГОСТ). Placeholder."""
        return None

    def verify(self, path: Path | str, sig: Path | str) -> bool:
        """Проверить подпись (ГОСТ). Placeholder."""
        return False


__all__ = ["MAC_LEVELS", "GOSTAdapter", "ParsecAdapter"]
