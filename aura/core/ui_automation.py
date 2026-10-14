"""#101 UI Automation — универсальный API управления приложениями.

Наука:
- AT-SPI2 (Linux/GNOME/KDE) — accessibility API
- Microsoft UIA (Windows) — UI Automation
- Apple AXAPI (macOS) — Accessibility API
- W3C ARIA (web) — браузерные элементы

Зачем:
  Aura должна управлять ЛЮБЫМ приложением (не только браузером),
  читать кнопки/текст, нажимать, печатать. Это «руки» для elder-care.

Стратегия:
  BaseBackend (Protocol) → LinuxAtspiBackend (готов)
                        → WindowsUiaBackend (stub, NotImplementedError)
                        → MacosAxapiBackend (stub, NotImplementedError)

API (одинаковый для всех платформ):
  get_backend() → BaseBackend | None
  list_windows() → list[str]
  read_window_tree(depth=2) → list[dict]  # {role, name, children}
  click_element(name) → bool
  type_text(text) → bool
  get_active_window() → str

Fallback:
  Если backend недоступен (нет gi/uia/AXAPI) → None,
  функции возвращают пусто, НЕ крашат.
"""
from __future__ import annotations

import platform
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class BaseBackend(Protocol):
    """Контракт UI Automation backend."""

    name: str

    def is_ready(self) -> bool: ...
    def list_windows(self) -> list[str]: ...
    def read_window_tree(self, depth: int = 2) -> list[dict[str, Any]]: ...
    def click_element(self, name: str) -> bool: ...
    def type_text(self, text: str) -> bool: ...
    def get_active_window(self) -> str: ...


class LinuxAtspiBackend:
    """Linux backend через AT-SPI2 (gi.repository.Atspi)."""

    name = "atspi"

    def __init__(self) -> None:
        self._atspi: Any = None
        try:
            import gi
            gi.require_version("Atspi", "2.0")
            from gi.repository import Atspi
            self._atspi = Atspi
        except Exception:
            self._atspi = None

    def is_ready(self) -> bool:
        return self._atspi is not None

    def list_windows(self) -> list[str]:
        if not self.is_ready():
            return []
        try:
            out = []
            desktop = self._atspi.get_desktop(0)
            for i in range(desktop.get_child_count()):
                app = desktop.get_child_at_index(i)
                if app is None:
                    continue
                for j in range(app.get_child_count()):
                    win = app.get_child_at_index(j)
                    if win and win.get_name():
                        out.append(win.get_name())
            return out
        except Exception:
            return []

    def read_window_tree(self, depth: int = 2) -> list[dict[str, Any]]:
        if not self.is_ready():
            return []
        try:
            tree = []
            desktop = self._atspi.get_desktop(0)
            for i in range(desktop.get_child_count()):
                app = desktop.get_child_at_index(i)
                if app is None:
                    continue
                for j in range(app.get_child_count()):
                    win = app.get_child_at_index(j)
                    if win is None:
                        continue
                    tree.append(self._walk(win, depth))
            return tree
        except Exception:
            return []

    def _walk(self, node: Any, depth: int) -> dict[str, Any]:
        info = {
            "role": (node.get_role_name() or "").lower(),
            "name": node.get_name() or "",
            "children": [],
        }
        if depth > 0:
            try:
                for k in range(min(node.get_child_count(), 30)):
                    ch = node.get_child_at_index(k)
                    if ch is not None:
                        info["children"].append(self._walk(ch, depth - 1))  # type: ignore[union-attr]
            except Exception:
                pass
        return info

    def click_element(self, name: str) -> bool:
        if not self.is_ready() or not name:
            return False
        try:
            target = self._find_by_name(self._atspi.get_desktop(0), name, depth=5)
            if target is None:
                return False
            action = target.get_action_iface()
            if action is None:
                return False
            action.do_action(0)  # первое действие = обычно "click"
            return True
        except Exception:
            return False

    def _find_by_name(self, node: Any, name: str, depth: int) -> Any:
        if depth <= 0 or node is None:
            return None
        try:
            if (node.get_name() or "").lower() == name.lower():
                return node
            for i in range(node.get_child_count()):
                found = self._find_by_name(
                    node.get_child_at_index(i), name, depth - 1
                )
                if found is not None:
                    return found
        except Exception:
            pass
        return None

    def type_text(self, text: str) -> bool:
        # AT-SPI генерация клавиш сложна (нужен xdotool/ydotool)
        return False

    def get_active_window(self) -> str:
        wins = self.list_windows()
        return wins[0] if wins else ""


class WindowsUiaBackend:
    """Windows backend через pywinauto/UIA (stub)."""

    name = "uia"

    def is_ready(self) -> bool:
        return False

    def list_windows(self) -> list[str]:
        return []

    def read_window_tree(self, depth: int = 2) -> list[dict[str, Any]]:
        return []

    def click_element(self, name: str) -> bool:
        return False

    def type_text(self, text: str) -> bool:
        return False

    def get_active_window(self) -> str:
        return ""


class MacosAxapiBackend:
    """macOS backend через PyObjC/AXAPI (stub)."""

    name = "axapi"

    def is_ready(self) -> bool:
        return False

    def list_windows(self) -> list[str]:
        return []

    def read_window_tree(self, depth: int = 2) -> list[dict[str, Any]]:
        return []

    def click_element(self, name: str) -> bool:
        return False

    def type_text(self, text: str) -> bool:
        return False

    def get_active_window(self) -> str:
        return ""


# === Auto-detect backend ===

_BACKEND: BaseBackend | None = None
_BACKEND_CHECKED = False


def _detect_backend() -> BaseBackend | None:
    system = platform.system()
    if system == "Linux":
        return LinuxAtspiBackend()
    if system == "Windows":
        return WindowsUiaBackend()
    if system == "Darwin":
        return MacosAxapiBackend()
    return None


def get_backend() -> BaseBackend | None:
    """Получить backend (lazy, кэшируется)."""
    global _BACKEND, _BACKEND_CHECKED
    if not _BACKEND_CHECKED:
        _BACKEND = _detect_backend()
        _BACKEND_CHECKED = True
    return _BACKEND


def reset_backend() -> None:
    """Сбросить кэш backend (для тестов)."""
    global _BACKEND, _BACKEND_CHECKED
    _BACKEND = None
    _BACKEND_CHECKED = False


# === Публичный API ===

def list_windows() -> list[str]:
    b = get_backend()
    return b.list_windows() if b else []


def read_window_tree(depth: int = 2) -> list[dict[str, Any]]:
    b = get_backend()
    return b.read_window_tree(depth) if b else []


def click_element(name: str) -> bool:
    b = get_backend()
    return b.click_element(name) if b else False


def type_text(text: str) -> bool:
    b = get_backend()
    return b.type_text(text) if b else False


def get_active_window() -> str:
    b = get_backend()
    return b.get_active_window() if b else ""


def backend_name() -> str:
    b = get_backend()
    return b.name if b else "none"


def is_ready() -> bool:
    b = get_backend()
    return b.is_ready() if b else False


__all__ = [
    "BaseBackend",
    "LinuxAtspiBackend",
    "MacosAxapiBackend",
    "WindowsUiaBackend",
    "backend_name",
    "click_element",
    "get_active_window",
    "get_backend",
    "is_ready",
    "list_windows",
    "read_window_tree",
    "reset_backend",
    "type_text",
]
