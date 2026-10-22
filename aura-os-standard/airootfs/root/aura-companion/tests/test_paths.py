"""Тесты paths.py."""
from __future__ import annotations
from aura import paths


def test_project_dir_exists():
    assert paths.PROJECT_DIR.exists()


def test_cache_dir_in_home():
    assert str(paths.HOME) in str(paths.CACHE_DIR)


def test_ensure_idempotent():
    paths.ensure()
    paths.ensure()
