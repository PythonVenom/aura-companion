# ADR-125: Social Memory (Family Graph)

**Статус:** Accepted
**Дата:** 2026-10-02

## Контекст

Alexa/Replika знают «user». Aura должна знать семью.
Это не опция — это её категория. Наш козырь.

## Наука

- SocialMemBench (2026). Benchmarking Social Memory in LLM Agents.
- PERSONA (2023). Personalized Dialogue via Entity Graphs.
- A-Mem (2025). Agentic Memory with entity relations.

Типы рёбер:
- FAMILY_OF (батя ↔ мама)
- PREFERS (батя → Чайковский)
- DISLIKES (мама → шум)
- HAS_ROLE (батя → «сенсорный, любит тишину»)
- EVENT (день рождения 15 мая)
- CONVERSATION_ABOUT (диалог X → тема Y)

## Решение

Граф в aura/core/memory/social.py, SQLite + adjacency list:

Схема entities: id, name, type, aliases, created_at
Схема relations: src_id, dst_id, kind, weight, evidence_json, last_seen
Схема events: id, entity_id, kind, date, payload

## Извлечение

LLM-extractor из каждого диалога:
- Named entities (имена, роли)
- Relations (X сделал Y)
- Preferences (X любит Z)

Промпт: «Извлеки сущности и связи в JSON: {entities:[], relations:[]}».

## Recall

- «что любит батя?» → embedding → find entity батя → relations PREFERS
- «когда ДР у мамы?» → entity мама → events kind=birthday

## Privacy

- Только локально (SQLite в ~/.cache/aura/social.db)
- Опционально: шифрование per-entity
- Кнопка «забудь всё о X» — каскадное удаление

## Последствия

- (+) Aura — член семьи, не ассистент
- (+) уникально на рынке
- (−) LLM-extractor стоит latency на каждый диалог

## Ссылки

- ADR-122 (Memory)
- ADR-126 (Meta)
