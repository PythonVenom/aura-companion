"""Mentor Main UI — голосовой + text интерфейс."""
from aura.kernel.agents.mentor.path import PathTracker
from aura.kernel.agents.mentor.ui import render_menu


def main(user: str = "batya") -> str:
    t = PathTracker(user)
    return render_menu(t)
