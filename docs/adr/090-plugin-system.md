# ADR-090: Plugin System

**Дата:** 2026-10-02
**Статус:** Проект

## Принцип
Aura = ядро + плагины (как Firefox, VS Code).
Ядро безопасно. Плагины — на свой риск (предупреждаем).

## Формат
~/.local/share/aura/plugins/<id>/
- manifest.json (риски, endpoint, warns)
- README.md (что делает, куда уходят данные)
- config.json (api_key через env)
- plugin.py (агент)

## Установка
aura plugin install <id>
→ warning
→ user consent [y/N]
→ api_key
→ ok

## Ephemeral agents
- Permanent: 10-15 агентов в RAM
- Ephemeral: 200+ на SSD, загрузка по задаче (subprocess)
- Auto-unload: 30 мин без использования

## Правовая защита
- MIT + diskлеймер
- README каждого плагина — disclaimers
- Aura = ядро, плагины = community
- Нет ответственности за утечки/расходы/бан

## YAGNI
- Не пишем свой D-Bus/marketplace
- Не валидируем плагины (позже — signed)

## Ссылки
ADR-088, ADR-091, ADR-084
