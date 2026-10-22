"""Health API — HTTP-эндпоинт статуса AURA.

Наука: Health Check Pattern (Nygard 2007).
Формат: JSON. Опционально Prometheus.
"""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any


def _get_status() -> dict[str, Any]:
    """Собрать статус AURA."""
    status: dict[str, Any] = {"status": "unknown"}
    try:
        from aura.bootstrap import build_orchestrator
        status["agents"] = len(build_orchestrator())
    except Exception as e:
        status["agents_error"] = str(e)
    try:
        from aura.core.cluster_health import summary
        s = summary()
        status["clusters"] = {"total": s["total"], "ok": s["ok"],
                              "degraded": s["degraded"], "fail": s["fail"]}
    except Exception:
        pass
    try:
        from aura.core import blackboard as bb
        snap = bb.snapshot()
        status["sector"] = snap.get("sector", "unknown")
        status["alerts"] = len(bb.recent_alerts(window_sec=300))
    except Exception:
        pass
    try:
        from aura.indicators import is_online, is_silent
        status["online"] = is_online()
        status["silent"] = is_silent()
    except Exception:
        pass

    # Финальный статус
    if status.get("agents", 0) > 0 and status.get("clusters", {}).get("fail", 0) == 0:
        status["status"] = "ok"
    else:
        status["status"] = "degraded"
    return status


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path in ("/", "/health", "/status"):
            body = json.dumps(_get_status(), ensure_ascii=False, indent=2).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *args) -> None:
        pass  # тихо


def serve(port: int = 8734, host: str = "127.0.0.1") -> None:
    """Запустить HTTP health сервер."""
    server = HTTPServer((host, port), HealthHandler)
    print(f"🛸 Health API: http://{host}:{port}/health")
    server.serve_forever()


def main() -> None:
    try:
        serve()
    except KeyboardInterrupt:
        print("\n🦾 Health API остановлен")


if __name__ == "__main__":
    main()


__all__ = ["_get_status", "main", "serve"]
