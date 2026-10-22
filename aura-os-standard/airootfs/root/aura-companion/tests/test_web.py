"""Web UI skeleton (ADR-042)."""
import pytest
from aura.web.app import create_app, HTML_HOME


def test_home_html_has_form():
    assert "<form" in HTML_HOME
    assert "htmx" in HTML_HOME


def test_create_app_or_skip():
    app = create_app()
    if app is None:
        pytest.skip("fastapi не установлен")


def test_status_endpoint_or_skip():
    app = create_app()
    if app is None:
        pytest.skip("fastapi не установлен")
    from fastapi.testclient import TestClient
    c = TestClient(app)
    r = c.get("/status")
    assert r.status_code == 200
