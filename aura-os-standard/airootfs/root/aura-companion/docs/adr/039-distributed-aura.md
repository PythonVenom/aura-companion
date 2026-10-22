# ADR-039: Distributed Aura

**Дата:** 2026-09-28
**Статус:** Проект
**Связано:** ADR-029, ADR-032, ADR-038

## Контекст

У семьи может быть:
- Box в гостиной (медиа, LLM)
- Box в мастерской (ЧПУ)
- Android у каждого
- NUC у родителей

Как связать? Как обрабатывать голос?

## Решение

**Федерация Aura** — несколько ядер работают как одно.

### Модели

1. **Primary + Secondary** (сейчас)
   - Primary Box — LLM, ASR, TTS
   - Secondary — только wake-word + stream audio → Primary

2. **Peer-to-peer** (2027)
   - Каждый Box — полноценное ядро
   - Discovery через mDNS
   - MapReduce-style: задача → ближайший

3. **Hub-and-spoke** (для больших объектов)
   - Центральный Aura Server (Strix Halo)
   - 10+ тонких клиентов (Pi Zero, Android)

### Протокол

- **Discovery:** mDNS (`_aura._tcp.local`)
- **Auth:** mTLS через общий CA, JWT rotation
- **Sync state:** CRDT (Yjs / Automerge) — таймеры, напоминания, история
- **LLM routing:** локальный если есть GPU, иначе → Primary

### Сценарии

**Дом с мастерской:**

    [Pi Zero: спальня]──┐
                        ├──► [N100: гостиная, LLM, ASR]
    [Pi Zero: кухня]────┤
                        │
    [Pi 5: мастерская]──┤
                        │
    [Android: муж]──────┤
                        │
    [Android: жена]─────┘

**Клиника:**

    [Aura Studio: сервер, 32B LLM]
    ├─ [кабинет 1: Pi 5 + микрофон]
    ├─ [кабинет 2: Pi 5 + микрофон]
    └─ [кабинет 3: Pi 5 + микрофон]

### Безопасность

- **Сегментация:** медицина/бухгалтерия — отдельная сеть
- **Шифрование:** WireGuard между узлами
- **ACL:** какие агенты доступны на каком Box
- **Ревокация:** если устройство украдено → выдалить по mTLS serial

### Что НЕ делаем

- Cloud sync (privacy)
- Blockchain (marketing hype)
- Свой mesh-протокол (используем WireGuard + mDNS)

## Последствия

**Плюсы:** масштабируется, отказоустойчиво, privacy
**Минусы:** сложно (CRDT, discovery)
**Сроки:** Primary+Secondary — Q4 2026; P2P — 2027

## Связанные
- ADR-029 (Multi-client)
- ADR-032 (JSON-RPC)
- ADR-038 (Hardware)
