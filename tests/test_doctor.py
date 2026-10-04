"""aura doctor — smoke."""
from unittest.mock import patch, MagicMock
from aura import doctor


def test_check_all_returns_tuple():
    lines, ok, total = doctor.check_all()
    assert isinstance(lines, list)
    assert total == 8
    assert len(lines) == 8


def test_check_all_service_down():
    with patch("subprocess.run") as mock:
        mock.return_value = MagicMock(stdout="inactive", returncode=1)
        lines, ok, total = doctor.check_all()
        assert any("aura.service" in l for l in lines)


def test_main_returns_int():
    with patch.object(doctor, "check_all", return_value=(["  ✅ test"], 1, 1)):
        rc = doctor.main()
        assert rc == 0


def test_main_returns_1_on_failure():
    with patch.object(doctor, "check_all", return_value=(["  ❌ test"], 0, 1)):
        rc = doctor.main()
        assert rc == 1
