"""#100 CDP Bridge — Chrome DevTools Protocol.

Наука:
- CDP (Chrome DevTools Protocol) — W3C-совместимый API
- HTTP-endpoints: /json, /json/version, /json/close/<id>
- WebSocket для команд (Page.navigate, Runtime.evaluate)

Зачем:
  Управление Chromium-браузерами БЕЗ расширения и native messaging.
  Работает с Chrome, Chromium, Edge, Brave, Vivaldi, Opera.
  Требует только флаг --remote-debugging-port=9222.

API:
  discover() → str | None         — найти CDP endpoint (ws URL)
  is_available() → bool            — Chrome запущен с --remote-debugging-port?
  list_tabs() → list[dict]         — все открытые вкладки
  new_tab(url) → dict | None       — новая вкладка
  close_tab(id) → bool             — закрыть вкладку
  navigate(url, tab_id=None) → bool — перейти по URL

Fallback:
  Если Chrome не запущен с флагом → все функции graceful.

Запуск Chrome с CDP:
  chromium --remote-debugging-port=9222
  или добавить в ~/.config/chromium-flags.conf
"""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9222
TIMEOUT = 3.0


def _endpoint(path: str, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> str:
    return f"http://{host}:{port}{path}"


def _http_get(url: str, timeout: float = TIMEOUT) -> dict | list | None:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None


def is_available(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> bool:
    """True если Chrome запущен с --remote-debugging-port."""
    data = _http_get(_endpoint("/json/version", host, port))
    return isinstance(data, dict) and "webSocketDebuggerUrl" in data


def discover(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> str | None:
    """Найти browser WebSocket URL."""
    data = _http_get(_endpoint("/json/version", host, port))
    if isinstance(data, dict):
        return data.get("webSocketDebuggerUrl")
    return None


def list_tabs(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> list[dict]:
    """Список открытых вкладок (только type=page)."""
    data = _http_get(_endpoint("/json", host, port))
    if not isinstance(data, list):
        return []
    return [
        {
            "id": t.get("id"),
            "title": t.get("title"),
            "url": t.get("url"),
            "type": t.get("type"),
            "ws_url": t.get("webSocketDebuggerUrl"),
        }
        for t in data
        if t.get("type") == "page"
    ]


def close_tab(tab_id: str, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> bool:
    """Закрыть вкладку по id."""
    if not tab_id:
        return False
    url = _endpoint(f"/json/close/{urllib.parse.quote(tab_id, safe='')}", host, port)
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT) as r:
            return r.status == 200
    except Exception:
        return False


def new_tab(url: str = "about:blank",
            host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> dict | None:
    """Открыть новую вкладку. Возвращает dict или None."""
    if not url:
        url = "about:blank"
    # Chrome ожидает URL в query без http:// префикса для своих схем
    q = urllib.parse.quote(url, safe="")
    ep = _endpoint(f"/json/new?{q}", host, port)
    try:
        req = urllib.request.Request(ep, method="PUT")
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            data = json.loads(r.read().decode("utf-8"))
            return {
                "id": data.get("id"),
                "title": data.get("title"),
                "url": data.get("url"),
                "ws_url": data.get("webSocketDebuggerUrl"),
            }
    except Exception:
        # Fallback: try GET (старые версии)
        try:
            with urllib.request.urlopen(ep, timeout=TIMEOUT) as r:
                data = json.loads(r.read().decode("utf-8"))
                return {
                    "id": data.get("id"),
                    "title": data.get("title"),
                    "url": data.get("url"),
                }
        except Exception:
            return None


def navigate(url: str, tab_id: str | None = None,
             host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> bool:
    """Перейти по URL. Если tab_id=None — использовать первую вкладку.

    Через HTTP: chrome не поддерживает навигацию в существующей вкладке
    через /json endpoint. Поэтому используем WebSocket — но в skeleton
    делаем fallback: открываем новую вкладку с нужным URL.
    """
    if tab_id:
        # Простой путь: закрыть старую + открыть новую
        close_tab(tab_id, host, port)
    tab = new_tab(url, host, port)
    return tab is not None


def get_active_tab(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> dict | None:
    """Первая вкладка (нет прямого API — берём первую в списке)."""
    tabs = list_tabs(host, port)
    return tabs[0] if tabs else None


__all__ = [
    "is_available", "discover", "list_tabs",
    "close_tab", "new_tab", "navigate", "get_active_tab",
    "DEFAULT_HOST", "DEFAULT_PORT",
]
