"""T-sec-4 — тесты consent flow."""
from pathlib import Path

import pytest

from aura.core import consent


@pytest.fixture(autouse=True)
def isolate_db(tmp_path, monkeypatch):
    """Изолировать consent.db в tmp."""
    monkeypatch.setattr(consent, "CONSENT_DB", tmp_path / "consent.db")


def test_scopes_defined():
    assert "microphone" in consent.SCOPES
    assert "telemetry" in consent.SCOPES
    assert consent.SCOPES["telemetry"].get("always_off") is True


def test_grant_and_check():
    assert consent.check("emotion_voice") is False
    assert consent.grant("emotion_voice") is True
    assert consent.check("emotion_voice") is True


def test_grant_unknown_scope():
    assert consent.grant("unknown") is False


def test_grant_always_off():
    # telemetry никогда не включается
    assert consent.grant("telemetry") is False
    assert consent.check("telemetry") is False


def test_revoke():
    consent.grant("reminiscence")
    assert consent.check("reminiscence") is True
    assert consent.revoke("reminiscence") is True
    assert consent.check("reminiscence") is False


def test_revoke_required_fails():
    # microphone — required, нельзя отозвать
    assert consent.revoke("microphone") is False


def test_all_status():
    consent.grant("emotion_voice")
    consent.grant("health_twin")
    s = consent.all_status()
    assert s["emotion_voice"]["granted"] is True
    assert s["health_twin"]["granted"] is True
    assert s["reminiscence"]["granted"] is False
    assert s["telemetry"]["granted"] is False  # always off


def test_audit_log():
    consent.grant("emotion_voice")
    consent.revoke("emotion_voice")
    log = consent.audit_log()
    assert len(log) >= 2
    actions = [e["action"] for e in log]
    assert "grant" in actions
    assert "revoke" in actions


def test_require_raises():
    with pytest.raises(PermissionError, match="emotion_voice"):
        consent.require("emotion_voice")


def test_require_passes():
    consent.grant("health_twin")
    consent.require("health_twin")  # не должно raise


def test_erase_all():
    consent.grant("emotion_voice")
    consent.grant("reminiscence")
    result = consent.erase_all("test")
    assert result["erased_consents"] == 2
    assert consent.check("emotion_voice") is False


def test_status_summary():
    consent.grant("emotion_voice")
    s = consent.status()
    assert s["scopes_total"] == len(consent.SCOPES)
    assert s["granted"] == 1
    assert "microphone" in s["required"]
    assert "telemetry" in s["always_off"]
