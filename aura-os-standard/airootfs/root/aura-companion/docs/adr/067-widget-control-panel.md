# ADR-067: Widget Control Panel

**Дата:** 2026-10-01
**Статус:** Принято

## Контекст

Управление Aura сейчас требует терминала: `systemctl --user restart aura`,
`ps aux | grep aura_main`, `kill <PID>`, `rm ~/.cache/aura/aura_pause.flag`.
Это узкое место (Theory of Constraints): каждая итерация разработки
начинается с 30–60 секунд работы в терминале и переключения контекста.

Bug 67 (залипание ASR) требует немедленного аварийного останова. Без
быстрого контроля итерация «правка → проверка → рестарт» деградирует.

## Решение

KDE Plasma Widget (QML) + DBus backend `aura-widget.service`.
Одно ядро состояния (`aura/core/state.py`) на все UI.
Loose Coupling: UI не знает внутренностей Aura.

### Архитектура

    ┌──────────────────────────────────────┐
    │ QML Widget (Control Panel)           │
    │  - кнопки, статус, submenu           │
    └────────────────┬─────────────────────┘
                     │ DBus: org.aura.Widget
    ┌────────────────▼─────────────────────┐
    │ aura-widget.service                  │
    │  ├ ControlService                    │
    │  ├ ReconService                      │
    │  ├ InfoService                       │
    │  ├ LogService                        │
    │  ├ MaintenanceService                │
    │  └ EmergencyService                  │
    └────────────────┬─────────────────────┘
                     │ DBus: StateChanged + subprocess
    ┌────────────────▼─────────────────────┐
    │ aura_main.py + listener.py           │
    └──────────────────────────────────────┘

### Общее ядро

`aura/core/state.py` — enum State (IDLE/LISTENING/THINKING/SPEAKING/
ERROR/PAUSED), publish/subscribe. Единственный источник правды.
Все UI (Control Widget, Dragon Core, будущие) подписаны на него.

### Реестр операций (25)

| # | Группа | Операция | Ядро | Приоритет |
|---|---|---|---|---|
| 1 | Control | Pause/Resume | flag `~/.cache/aura/aura_pause.flag` | 🔴 |
| 2 | Control | Restart | systemd | 🔴 |
| 3 | Control | Stop | systemd | 🔴 |
| 4 | Control | Kill | systemd SIGKILL | 🔴 |
| 5 | Control | Start | systemd | 🟡 |
| 6 | Recon | Recon (base/bugs/widget/all) | `aura_recon <tag>` | 🔴 |
| 7 | Recon | Health | `aura_health.py` | 🟡 |
| 8 | Recon | Bug bundle | `aura_bug_bundle` | 🟡 |
| 9 | Recon | Log bundle | journalctl --since | 🟡 |
| 10 | Info | Status | `aura_health.py --status` | 🟡 |
| 11 | Info | Snapshot | `aura_snapshot` | 🟡 |
| 12 | Info | Git dirty | git status | 🟢 |
| 13 | Info | Counts | grep+wc | 🟢 |
| 14 | Logs | Live log | journalctl -f | 🟡 |
| 15 | Logs | Last 100 | journalctl -n | 🟢 |
| 16 | Logs | Errors | journalctl -p err | 🟡 |
| 17 | Maintenance | Cleanup | `aura_cleanup` | 🟡 |
| 18 | Maintenance | Update | git pull + pip | 🟢 |
| 19 | Maintenance | Reset cache | rm ~/.cache/aura | 🟢 |
| 20 | Integration | Open config | $EDITOR | 🟢 |
| 21 | Integration | Open project | dolphin | 🟢 |
| 22 | Emergency | Mute mic | wpctl set-mute | 🔴 |
| 23 | Emergency | Panic | composite | 🟡 |
| 24 | Visual | State widget | DBus | 🟢 |
| 25 | Visual | CPU sparkline | metrics | 🟢 |

### Слои

1. Domain (`aura/core/state.py`) — 100% покрытие
2. Service (`aura/services/*.py`) — mockable adapters
3. Adapter (systemd, journal, wpctl) — за интерфейсами
4. UI (QML) — тонкий клиент

## Последствия

- Ускорение цикла разработки (ToC снят)
- Bug 67 больше не блокирует (Kill в один клик)
- Dragon Core (ADR-062) подключается к тому же ядру без переделки
- Требует `python-dbus` или `sdbus` в venv (отдельный ADR)
- QML не юнит-тестируется — smoke через qmlscene

## Ссылки

- ADR-050 (aura_health read-only)
- ADR-062 (Dragon Core, в VISION)
- ADR-068 (Recon subsystem)
- ADR-069 (Pause via flag)
- ADR-070 (DBus adapter strategy)
