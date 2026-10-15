"""Theme — минималистичная тёмная тема AURA.

Наука: Mental-health UI (SAVO, Lifted). Clean layout, pastel gradients,
warm oranges + deep indigos, no pop-ups.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

THEME_FILE = Path.home() / ".cache" / "aura" / "theme.json"


@dataclass
class Theme:
    """Тема UI."""
    mode: str = "dark"           # dark | light
    font_size: int = 16          # базовый размер
    font_family: str = "JetBrains Mono"
    bg: str = "#0e1116"          # глубокий индиго
    fg: str = "#e6e1d5"          # тёплый беж
    accent: str = "#ff8c42"      # тёплый оранжевый
    muted: str = "#7a8290"
    error: str = "#e5484d"
    success: str = "#46a758"
    line_height: float = 1.6
    padding: int = 12
    rounded: int = 8
    show_emoji: bool = True
    show_timestamps: bool = False
    silent_animations: bool = True  # без мигания

    def to_css(self) -> str:
        """CSS-стили (для будущего TUI/HTML)."""
        return f"""
        :root {{
            --bg: {self.bg};
            --fg: {self.fg};
            --accent: {self.accent};
            --muted: {self.muted};
            --error: {self.error};
            --success: {self.success};
            --font: {self.font_family};
            --size: {self.font_size}px;
            --line: {self.line_height};
            --pad: {self.padding}px;
            --rounded: {self.rounded}px;
        }}
        body {{
            background: var(--bg);
            color: var(--fg);
            font-family: var(--font);
            font-size: var(--size);
            line-height: var(--line);
            padding: var(--pad);
        }}
        .accent {{ color: var(--accent); }}
        .muted  {{ color: var(--muted); }}
        .error  {{ color: var(--error); }}
        .success {{ color: var(--success); }}
        """


_THEME: Theme | None = None


def _load() -> Theme:
    if THEME_FILE.exists():
        try:
            data = json.loads(THEME_FILE.read_text(encoding="utf-8"))
            return Theme(**{k: v for k, v in data.items() if k in Theme.__dataclass_fields__})
        except Exception:
            pass
    return Theme()


def _save(theme: Theme) -> bool:
    try:
        THEME_FILE.parent.mkdir(parents=True, exist_ok=True)
        THEME_FILE.write_text(json.dumps(asdict(theme), ensure_ascii=False, indent=2))
        return True
    except Exception:
        return False


def get_theme() -> Theme:
    global _THEME
    if _THEME is None:
        _THEME = _load()
    return _THEME


def set_theme(theme: Theme) -> bool:
    global _THEME
    _THEME = theme
    return _save(theme)


__all__ = ["Theme", "get_theme", "set_theme"]
