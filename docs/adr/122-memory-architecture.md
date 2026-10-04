# ADR-122: Memory Architecture (10 слоёв)

**Статус:** Accepted
**Дата:** 2026-10-02
**Verified:** будет при первом коде

## Контекст

Текущая память — 4 слоя (Tulving 1972). Наука за 50 лет ушла дальше.
Для семейного ИИ нужны слои, которых нет ни у Alexa, ни у Replika.

## Решение: 10 слоёв

| # | Слой | Наука | Aura |
|---|---|---|---|
| 1 | Sensory | Atkinson & Shiffrin (1968) | ASR/TTS буфер, ~1с |
| 2 | Working | Baddeley & Hitch (1974) | Context window, 20 последних |
| 3 | Episodic | Tulving (1972) | ChromaDB, 945 диалогов |
| 4 | Semantic | Tulving (1972) + MIRIX (2025) | Коллекция facts (новое) |
| 5 | Procedural | Squire (1992) | dispatcher (22 handler) |
| 6 | Prospective | Einstein & McDaniel (1990) | care.py |
| 7 | Emotional | McGaugh (2004) | journal_mood.py |
| 8 | Spatial | Burgess, Maguire & O'Keefe (2002) | context_memory.py (X11) |
| 9 | Social | SocialMemBench (2026) | НОВОЕ (ADR-125) |
| 10 | Meta | MetaMem (2026) | НОВОЕ (ADR-126) |

## Синтез-референсы

- CoALA: Sumers, T. et al. (2024). Cognitive Architectures for Language Agents. TMLR.
- MIRIX: Wang, Y. et al. (2025). MIRIX: Multi-Agent Memory System.
- ZenBrain: (2025). 3-phase consolidation (SWS/REM/SHY), +21.6% F1 на LoCoMo.
- LoCoMo: Maharana, A. et al. (2024). Evaluating Very Long-Term Conversational Memory.

## Архитектура (код)

    aura/core/memory/
    ├── layers.py         — реестр 10 слоёв
    ├── working.py        — кольцевой буфер
    ├── episodic.py       — обёртка над AgentRAGMemory
    ├── semantic.py       — факты subject-predicate-object
    ├── prospective.py    — обёртка над care
    ├── emotional.py      — обёртка над journal_mood
    ├── spatial.py        — обёртка над context_memory
    ├── social.py         — граф семьи (ADR-125)
    ├── meta.py           — confidence (ADR-126)
    ├── consolidator.py   — decay + суммаризация
    └── recall.py         — единая точка запроса

## Recall

Один вход → опрос всех слоёв → ранжирование по:
- Relevance (embedding similarity)
- Recency (Ebbinghaus exponential decay)
- Emotional weight (McGaugh)
- Confidence (Meta layer)

## Последствия

- (+) Aura помнит «что говорил», «что знаю», «кто есть кто», «уверен ли»
- (+) уникальный козырь: Social + Meta
- (−) сложнее recall (объединение из 10 источников)

## Милстоуны

- v4.0: слои 1-9 (кроме Meta)
- v5.0: слой 10 (Meta)
