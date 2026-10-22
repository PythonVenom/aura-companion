# ADR-105: Bridge Architecture

**Дата:** 2026-10-02
**Статус:** Принято (MVP, работает)

## Контекст
Firefox extension ↔ Aura. Native messaging protocol.
Первая версия: echo-сервер (не работает как мост).
Вторая: race condition (2 host-процесса, timeout).

## Решение
`aura_bridge_host.py` — единственный процесс:
1. **Socket server** (daemon thread) — слушает `/tmp/aura_firefox.sock`
2. **Main loop** — синхронный: Aura → Firefox → Aura
3. Firefox запускает host через native messaging (manifest)

Поток:
    Aura → socket → in_q → main loop → write_msg(stdout) → Firefox
    Firefox → read_msg(stdin) → socket → Aura

Особенности:
- Один процесс (не fork)
- Синхронный request/response (in_q.get() блокирующий)
- Реконнект на стороне extension (browser.runtime.connectNative)
- Host перезапускается Firefox'ом при reload extension

## Требует
- `~/.mozilla/native-messaging-hosts/aura_bridge.json`
- `aura-bridge@pythonvenom.local` в manifest extension
- При reload: `pkill -f aura_bridge_host && rm -f /tmp/aura_firefox.sock`

## Ссылки
ADR-011 (Firefox bridge, оригинал), ADR-077 (UI Agent)
