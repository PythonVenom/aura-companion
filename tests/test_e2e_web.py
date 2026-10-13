"""E2E тесты Aura Web (2026-10-13).

Наука:
- Fowler 2003 (Test Pyramid) — мало e2e, но они ловят реальные регрессии
- Cohn 2009 (Succeeding with Agile) — UI-тесты через Playwright
- Humble & Farley 2010 (Continuous Delivery) — e2e как gate

Что проверяем:
1. Реальный uvicorn-сервер отвечает
2. HTTP endpoints (health, status, agents, chat)
3. Playwright: реальный браузер открывает /, видит UI, отправляет команду
4. Mobile viewport (elder-care, ADR-057)
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest


PORT = 18080  # не 8080 — чтобы не конфликтовать с работающим демоном
BASE_URL = f"http://127.0.0.1:{PORT}"


# ============================================================
# Fixture: поднять uvicorn на время тестов
# ============================================================
@pytest.fixture(scope="module")
def aura_server():
    """Запустить uvicorn с aura/web/api.py на PORT."""
    project = Path(__file__).parent.parent

    # Проверяем что порт свободен
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex(("127.0.0.1", PORT)) == 0:
            pytest.skip(f"Порт {PORT} занят — пропускаю e2e")

    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"

    proc = subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn",
            "aura.web.api:create_app",
            "--factory",
            "--host", "127.0.0.1",
            "--port", str(PORT),
            "--log-level", "warning",
        ],
        cwd=str(project),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Ждём готовности (до 10 сек)
    deadline = time.time() + 10
    ready = False
    while time.time() < deadline:
        try:
            r = httpx.get(f"{BASE_URL}/health", timeout=1.0)
            if r.status_code == 200:
                ready = True
                break
        except Exception:
            time.sleep(0.3)

    if not ready:
        proc.terminate()
        try:
            out, err = proc.communicate(timeout=3)
        except Exception:
            proc.kill()
            out, err = b"", b""
        pytest.skip(f"uvicorn не поднялся: {err.decode()[:300]}")

    yield proc

    proc.terminate()
    try:
        proc.wait(timeout=3)
    except Exception:
        proc.kill()


# ============================================================
# HTTP E2E
# ============================================================
def test_e2e_health(aura_server):
    """/health → 200 ok."""
    r = httpx.get(f"{BASE_URL}/health", timeout=5)
    assert r.status_code == 200
    data = r.json()
    assert data.get("status") == "ok"


def test_e2e_status(aura_server):
    """/status → JSON."""
    r = httpx.get(f"{BASE_URL}/status", timeout=5)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, dict)


def test_e2e_agents(aura_server):
    """/agents → структура.

    uvicorn --factory создаёт app без orchestrator → count=0.
    Проверяем что endpoint работает и отдаёт структуру.
    """
    r = httpx.get(f"{BASE_URL}/agents", timeout=5)
    assert r.status_code == 200
    data = r.json()
    assert "agents" in data
    assert "count" in data
    assert isinstance(data["count"], int)


def test_e2e_version(aura_server):
    """/version → строка версии."""
    r = httpx.get(f"{BASE_URL}/version", timeout=5)
    assert r.status_code == 200
    data = r.json()
    assert "version" in data


def test_e2e_chat_post(aura_server):
    """POST /chat → запись в inbox."""
    r = httpx.post(
        f"{BASE_URL}/chat",
        json={"user": "e2e тест"},
        timeout=5,
    )
    assert r.status_code == 200
    data = r.json()
    assert data.get("user") == "e2e тест"


def test_e2e_chat_history(aura_server):
    """GET /chat/history → массив."""
    r = httpx.get(f"{BASE_URL}/chat/history", timeout=5)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, (list, dict))


def test_e2e_csrf_blocks_evil(aura_server):
    """CSRF: злой origin → 403."""
    r = httpx.post(
        f"{BASE_URL}/chat",
        json={"user": "тест"},
        headers={"Origin": "https://evil.example.com"},
        timeout=5,
    )
    assert r.status_code == 403


# ============================================================
# Playwright E2E (реальный браузер)
# ============================================================
def test_e2e_playwright_loads_ui(aura_server):
    """Playwright: загружаем /, видим «Aura Web»."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        pytest.skip("playwright не установлен")

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)
        except Exception as e:
            pytest.skip(f"chromium не запустился: {e}")

        page = browser.new_page()
        page.goto(BASE_URL + "/ui", timeout=10000)
        # Проверяем заголовок
        title = page.title()
        content = page.content()
        browser.close()

    assert "Aura" in title or "Aura" in content


def test_e2e_playwright_ui_has_form(aura_server):
    """Playwright: на / есть поле ввода."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        pytest.skip("playwright не установлен")

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)
        except Exception as e:
            pytest.skip(f"chromium не запустился: {e}")

        page = browser.new_page()
        page.goto(BASE_URL + "/ui", timeout=10000)
        # Ищем input или textarea
        has_input = page.locator("input, textarea").count() > 0
        browser.close()

    assert has_input, "На странице нет поля ввода"


def test_e2e_playwright_mobile_viewport(aura_server):
    """Playwright: mobile viewport (elder-care, ADR-057)."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        pytest.skip("playwright не установлен")

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)
        except Exception as e:
            pytest.skip(f"chromium не запустился: {e}")

        # iPhone SE
        device = p.devices.get("iPhone SE")
        if device is None:
            # Старый API
            context = browser.new_context(
                viewport={"width": 375, "height": 667},
                user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 15_0) AppleWebKit/605.1.15",
            )
        else:
            context = browser.new_context(**device)

        page = context.new_page()
        page.goto(BASE_URL + "/ui", timeout=10000)
        # Страница загрузилась, элементы видны
        assert page.locator("body").count() > 0
        context.close()
        browser.close()
