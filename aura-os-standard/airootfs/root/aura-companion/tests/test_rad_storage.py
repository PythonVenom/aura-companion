"""Tests for radiation-tolerant storage (P3 #158)."""
from pathlib import Path

import pytest

from aura.core.rad_storage import (
    RadiationTolerantStore,
    RadStorageError,
    crc32,
)


@pytest.fixture
def store(tmp_path: Path) -> RadiationTolerantStore:
    return RadiationTolerantStore(tmp_path / "rad")


def test_crc32_stable():
    assert crc32(b"hello") == crc32(b"hello")
    assert crc32(b"hello") != crc32(b"world")


def test_write_read_roundtrip(store):
    store.write("meds", b"aspirin 100mg")
    assert store.read("meds") == b"aspirin 100mg"


def test_three_copies_written(store):
    store.write("k", b"data")
    d = store._dir("k")
    for i in range(3):
        assert (d / f"copy{i}.bin").exists()
        assert (d / f"copy{i}.crc").exists()


def test_survives_one_bitflip(store):
    store.write("meds", b"aspirin")
    d = store._dir("meds")
    (d / "copy0.bin").write_bytes(b"aspirin_flip")
    # 2 из 3 валидны — большинство
    assert store.read("meds") == b"aspirin"


def test_unrecoverable_when_majority_broken(store):
    store.write("meds", b"aspirin")
    d = store._dir("meds")
    (d / "copy0.bin").write_bytes(b"broken0")
    (d / "copy1.bin").write_bytes(b"broken1")
    with pytest.raises(RadStorageError):
        store.read("meds")


def test_missing_block_raises(store):
    with pytest.raises(RadStorageError):
        store.read("nonexistent")


def test_scrub_repairs_broken_copy(store):
    store.write("k", b"payload")
    d = store._dir("k")
    (d / "copy1.bin").write_bytes(b"garbage")
    repaired = store.scrub("k")
    assert repaired >= 1
    assert store.read("k") == b"payload"


def test_scrub_no_repair_when_clean(store):
    store.write("k", b"payload")
    assert store.scrub("k") == 0


def test_unhashable_key_ok(store):
    store.write("ключ с пробелами", b"data")
    assert store.read("ключ с пробелами") == b"data"


def test_binary_data_roundtrip(store):
    payload = bytes(range(256))
    store.write("bin", payload)
    assert store.read("bin") == payload
