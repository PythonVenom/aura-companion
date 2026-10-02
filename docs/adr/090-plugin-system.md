# ADR-090: Plugin System

**Дата:** 2026-10-02
**Статус:** Принято

## Принцип
Aura = ядро + плагины (как Firefox, VS Code).
Ядро безопасно. Плагины — на свой риск (предупреждаем).

## Формат
~/.local/share/aura/plugins/<id>/
- manifest.json (id, name, version, author, risk_level, data_leaves_device, endpoint, warns, requires, user_consent_required)
- README.md (что делает, куда уходят данные)
- plugin.py (агент, эфемерный — Phase 7)

## CLI
aura_plugin list
aura_plugin install <path> [--force]
aura_plugin remove <id>
aura_plugin info <id>

## Install flow
1. load_manifest(source)
2. if needs_consent: WARN + warnings + input("y/N")
3. copytree to ~/.local/share/aura/plugins/<id>/
4. Logbook event "plugin_installed"

## Ephemeral agents (Phase 7)
- Permanent: 10-15 агентов в RAM (ядро)
- Ephemeral: 200+ на SSD, загрузка по задаче (subprocess)
- Auto-unload: 30 мин без использования

## Правовая защита
- MIT + disclaimer
- README каждого плагина — disclaimers
- Aura = ядро, плагины = community
- Нет ответственности за утечки/расходы/бан

## YAGNI
- Нет валидации кода плагина (позже — signed)
- Нет реестра/marketplace (позже — если будет спрос)

## Реализация (MVP, 2026-10-02)
- aura/core/plugin_manifest.py — парсинг + dataclass
- aura/core/plugin_manager.py — list/get/install/remove
- scripts/aura_plugin.py — CLI
- 8 TDD тестов

## Ссылки
ADR-088 (Multi-AI), ADR-091 (Egress Broker), ADR-084 (Logbook)
