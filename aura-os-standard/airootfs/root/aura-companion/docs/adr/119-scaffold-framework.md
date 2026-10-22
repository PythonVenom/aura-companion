# ADR-119: Scaffold Framework

**Статус:** Accepted
**Дата:** 2026-10-02

## Решение

6 scaffold-скриптов (`handler.py`, `route.py`, `locale.py`, `eval.py`, `adr.py`, `release.py`).
Идемпотентны, обратимы (`--undo`), шаблоны в `scripts/scaffold/templates/`.
Цель: v5/v6/v7 закрываются за 30 минут.
