# AURA — СТАТУС ПРОЕКТА

**Дата:** 2026-10-15  
**Версия:** v8.2.0 «Autonomous»

## Цифры
- Агентов: 118
- Коммитов: 420+
- ADR: 164
- mypy: 0, Ruff: 0
- Тесты: 2600+ pytest

## Компоненты 100%
### Ядро
- Orchestrator, Registry, Protocol, Constitution
- Deterministic, TMR, RadStorage (P3)
- Boot Report, Blackboard, Agent Graph
- MCP Adapter, System Tray, Indicators
- 9 Кластеров (GAIA), 8 LLM-провайдеров
- ZeroMQ, Sandbox, Receipts, Watchdog, Prometheus

### Elder-care (100%)
- SOS, Fall, Meds, Call, FinElder, Safe-word

### Голос (100%)
- F-074, STT, Ducking, Stop, VoicePrint

### Память (7 слоёв + Hub)
- Working, Episodic, Semantic, Emotional
- Prospective, Social, Spatial
- MemoryHub + RAG + ContextRecall

### Видео (5 агентов)
- Camera, FacialEmotion, VideoAnalyzer, Gesture, AVFusion

### Инфраструктура
- Steamworks, Plugin SDK, i18n (7 языков)
- Backup, Idle, Alert, Nightly, MoodHistory, Patterns

### UI для биполярки
- System tray + Super+A, tkinter виджет
- Режим тишины, AuraView

### Характер
- 7 ядер (GLaDOS), Affinity, Quirks, Emotion evolution

### Безопасность
- Rule 0 (OWASP LLM01), Red-team 12/12, Receipts

## Проверка
```
./venv/bin/python -m aura.cli boot-report
./venv/bin/python -m aura.cli doctor
./venv/bin/python scripts/test_elder.py
./venv/bin/python scripts/test_voice.py
./venv/bin/python scripts/test_all_agents.py
./venv/bin/python -m aura.core.agent_watchdog
./venv/bin/python -m aura.web.metrics
./venv/bin/python -m aura.web.debug_dashboard
```

## Чат
```
./venv/bin/python -m aura.chat
./venv/bin/python -m aura.cockpit.ui.widget
```
