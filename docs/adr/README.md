# Architecture Decision Records

Все архитектурные решения проекта Aura.

Формат: [MADR](https://adr.github.io/madr/).

## Список

| # | Название | Статус |
|---|---|---|
| 001 | Modular architecture | Принято |
| 002 | Orchestrator integration | Принято |
| 003 | aura-main parity | Принято |
| 004 | Dead code inventory | Принято |
| 005 | LLM routing | Принято |
| 006 | Barge-in architecture | Принято |
| 007 | AEC echo-cancel | Принято |
| 008 | Monolith decommission | Принято |
| 009 | Barge-in WirePlumber blocker | Отложено |
| 010 | Definition of Done beta | Принято |
| 011 | Modular architecture (v2) | Принято |
| 012 | Dialog FSM | Принято |
| 013 | Dialogue Manager | Принято |
| 014 | Proactive Assistant | Принято |
| 015 | Calendar from Chats | Принято |
| 016 | Plasma Architecture | Принято |
| 017 | Platform Abstraction Layer | Принято |
| 018 | Site Adapters | Принято |
| 019 | Installation Experience | Принято |
| 020 | Testing Strategy | Принято |
| 021 | Flash-install | Принято |
| 022 | Cross-platform strategy | Принято |
| 023 | Voice Customization | Принято |

## Как читать

- **Принято** — реализовано в коде
- **Отложено** — решено, но не реализовано
- **Устарело** — заменено другим ADR

## Как добавить

1. Скопировать шаблон: `docs/adr/XXX-template.md`
2. Заполнить: Контекст, Решение, Последствия
3. Обновить этот README
4. Коммит с `docs(adr): ADR-XXX`
