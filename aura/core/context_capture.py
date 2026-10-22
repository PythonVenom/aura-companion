"""Context Capture — захват активного окна для контекста Aura.

Использует xdotool / xprop (X11).
"""
from __future__ import annotations
import subprocess
import logging

log = logging.getLogger("aura.context_capture")

def get_active_window_info() -> dict:
    """Возвращает информацию об активном окне (title, class)."""
    info = {"title": "", "class": "", "app": ""}
    try:
        # Получаем ID активного окна
        win_id_res = subprocess.run(
            ["xdotool", "getactivewindow"], 
            capture_output=True, text=True, check=True
        )
        win_id = win_id_res.stdout.strip()
        
        # Получаем заголовок
        title_res = subprocess.run(
            ["xdotool", "getwindowname", win_id], 
            capture_output=True, text=True, check=True
        )
        info["title"] = title_res.stdout.strip()
        
        # Получаем класс приложения (WM_CLASS)
        xprop_res = subprocess.run(
            ["xprop", "-id", win_id, "WM_CLASS"], 
            capture_output=True, text=True, check=True
        )
        # Вывод: WM_CLASS(STRING) = "code", "Code"
        if "=" in xprop_res.stdout:
            classes = xprop_res.stdout.split("=")[1].strip().split(", ")
            if classes:
                info["class"] = classes[-1].strip('"')
                info["app"] = info["class"].lower()
                
    except subprocess.CalledProcessError:
        pass # Нет активного окна или X11 не отвечает
    except Exception as e:
        log.error(f"Context capture error: {e}")
        
    return info

def format_context_for_prompt() -> str:
    """Форматирует контекст для передачи в LLM (в системный промпт)."""
    ctx = get_active_window_info()
    if not ctx["title"]:
        return ""
    return f"[КОНТЕКСТ ЭКРАНА] Сейчас пользователь смотрит на окно: {ctx['app']} | Заголовок: {ctx['title']}"

__all__ = ["get_active_window_info", "format_context_for_prompt"]
