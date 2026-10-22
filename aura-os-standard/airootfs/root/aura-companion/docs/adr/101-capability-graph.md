# ADR-101: Capability Graph

**Дата:** 2026-10-02
**Статус:** Принято (MVP)

## Контекст
HTN Planner и ReAct Loop не знают что умеет Aura.
Без карты возможностей они не могут строить планы.

## Решение
`aura/core/capability_graph.py`:
- Capability: name, description, inputs, outputs, tags, handler
- CapabilityGraph: add, get, by_tag, find_for, all_names
- build_default_graph(): ~30 узлов (time, music, window, app,
  browser, vk, care, journal, focus, handsfree, context,
  recon, world, control, power)

Тег `danger` — для confirm-flow (kill, shutdown, close).

Голосом: «что ты умеешь» → AgentCapabilities.

## YAGNI
- Не описывать все 44 агента. 30 = 80% покрытия.
- Не привязывать handler сейчас (позже — direct dispatch).

## Ссылки
ADR-100 (World Model), ADR-102 (HTN Planner, план)
