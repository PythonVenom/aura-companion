# ADR-156: Aura как симбиотическая плазма

**Статус:** Принято
**Дата:** 2026-10-05

## Контекст

Aura работает на 14 платформах. Вопрос: как относиться к ОС?

Три варианта:
1. **Заменить ОС** (Redox, Hurd) — 30+ лет, не для одного человека
2. **Быть приложением** — теряем интеграцию, остаёмся «ещё одним окном»
3. **Быть плазмой** — перенимаем форму и свойства ОС, остаёмся собой

## Решение

Aura — **симбиотическая плазма**. Она:
- Течёт в форму ОС (принимает её API, пути, модели)
- Перенимает свойства (безопасность, UX, ecosystem)
- Остаётся одной сущностью (одно ядро, один API для пользователя)
- Не борется с ОС — дополняет её

## Наука

- Margulis 1967 — симбиогенез (слияние ≠ замена)
- Gamma et al. 1994 — Adapter pattern
- Dijkstra 1968 — слои не борются, дополняют
- Nissenbaum 2004 — контекстная приватность
- Bauman 2000 — liquid modernity
- Suchman 1987 — situated action

## Что перенимаем

| ОС | Feature | Как используем |
|---|---|---|
| Astra Linux | MAC Parsec | Метки доступа для медицины бати |
| Astra Linux | ГОСТ Р 34.10-2012 | Подпись данных (если требуется) |
| Astra Linux | ФСТЭК | Готовность к сертификации |
| Windows | SAPI / WSR | TTS/ASR нативно, не через PortAudio |
| Windows | Hello | Биометрия для доступа к медицине |
| Windows | Defender | Cooperative scan (не блокирует) |
| macOS | Keychain | Мастер-ключ SQLCipher там, не в файле |
| macOS | Touch ID | То же, что Hello |
| macOS | Shortcuts | Голосовые команды → Shortcuts |
| Android | Intents | Открытие URL/файлов (уже есть) |
| Android | Foreground service | Постоянная работа Aura |
| Arch | systemd | Aura как user unit |
| Arch | PipeWire | Нативный audio |
| BSD | Capsicum | Capability-based доступ |

## Последствия

### Положительные
- Aura **не конкурирует** с ОС — их интеграция глубже
- Готовность к **госзаказчикам** (Astra + Aura)
- **Нативная безопасность** (не своя, а ОС)
- **Нативный UX** (не свой, а ОС)

### Отрицательные
- **Зависимость от ОС** — если Astra уйдёт, Aura теряет MAC
- **Сложность HAL** — 6+ адаптеров вместо одного
- **Тестирование** — каждый adapter отдельно
- **Документация** — что где работает

### Fallback
- Если ОС feature недоступна → graceful degradation (уже есть в HAL)
- Если ГОСТ-крипто нет → fallback на AES-256 (SQLCipher)

## Связанные ADR

- ADR-092 (Astra Linux)
- ADR-151 (Hardware profiles)
- ADR-155 (Neuro-rights)
- ADR-017 (Platform abstraction)

## Ссылки

- Margulis L. (1967). Origin of Mitosing Cells.
- Gamma E. et al. (1994). Design Patterns.
- Dijkstra E. (1968). The Structure of the THE Multiprogramming System.
- Приказ ФСТЭК №17 (2009).
- ГОСТ Р 34.10-2012.
