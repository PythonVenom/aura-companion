"""Тесты для aura/core/plugin_manifest.py (ADR-090)."""
from __future__ import annotations
import json
from pathlib import Path
import pytest
from aura.core.plugin_manifest import PluginManifest, load_manifest


@pytest.fixture
def manifest_dir(tmp_path):
    d = tmp_path / "deepseek"
    d.mkdir()
    (d / "manifest.json").write_text(json.dumps({
        "id": "deepseek",
        "name": "DeepSeek AI",
        "version": "1.0.0",
        "author": "community",
        "risk_level": "cloud",
        "data_leaves_device": True,
        "endpoint": "https://api.deepseek.com",
        "warns": ["Данные уходят в DeepSeek", "Логи 30 дней"],
        "requires": ["api_key"],
        "user_consent_required": True,
    }), encoding="utf-8")
    return d


def test_load_manifest_basic(manifest_dir):
    m = load_manifest(manifest_dir)
    assert m.id == "deepseek"
    assert m.name == "DeepSeek AI"
    assert m.version == "1.0.0"


def test_manifest_is_cloud(manifest_dir):
    m = load_manifest(manifest_dir)
    assert m.is_cloud is True
    assert m.needs_consent is True


def test_manifest_has_api_key(manifest_dir):
    m = load_manifest(manifest_dir)
    assert m.requires_api_key is True


def test_manifest_warns_count(manifest_dir):
    m = load_manifest(manifest_dir)
    assert len(m.warns) == 2


def test_load_manifest_missing_file(tmp_path):
    d = tmp_path / "empty"
    d.mkdir()
    with pytest.raises(FileNotFoundError):
        load_manifest(d)


def test_load_manifest_invalid_json(tmp_path):
    d = tmp_path / "bad"
    d.mkdir()
    (d / "manifest.json").write_text("not json", encoding="utf-8")
    with pytest.raises(ValueError):
        load_manifest(d)


def test_load_manifest_missing_id(tmp_path):
    d = tmp_path / "noid"
    d.mkdir()
    (d / "manifest.json").write_text(json.dumps({"name": "x"}), encoding="utf-8")
    with pytest.raises(ValueError):
        load_manifest(d)


def test_load_manifest_defaults(tmp_path):
    d = tmp_path / "minimal"
    d.mkdir()
    (d / "manifest.json").write_text(json.dumps({
        "id": "minimal", "name": "Minimal"
    }), encoding="utf-8")
    m = load_manifest(d)
    assert m.risk_level == "local"
    assert m.is_cloud is False
    assert m.needs_consent is False
    assert m.warns == []
    assert m.requires == []
