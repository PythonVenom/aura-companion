# AURA · GAPS (обновлено 2026-10-15)

## ✅ ЗАКРЫТО ЗА СЕССИЮ 14-15.10

- Watchdog speaker — работает
- RAG embedding 404 — исправлено (nomic-embed-text)
- Captain agent — есть (aura/agents/captain.py)
- Identity.yaml — внедрён (config/identity.yaml)
- TUI/Cockpit — 10+ файлов (aura/cockpit/)
- Game layer — 5 файлов (aura/game/)
- Screen capture (grim) — есть (aura/agents/vision.py)
- OCR (tesseract) — есть
- Notifications — частично
- Blackboard + Coordinator + AgentGraph — есть (рой)
- MCP adapter — есть (aura/core/mcp_adapter.py)
- CI/CD — есть (.github/workflows/ci.yml)
- CONTRIBUTING.md — есть

## 🔴 БЛОКЕРЫ (2)

1. Микрофон AEC — полное эхо-подавление (сейчас VAD+gate)
2. Дублирование aura_project vs aura-companion

## 🏗️ АРХИТЕКТУРА (6)

3. Rituals (утро/вечер) — нет
4. Curiosity Engine — нет
5. User Profile — нет
6. Learnings — нет
7. Initiative — нет
8. Self-Model — нет

## 🔌 ИНФРАСТРУКТУРА (8)

9. tg_bridge — stub
10. vk_bridge — stub
11. max_bridge — stub
12. whatsapp_bridge — stub
13. Astra Linux адаптер (F-092) — план
14. Эльбрус e2k (F-038) — план
15. ARM адаптер — нет
16. Fedora адаптер — нет

## 💻 КОД (10)

17. Mentor TUI add/edit — нет
18. Profile Ledger Ed25519 — нет
19. WineLauncher (F-052) — нет
20. CarHistory + 1С (F-053) — нет
21. AgentCANBus (F-050) — нет
22. DTC 500+ (F-051) — нет
23. DBus API (F-045) — нет
24. Configurator GTK4 (F-046) — нет
25. Self-Model — нет
26. Meta-Memory — базово

## 🎯 ПРИОРИТЕТЫ ТОП-1

1. 90+ агентов вне elder-care — прогнать живьём
2. ContextRecall — тест на месяц
3. AgentGraph → визуализация
4. TMR/RadStorage → elder-care
5. Бенчмарки GAIA/SWE-bench
6. Публикация на Хабр (когда разморозишь)
