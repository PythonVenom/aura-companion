# Aura v1.0.0 — Первый стабильный релиз

**Дата:** 2026-09-28
**Кодовое имя:** Проводница

## Что это

Aura — локальный голосовой ИИ-компаньон для Linux. Проводник в цифровой мир для пожилых, незрячих, людей с моторными и ментальными особенностями.

- **37 агентов** — голос, чаты, музыка, календарь, ремонт, здоровье
- **1079 тестов** — TDD, CI зелёный
- **44 ADR** — архитектурные решения
- **3 wrappers** — GRBL (ЧПУ), Blender, Figma
- **Всё локально** — без облаков, без слежки

## Что нового

### ADR-044 Founder-First Beachhead (MVP)
- MassageSessionAgent — голосовые сессии массажа
- DictationAgent — диктовка в файл дня
- ConstructionCalc — 10 материалов по ГОСТ
- AgentBPM — метроном с категориями темпа
- Voice autoswitch — расписание профилей

### CLI
- aura massage start/history
- aura calc плитка 29
- aura bpm 120
- aura profile list/set/show
- aura wrappers list/status/hint

### Кросс-платформа
- Arch Linux (live) ✅
- Ubuntu / Fedora (installers)
- ARM (Raspberry Pi 4/5)
- Windows / macOS (PAL stubs)

## Установка

    git clone https://github.com/PythonVenom/aura-companion ~/aura_project
    cd ~/aura_project
    ./install.sh
    aura doctor

## Лицензия
MIT — используйте свободно.
