# Release Checklist — v1.0

**Дата:** 2026-09-28
**Связано:** ADR-010 (Definition of Done)

## Код

- [x] 1000+ тестов, все зелёные
- [x] CI зелёный (последние 10 ранов)
- [x] 33 агента зарегистрированы
- [x] 39 ADR в индексе
- [ ] 24-часовой прогон stability (PASS)
- [ ] Live Bug 15 закрыт (Анастасия)
- [ ] Live VK/TG протестирован

## Документация

- [x] README.md + README.en.md
- [x] MANIFESTO.md
- [x] CHANGELOG.md (Keep a Changelog)
- [x] ARCHITECTURE.md + диаграмма
- [x] docs/manual.md
- [x] docs/manual-simple.md
- [x] docs/troubleshooting.md
- [x] docs/faq.md
- [x] docs/craft-onboarding.md
- [x] docs/professions.md (110+)
- [x] docs/strategy-2026.md
- [ ] Demo-видео (2 мин, OBS) → docs/screenshots/demo.gif

## Маркетинг

- [ ] Habr-статья (черновик 90% в ~/aura_private/habr-draft.md)
- [ ] GitHub Release v1.0 с notes
- [ ] Reddit r/selfhosted + r/linux (посты готовы?)
- [ ] Twitter/X анонс

## Партнёрства

- [ ] Pitch deck для AMD (PARTNERSHIP.md → PDF)
- [ ] Pitch deck для Intel
- [ ] Raspberry Pi Foundation (accessibility-миссия)

## Юрлицо

- [ ] Проверить «Психея» в Роспатенте (класс 9, 42)
- [ ] Проверить «Проводница» в Роспатенте
- [ ] ИП или ООО (когда пойдут деньги)

## Платформы

- [x] Arch Linux
- [x] Ubuntu / Fedora (installers)
- [x] ARM (Raspberry Pi)
- [x] Windows / macOS (PAL)
- [ ] Android (Termux, Q2 2026)

## После v1.0 (Q1 2026)

- Telegram bot (ADR-041)
- Web UI htmx (ADR-042)
- Домен aura-companion.dev
- Blender wrapper live
- Aura Dev (ADR-030)

## Финальный smоke-тест

    aura doctor
    aura check
    pytest tests/ -q
    gh run list --limit 5

Все зелёные → tag v1.0.0 → push --tags → GitHub Release.
