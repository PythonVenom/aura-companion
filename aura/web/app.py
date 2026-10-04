"""Aura Web UI (ADR-042) — skeleton.

FastAPI + htmx + Jinja2. Порт 8080.
Graceful: если fastapi не установлен — не падаем.
"""
from __future__ import annotations

HTML_HOME = """<!doctype html>
<html lang="ru"><head><meta charset="utf-8">
<title>Aura Web</title>
<script src="https://unpkg.com/htmx.org@1.9.10"></script>
<style>body{font-family:system-ui;max-width:780px;margin:2rem auto;padding:1rem}
input,button{padding:.5rem;font-size:1rem}
#out{margin-top:1rem;padding:1rem;background:#f5f5f5;border-radius:6px;white-space:pre-wrap}</style>
</head><body>
<h1>🌟 Aura Web</h1>
<p>Локальный клиент к ядру. Введи команду:</p>
<form hx-post="/cmd" hx-target="#out" hx-swap="innerHTML">
  <input name="text" placeholder="Аура, таймер 5 минут" size="40" autofocus>
  <button>→</button>
</form>
<div id="out">Ожидаю команду...</div>
<ul>
  <li><a href="/status">/status</a></li>
  <li><a href="/agents">/agents</a></li>
</ul>
</body></html>"""


def create_app():
    try:
        from fastapi import FastAPI, Form
        from fastapi.responses import HTMLResponse
    except ImportError:
        print("❌ fastapi не установлен: pip install fastapi uvicorn")
        return None

    app = FastAPI(title="Aura Web")

    @app.get("/", response_class=HTMLResponse)
    def home():
        return HTML_HOME

    @app.post("/cmd", response_class=HTMLResponse)
    async def cmd(text: str = Form("")):
        if not text.strip():
            return "<i>Пустая команда</i>"
        try:
            from aura.bootstrap import build_orchestrator
            orch = build_orchestrator()
            result = await orch.process(text)
            return f"<b>→</b> {result}"
        except Exception as e:
            return f"<b style='color:red'>❌</b> {e}"

    @app.get("/status", response_class=HTMLResponse)
    def status():
        try:
            from aura.bootstrap import build_orchestrator
            orch = build_orchestrator()
            return f"<p>✅ Ядро: {len(orch)} агентов</p><a href='/'>←</a>"
        except Exception as e:
            return f"<p>❌ {e}</p><a href='/'>←</a>"

    @app.get("/agents", response_class=HTMLResponse)
    def agents():
        try:
            from aura.bootstrap import build_orchestrator
            orch = build_orchestrator()
            names = sorted(a.name for a in orch.registry)
            return "<ul>" + "".join(f"<li>{n}</li>" for n in names) + "</ul><a href='/'>←</a>"
        except Exception as e:
            return f"<p>❌ {e}</p>"

    return app


def main() -> None:
    app = create_app()
    if app is None:
        return
    try:
        import uvicorn
        uvicorn.run(app, host="127.0.0.1", port=8080)
    except ImportError:
        print("❌ uvicorn не установлен: pip install uvicorn")


if __name__ == "__main__":
    main()
