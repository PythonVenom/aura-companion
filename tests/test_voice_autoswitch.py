"""Voice autoswitch (ADR-044)."""
from datetime import datetime
from aura import voice_autoswitch as va


def test_schedule_morning():
    assert va.get_current_profile(datetime(2026, 9, 28, 7, 0)) == "sport"


def test_schedule_workday():
    assert va.get_current_profile(datetime(2026, 9, 28, 12, 0)) == "massage"


def test_schedule_evening():
    assert va.get_current_profile(datetime(2026, 9, 28, 19, 0)) == "construction"


def test_schedule_night():
    assert va.get_current_profile(datetime(2026, 9, 28, 23, 30)) == "default"
    assert va.get_current_profile(datetime(2026, 9, 28, 3, 0)) == "default"


def test_should_switch_same():
    # Если текущий совпадает с расписанием — не переключать
    now = datetime(2026, 9, 28, 12, 0)
    assert va.should_switch("massage", now) is None


def test_should_switch_diff():
    now = datetime(2026, 9, 28, 12, 0)
    assert va.should_switch("default", now) == "massage"


def test_schedule_covers_24h():
    """Каждый час должен попасть в какой-то профиль."""
    for h in range(24):
        p = va.get_current_profile(datetime(2026, 9, 28, h, 0))
        assert p, f"час {h} без профиля"
