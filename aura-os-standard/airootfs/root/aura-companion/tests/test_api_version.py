"""#156 API Versioning — тесты."""
from __future__ import annotations

import pytest

from aura.core.api_version import (
    APIVersion, CURRENT_API, api, check_all, is_compatible, registered,
)


def test_parse_simple():
    v = APIVersion.parse("1.2.3")
    assert v.major == 1 and v.minor == 2 and v.patch == 3


def test_parse_prerelease():
    v = APIVersion.parse("2.0.0-rc1")
    assert v.prerelease == "rc1"


def test_parse_invalid():
    with pytest.raises(ValueError):
        APIVersion.parse("not-a-version")


def test_str():
    assert str(APIVersion.parse("1.2.3")) == "1.2.3"
    assert str(APIVersion.parse("2.0.0-rc1")) == "2.0.0-rc1"


def test_compatible_same_major():
    v1 = APIVersion.parse("1.2.3")
    v2 = APIVersion.parse("1.5.0")
    assert v1.is_compatible(v2) is True


def test_incompatible_different_major():
    v1 = APIVersion.parse("1.0.0")
    v2 = APIVersion.parse("2.0.0")
    assert v1.is_compatible(v2) is False


def test_current_api_is_v1():
    assert CURRENT_API.major == 1


def test_api_decorator():
    @api("1.5.0")
    def my_func():
        pass
    assert my_func.__api_version__ == APIVersion.parse("1.5.0")


def test_is_compatible_helper():
    assert is_compatible("1.9.9") is True
    assert is_compatible("2.0.0") is False
    assert is_compatible("invalid") is False


def test_check_all_returns_incompatible():
    @api("2.0.0")
    def bad_func():
        pass
    bad = check_all()
    assert any("bad_func" in b for b in bad)
