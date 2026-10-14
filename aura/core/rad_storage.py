"""Radiation-tolerant storage (P3 #158).

Запись критичных данных с CRC32 + 3 копиями + верификация.
Вдохновлено memory scrubbing на космических аппаратах (RAD750, JWST).

Применение в AURA: stress.db, meds.db, recall.db — защита от bit-flip
на диске, silent corruption, сбоев ФС.

Ключевые понятия:
- Block — фрагмент данных с CRC32.
- Triple copy — 3 независимые копии блока на диске.
- Scrub — периодическая проверка CRC + восстановление из большинства.
"""
from __future__ import annotations

import hashlib
import zlib
from dataclasses import dataclass
from pathlib import Path


class RadStorageError(Exception):
    """Radiation storage: невозможно восстановить блок."""


def crc32(data: bytes) -> int:
    """CRC32 для верификации целостности."""
    return zlib.crc32(data) & 0xFFFFFFFF


@dataclass
class Block:
    """Блок данных с CRC и метаданными."""
    key: str
    data: bytes
    crc: int

    @classmethod
    def create(cls, key: str, data: bytes) -> "Block":
        return cls(key=key, data=data, crc=crc32(data))

    def verify(self) -> bool:
        return crc32(self.data) == self.crc


class RadiationTolerantStore:
    """Хранилище с triple-copy и CRC-верификацией.

    Формат на диске:
        <root>/<key>/copy0.bin, copy1.bin, copy2.bin
        <root>/<key>/copyN.crc     (hex CRC32)

    Пример:
        store = RadiationTolerantStore(Path("/tmp/rad"))
        store.write("meds", b"aspirin 100mg")
        data = store.read("meds")  # переживет 1 bit-flip
    """

    COPIES = 3

    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _dir(self, key: str) -> Path:
        safe = hashlib.sha256(key.encode()).hexdigest()[:16]
        d = self.root / safe
        d.mkdir(parents=True, exist_ok=True)
        return d

    def write(self, key: str, data: bytes) -> None:
        d = self._dir(key)
        block = Block.create(key, data)
        for i in range(self.COPIES):
            (d / f"copy{i}.bin").write_bytes(block.data)
            (d / f"copy{i}.crc").write_text(f"{block.crc:08x}")

    def read(self, key: str) -> bytes:
        d = self._dir(key)
        votes: dict[int, list[bytes]] = {}
        for i in range(self.COPIES):
            bin_p = d / f"copy{i}.bin"
            crc_p = d / f"copy{i}.crc"
            if not bin_p.exists() or not crc_p.exists():
                continue
            data = bin_p.read_bytes()
            expected = int(crc_p.read_text().strip(), 16)
            if crc32(data) == expected:
                votes.setdefault(expected, []).append(data)

        if not votes:
            raise RadStorageError(f"Block '{key}' unrecoverable")

        best_crc, copies = max(votes.items(), key=lambda kv: len(kv[1]))
        if len(copies) * 2 <= self.COPIES:
            raise RadStorageError(
                f"Block '{key}': no majority ({len(copies)}/{self.COPIES})"
            )
        return copies[0]

    def scrub(self, key: str) -> int:
        """Верифицировать все копии, восстановить битые из большинства.
        Возвращает число восстановленных копий.
        """
        d = self._dir(key)
        valid: dict[int, bytes] = {}
        for i in range(self.COPIES):
            bin_p = d / f"copy{i}.bin"
            crc_p = d / f"copy{i}.crc"
            if not bin_p.exists():
                continue
            data = bin_p.read_bytes()
            crc = crc32(data)
            expected_txt = crc_p.read_text().strip() if crc_p.exists() else ""
            expected = int(expected_txt, 16) if expected_txt else -1
            if crc == expected:
                valid[crc] = data

        if not valid:
            raise RadStorageError(f"Scrub '{key}': no valid copies")

        best_crc, best_data = max(valid.items(), key=lambda kv: 0)
        repaired = 0
        for i in range(self.COPIES):
            bin_p = d / f"copy{i}.bin"
            crc_p = d / f"copy{i}.crc"
            data = bin_p.read_bytes() if bin_p.exists() else b""
            if crc32(data) != best_crc:
                bin_p.write_bytes(best_data)
                crc_p.write_text(f"{best_crc:08x}")
                repaired += 1
        return repaired
