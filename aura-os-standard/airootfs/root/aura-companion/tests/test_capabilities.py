"""Тесты для aura/core/capabilities.py — Borderlands-style система.

Наука (Д4): Saltzer & Schroeder 1975, Ferraiolo & Kuhn 1992,
Sandhu et al. 1996, NIST SP 800-162 (2014), Gamma 1994.

Проверяем:
- Composite: class + trees → capabilities
- Decorator: class_mod добавляет/убирает права
- Wildcard: admin = '*'
- Fail-closed: нет профиля → deny
- Комбинации: elder + medical, elder + caregiver, elder + medical + caregiver
- Изоляция: elder НЕ имеет shell, dev НЕ имеет sos
"""
from __future__ import annotations

import pytest

from aura.core.capabilities import (
    CLASSES, TREES, CLASS_MODS,
    Profile,
    set_current, current, require,
)


# ═══════════════════════════════════════════════════════════════
# CLASSES
# ═══════════════════════════════════════════════════════════════

def test_classes_all_present():
    """6 базовых классов должны существовать."""
    expected = {"elder", "kid", "blind", "dev", "admin", "guest"}
    assert expected <= set(CLASSES.keys())


def test_elder_has_sos():
    p = Profile(name="elder", base_class="elder")
    assert p.has("sos")
    assert p.has("meds")
    assert p.has("fall")


def test_elder_no_shell():
    """Least privilege: elder НЕ имеет shell."""
    p = Profile(name="elder", base_class="elder")
    assert not p.has("shell")
    assert not p.has("shell:safe")
    assert not p.has("git:read")


def test_dev_has_shell_safe_no_sos():
    p = Profile(name="dev", base_class="dev")
    assert p.has("shell:safe")
    assert p.has("git:read")
    assert not p.has("sos")  # dev не elder-care


def test_admin_wildcard():
    p = Profile(name="admin", base_class="admin")
    assert p.has("anything")
    assert p.has("shell:unsafe")
    assert p.has("*")


def test_guest_minimal():
    p = Profile(name="guest", base_class="guest")
    assert p.has("voice")
    assert p.has("time")
    assert not p.has("sos")
    assert not p.has("shell")


def test_unknown_class_empty():
    """Неизвестный класс → пустой набор прав (не падает)."""
    p = Profile(name="unknown", base_class="nonexistent")
    caps = p.capabilities()
    assert caps == frozenset()


# ═══════════════════════════════════════════════════════════════
# TREES (modifiers)
# ═══════════════════════════════════════════════════════════════

def test_elder_medical_adds_rights():
    p = Profile(name="elder-medical", base_class="elder", trees=("medical",))
    assert p.has("medical:read")
    assert p.has("bpm:read")
    assert p.has("sos:priority")
    assert p.has("sos")  # базовое не потерялось


def test_elder_caregiver():
    p = Profile(name="elder-caregiver", base_class="elder", trees=("caregiver",))
    assert p.has("family:call")
    assert p.has("reports:read")
    assert p.has("meds:manage")


def test_elder_medical_caregiver_combined():
    """Комбинация двух деревьев — Borderlands-style."""
    p = Profile(
        name="elder-full",
        base_class="elder",
        trees=("medical", "caregiver"),
    )
    assert p.has("medical:read")
    assert p.has("bpm:read")
    assert p.has("family:call")
    assert p.has("reports:read")
    assert p.has("sos")


def test_unknown_tree_ignored():
    """Неизвестное дерево → пустое расширение."""
    p = Profile(name="test", base_class="elder", trees=("nonexistent",))
    assert p.has("sos")  # базовое не потерялось
    assert not p.has("nonexistent")


# ═══════════════════════════════════════════════════════════════
# CLASS MODS (decorator)
# ═══════════════════════════════════════════════════════════════

def test_elder_night_adds_and_disables():
    p = Profile(name="elder-night", base_class="elder", class_mod="elder-night")
    assert p.has("night_mode")
    assert p.has("only_critical")
    assert not p.has("music_ducker")
    assert not p.has("handsfree")
    # Базовое elder осталось
    assert p.has("sos")


def test_dev_sandbox_disables_write():
    p = Profile(name="dev-sandbox", base_class="dev", class_mod="dev-sandbox")
    assert p.has("shell:dry_run")
    assert not p.has("git:write")
    assert not p.has("fs:write")
    assert p.has("git:read")  # базовое осталось


def test_unknown_class_mod_ignored():
    p = Profile(name="test", base_class="elder", class_mod="nonexistent")
    assert p.has("sos")  # базовое не потерялось


# ═══════════════════════════════════════════════════════════════
# RUNTIME STATE (fail-closed)
# ═══════════════════════════════════════════════════════════════

def test_fail_closed_no_profile():
    """Saltzer & Schroeder 1975: default-deny."""
    set_current(None)
    assert require("sos") is False
    assert require("anything") is False


def test_set_current_admin():
    set_current(Profile(name="admin", base_class="admin"))
    assert require("sos") is True
    assert require("anything") is True


def test_set_current_elder():
    set_current(Profile(name="elder", base_class="elder"))
    assert require("sos") is True
    assert require("shell") is False


def test_current_returns_profile():
    p = Profile(name="test", base_class="elder")
    set_current(p)
    assert current() is p
    set_current(None)
    assert current() is None


# ═══════════════════════════════════════════════════════════════
# FROZEN DATACLASS
# ═══════════════════════════════════════════════════════════════

def test_profile_immutable():
    """Profile frozen — нельзя мутировать."""
    p = Profile(name="test", base_class="elder")
    with pytest.raises(Exception):  # FrozenInstanceError
        p.name = "changed"


def test_capabilities_is_frozenset():
    """Возвращаемый набор — frozenset (иммутабельный)."""
    p = Profile(name="test", base_class="elder")
    caps = p.capabilities()
    assert isinstance(caps, frozenset)
    with pytest.raises(AttributeError):
        caps.add("new")
