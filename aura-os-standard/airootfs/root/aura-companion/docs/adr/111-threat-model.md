# ADR-111: Threat Model (STRIDE + DREAD)

**Статус:** Accepted
**Дата:** 2026-10-02

## Активы

Bridge socket (🔴), Journal (🔴), Care (🔴), VK (🟡), Power (🟡)

## STRIDE

| Угроза | Сценарий | Митигация |
|---|---|---|
| Spoofing | Поддельный клиент к socket | ADR-113 |
| Tampering | Правка content_vk.js | v5 |
| Repudiation | Юзер не помнит | ADR-112 |
| Info disclosure | Journal читается | perms 600 |
| DoS | Flood socket | ADR-115 tarpit |
| Elevation | power.* извне | ADR-113 |

## DREAD > 30

Bridge spoofing (37), Journal leakage (32) — митигация обязательна.
