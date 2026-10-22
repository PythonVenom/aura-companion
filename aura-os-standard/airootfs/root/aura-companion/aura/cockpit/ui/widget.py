"""AURA Widget — минимальный GUI-чат (tkinter).

Наука: Mental-health UI (SAVO). Минимализм, крупный шрифт,
тёмная тема, никаких pop-up.
"""
from __future__ import annotations

import asyncio
import threading
import tkinter as tk
from tkinter import scrolledtext

from aura.cockpit.ui.theme import get_theme


class AuraWidget:
    """Минимальный GUI-чат для AURA."""

    def __init__(self) -> None:
        self.theme = get_theme()
        self.root = tk.Tk()
        self.root.title("AURA — бортовой компьютер")
        self.root.geometry("700x500")
        self.root.configure(bg=self.theme.bg)
        self._build_ui()

    def _build_ui(self) -> None:
        t = self.theme
        # Заголовок
        tk.Label(
            self.root, text="🛸 AURA",
            bg=t.bg, fg=t.accent,
            font=(t.font_family, t.font_size + 4, "bold"),
            pady=t.padding,
        ).pack(anchor="w", padx=t.padding)

        # Чат
        self.chat = scrolledtext.ScrolledText(
            self.root, wrap=tk.WORD,
            bg=t.bg, fg=t.fg,
            insertbackground=t.accent,
            font=(t.font_family, t.font_size),
            relief=tk.FLAT, padx=t.padding, pady=t.padding,
            height=20,
        )
        self.chat.pack(fill=tk.BOTH, expand=True, padx=t.padding, pady=t.padding)
        self.chat.configure(state=tk.DISABLED)

        # Поле ввода
        frame = tk.Frame(self.root, bg=t.bg)
        frame.pack(fill=tk.X, padx=t.padding, pady=(0, t.padding))

        self.entry = tk.Entry(
            frame, bg=t.bg, fg=t.fg,
            insertbackground=t.accent,
            font=(t.font_family, t.font_size),
            relief=tk.FLAT,
        )
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8)
        self.entry.bind("<Return>", self._on_send)

        tk.Button(
            frame, text="→", command=self._on_send,
            bg=t.accent, fg=t.bg,
            font=(t.font_family, t.font_size + 4, "bold"),
            relief=tk.FLAT, padx=t.padding, cursor="hand2",
        ).pack(side=tk.RIGHT, padx=(t.padding // 2, 0))

        self._append("AURA", "Система в норме. Готова к работе.", "accent")

    def _append(self, who: str, text: str, tag: str = "") -> None:
        self.chat.configure(state=tk.NORMAL)
        self.chat.insert(tk.END, f"{who}: ", tag)
        self.chat.insert(tk.END, f"{text}\n\n")
        self.chat.configure(state=tk.DISABLED)
        self.chat.see(tk.END)

    def _on_send(self, event=None) -> None:
        text = self.entry.get().strip()
        if not text:
            return
        self.entry.delete(0, tk.END)
        self._append("Вы", text)
        threading.Thread(target=self._ask, args=(text,), daemon=True).start()

    def _ask(self, text: str) -> None:
        try:
            from aura.bootstrap import build_orchestrator
            orch = build_orchestrator()
            response = asyncio.run(orch.process(text))
        except Exception as e:
            response = f"❌ {e}"
        self.root.after(0, self._append, "AURA", str(response), "accent")

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    AuraWidget().run()


if __name__ == "__main__":
    main()


__all__ = ["AuraWidget", "main"]
