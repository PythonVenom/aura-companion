# ADR-130: Accessibility (WCAG 2.2 AA + Elder Care)

**Статус:** Accepted
**Дата:** 2026-10-02

## Контекст

Aura — семейный ИИ, у которого elder care в ядре. Accessibility = не опция,
а обязательство. Наука:

- W3C (2023). Web Content Accessibility Guidelines (WCAG) 2.2. W3C Recommendation.
- Lazar, J. et al. (2017). Ensuring Digital Accessibility through Process and Policy.
- WHO (2022). Global report on assistive technology.

## WCAG 2.2 AA — 4 принципа

**POUR**:
- Perceivable — видимо/слышимо
- Operable — управляемо
- Understandable — понятно
- Robust — работает с ассистивными технологиями

## Целевые критерии для Aura

| Критерий | WCAG | Aura |
|---|---|---|
| 1.4.3 Contrast (min) | AA | ≥ 4.5:1 для текста |
| 1.4.4 Resize text | AA | ≥ 200% без потери |
| 1.4.11 Non-text contrast | AA | ≥ 3:1 для UI |
| 2.1.1 Keyboard | A | всё доступно с клавиатуры |
| 2.5.5 Target size | AAA | ≥ 44×44 px (для elder) |
| 1.2.2 Captions | A | все голосовые → текст |
| 3.1.5 Reading level | AAA | просто, коротко (для elder) |

## Elder-care надстройка

- **Шрифт**: минимум 18pt (в 1.5× от обычного)
- **Контраст**: ≥ 7:1 (AAA) — для слабовидящих
- **Голос**: медленнее (0.85× скорость Piper)
- **Ответы**: ≤ 15 слов когда elder_mode=True
- **Таймауты**: нет автоскрытия, диалог ждёт сколько угодно

## Реализация

- `aura/ui/accessibility.py` — настройки + профили
- Профили: `default`, `elder`, `low_vision`, `screen_reader`
- Hook в orchestrator: если elder_mode → ограничение длины ответа

## Метрики

- Contrast ratio всех элементов — измеряется
- Target size — CSS-safe
- Elder-mode: доля ответов > 15 слов — цель 0%

## Последствия

- (+) Aura доступна бабушке/дедушке
- (+) WCAG 2.2 AA сертифицируемо
- (+) уникально на рынке (Alexa не сертифицирована)
- (−) +UI-слой (сейчас только CLI/голос)
- (−) требует ревью всех ответов на длину

## Ссылки

- WCAG 2.2 (W3C, 2023)
- ADR-117 (Constitution)
