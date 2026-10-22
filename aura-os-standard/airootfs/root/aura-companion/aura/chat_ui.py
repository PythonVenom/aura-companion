"""aura chat-ui — чат с Аурой + HUD + меню с цифрами.

F-102b: возвращаем меню с нажимаемыми вариантами из утренней сессии.
Слева — состояние систем. Сверху — категории. Внутри — действия.
Свободный текст тоже работает.
"""
from __future__ import annotations

import asyncio
import contextlib
import shutil
import subprocess
import sys
from pathlib import Path

# ANSI
R = "\033[0m"
B = "\033[1m"
D = "\033[2m"
G = "\033[32m"
Y = "\033[33m"
C = "\033[36m"
M = "\033[35m"
RED = "\033[31m"
W = 62


def clear() -> None:
    print("\033[2J\033[H", end="")


def row(text: str, width: int = W) -> str:
    try:
        from wcwidth import wcswidth
        v = wcswidth(text)
    except ImportError:
        v = len(text)
    return f"║ {text}{' ' * max(0, width - v - 2)} ║"


def hr(char: str = "─", width: int = W) -> str:
    return "╠" + char * width + "╣"


TOP = "╔" + "═" * W + "╗"
MID = "╠" + "═" * W + "╣"
BOT = "╚" + "═" * W + "╝"


# ─── HUD ──────────────────────────────────────────────
def detect_hud() -> dict:
    hud = {
        "mic": False, "llm": False, "llm_name": "?",
        "rag": 0, "speaker": False, "voice": "?",
        "agents": 0, "modules": 0,
    }
    with contextlib.suppress(Exception):
        r = subprocess.run(["pactl", "get-default-source"],
                           capture_output=True, text=True, timeout=2)
        hud["mic"] = bool(r.stdout.strip())

    with contextlib.suppress(Exception):
        import json
        import urllib.request
        with urllib.request.urlopen(
            "http://localhost:11434/api/tags", timeout=2
        ) as resp:
            data = json.load(resp)
            models = [m["name"] for m in data.get("models", [])]
            hud["llm"] = bool(models)
            qw = [m for m in models if "qwen" in m.lower()]
            hud["llm_name"] = (
                qw[0].split(":")[0] if qw else (models[0].split(":")[0] if models else "?")
            )

    with contextlib.suppress(Exception):
        v = Path.home() / "aura-companion/voices/ru_RU-irina-medium.onnx"
        hud["speaker"] = v.exists() or shutil.which("piper") is not None
        hud["voice"] = "Ирина" if v.exists() else "?"

    # F-102e: HUD RAG — прямой путь к ChromaDB
    import sqlite3
    chroma_db = Path.home() / ".local/share/aura/rag_db/chroma.sqlite3"
    if chroma_db.exists():
        try:
            conn = sqlite3.connect(str(chroma_db))
            cur = conn.execute("SELECT COUNT(*) FROM embeddings")
            hud["rag"] = cur.fetchone()[0]
            conn.close()
        except Exception:
            hud["rag"] = -1  # покажет -1 если ошибка

    return hud


def render_hud(h: dict) -> str:
    def mk(ok: bool) -> str:
        return f"{G}●{R}" if ok else f"{RED}○{R}"

    return "\n".join([
        TOP,
        row(f"{B}🛸  AURA  {R}{D}— Капитан видит сквозь{R}"),
        MID,
        row(f"  {mk(h['mic'])} Микрофон    {D}T-one STT{R}"),
        row(f"  {mk(h['llm'])} LLM         {h['llm_name']}"),
        row(f"  {mk(h['speaker'])} Голос       Piper · {h['voice']}"),
        row(f"  {G}●{R} RAG         {h['rag']} диалогов"),
        row(f"  {G}●{R} Агентов     {h['agents']}  ·  модулей {h['modules']}"),
        BOT,
    ])


# ─── Категории и действия ─────────────────────────────
MENU = [
    ("music",    "🎵 Музыка",          ["включи музыку", "тише", "громче",
                                        "следующий трек", "предыдущий трек",
                                        "пауза", "стоп музыку"]),
    ("windows",  "🖥  Рабочие столы",   ["обзор", "следующий рабочий стол",
                                        "предыдущий рабочий стол",
                                        "новый рабочий стол"]),
    ("overview", "📺 Обзор и статус",  ["обзор", "что в фокусе",
                                        "диагностика", "статус системы"]),
    ("weather",  "🌤  Погода",          ["какая погода", "погода на завтра",
                                        "погода на дачу"]),
    ("time",     "🕐 Время, дата",     ["сколько времени", "какое число",
                                        "календарь на сегодня"]),
    ("meds",     "💊 Таблетки",        ["таблетки", "напомни про таблетки"]),
    ("sos",      "🚨 SOS",             ["sos", "вызов скорой"]),
    ("memory",   "🧠 Память",          ["что ты знаешь о себе",
                                        "сколько фактов", "статистика"]),
    ("apps",     "🚀 Приложения",      ["открой браузер", "открой терминал",
                                        "открой файлы"]),
    ("settings", "⚙️  Настройки",      ["статус", "настройки", "громкость"]),
]


def render_menu() -> str:
    lines = [TOP,
             row(f"{B}ВЫБЕРИ КАТЕГОРИЮ{R}"),
             MID]
    for i, (_k, label, _a) in enumerate(MENU, 1):
        lines.append(row(f"  [{i:2}] {label}"))
    lines.append(MID)
    lines.append(row(f"  [{B}.{R} ]  {D}свободный текст{R}"))
    lines.append(row(f"  [{B}0{R} ]  выход"))
    lines.append(BOT)
    return "\n".join(lines)


def render_sub(key: str) -> str:
    for k, label, actions in MENU:
        if k == key:
            lines = [TOP, row(f"{B}{label}{R}"), MID]
            for i, a in enumerate(actions, 1):
                lines.append(row(f"  [{i}] {a}"))
            lines.append(MID)
            lines.append(row(f"  [{B}0{R}] назад"))
            lines.append(BOT)
            return "\n".join(lines)
    return ""


def ask(prompt: str = "> ") -> str:
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        return "0"


# ─── Отправка в оркестратор ───────────────────────────
async def send(orch, text: str) -> str:
    from aura.core.protocol import AgentRequest
    req = AgentRequest(text=text)
    try:
        agent = orch.registry.find(req) if hasattr(orch.registry, "find") else None
        if agent is not None:
            resp = await agent.handle(req)
            return getattr(resp, "text", None) or str(resp)
        return await orch.process(text)
    except Exception as e:
        return f"❌ {e}"


# ─── Главный цикл ─────────────────────────────────────
async def _loop() -> int:
    from aura.bootstrap import build_orchestrator
    orch = build_orchestrator()

    speaker = None
    with contextlib.suppress(Exception):
        from aura.agents.speaker import AgentSpeaker
        speaker = AgentSpeaker()

    def say(text: str) -> None:
        if speaker is not None and text:
            with contextlib.suppress(Exception):
                speaker.say(text)
                speaker.wait(timeout=30)

    def pause() -> None:
        with contextlib.suppress(EOFError, KeyboardInterrupt):
            input(f"\n{D}Enter...{R}")

    while True:
        clear()
        print(render_hud(detect_hud()))
        print()
        print(render_menu())
        print()
        raw = ask(f"{B}Выбор > {R}")

        if raw in ("0", "q", "quit", "exit", "выход"):
            break

        if raw in (".", "..", "т", "текст"):
            clear()
            print(render_hud(detect_hud()))
            print()
            print(f"{D}Свободный текст. 'назад' — вернуться.{R}")
            while True:
                free = ask(f"{C}текст > {R}")
                if free.lower() in ("назад", "back", "0"):
                    break
                if not free:
                    continue
                print(f"{D}...{R}")
                ans = await send(orch, free)
                print(f"🤖 {ans}")
                say(ans)
            continue

        if raw.isdigit():
            idx = int(raw)
            # F-102c: числа вне диапазона — не в LLM
            if idx > len(MENU):
                print(f"❌ Нет варианта {idx}. Диапазон 1–{len(MENU)}.")
                pause()
                continue
            if 1 <= idx <= len(MENU):
                key, label, actions = MENU[idx - 1]
                while True:
                    clear()
                    print(render_hud(detect_hud()))
                    print()
                    print(render_sub(key))
                    print()
                    sub = ask(f"{B}{label} > {R}")
                    if sub in ("0", "q", "назад", ""):
                        break
                    if sub.isdigit():
                        ai = int(sub)
                        if ai > len(actions):
                            print(f"❌ Нет варианта {ai}. Диапазон 1–{len(actions)}.")
                            pause()
                            continue
                        if 1 <= ai <= len(actions):
                            phrase = actions[ai - 1]
                            print(f"{D}→ {phrase}{R}")
                            ans = await send(orch, phrase)
                            print(f"🤖 {ans}")
                            say(ans)
                            pause()
                continue

        if raw:
            ans = await send(orch, raw)
            print(f"🤖 {ans}")
            say(ans)
            pause()

    print(f"\n{G}🦾 До связи, Капитан.{R}")
    return 0


def main() -> int:
    try:
        return asyncio.run(_loop())
    except KeyboardInterrupt:
        print()
        return 0


if __name__ == "__main__":
    sys.exit(main())
