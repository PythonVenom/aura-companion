# ADR-016: Plasma Architecture — универсальная интеграция с цифровым миром

## Дата
2026-09-27

## Статус
Принято

## Контекст

Сейчас Aura работает с **Максом** через:
- **Firefox bridge** (`content_max.js` + `background.js` + `aura_firefox_host.py`).
- **Pull** через `get_last_message_preview` (list_chats каждые 30 сек).
- **ProactiveEngine** для детекта новых сообщений.

**Проблема:** этот код **специфичен для Макса**. При добавлении **Telegram, VK, YouTube, Gmail, Rutube** придётся:
- Писать **новый** content script для каждого.
- Дублировать логику детекта новых событий.
- Менять `proactive.py` под каждый сайт.
- Ломаться при редизайне сайта.

**Что хочет автор (метафора):** Aura должна быть **как плазма** — принимать **форму контейнера** (интерфейса сайта) и **сцепляться** с ним. Не «Aura под Макс», а **универсальный адаптер**.

## Наука — что говорит

### Adapter Pattern (GoF, 1994)

> Обёртка вокруг несовместимого интерфейса, чтобы он стал совместим.

**Применение:** Aura знает **общий интерфейс**. Каждый сайт — **свой adapter**.

### Chain of Responsibility (GoF, 1994)

> Запрос проходит по цепочке обработчиков. Первый, кто справился — отвечает.

**Применение:** DOM → API → Vision → помощь пользователя. Первый непустой результат.

### Graceful Degradation (Nygard, «Release It!», 2007)

> Система должна **деградировать**, а не падать.

**Применение:** если DOM сломался, Aura переключается на Vision. Не «ошибка», а «другой метод».

### Antifragility (Taleb, «Antifragile», 2012)

> Не «устойчивость» (выдерживает удары), не «хрупкость» (ломается), а **усиливается** от давления.

**Применение:** каждый сломанный adapter → новый уровень fallback. Aura **становится сильнее** от проблем.

### Assistive Technology (AT-SPI, Linux)

> Screen readers (Orca, NVDA) дают **семантический** доступ к любому GUI.

**Применение:** **миссия проекта** — люди с ограничениями. AT-SPI — **правильный** путь для незрячих.

### Model Context Protocol (Anthropic, 2024)

> Стандарт для LLM-tools. Позволяет Aura дёргать сервисы через единый протокол.

**Применение:** **дверь в будущее**. Когда Telegram/VK/Gmail выпустят MCP-серверы — Aura подключится без своего кода.

## Решение

**Plasma Architecture** — многоуровневая интеграция с универсальным интерфейсом.

### Уровни интеграции (chain of responsibility)

```
1. DOM adapter       ← основной. Быстро. Без токенов.
2. API adapter       ← стабильно. Токены.
3. Vision adapter    ← универсально. Медленно.
4. AT-SPI adapter    ← для screen readers (миссия).
5. MCP adapter       ← будущее. Единый стандарт.
6. Спросить тебя     ← graceful fallback.
```

**Каждый сайт реализует что может:**
- **Макс:** DOM + Vision.
- **Telegram:** DOM + API (Bot API) + Vision.
- **Gmail:** API (IMAP) + Vision.
- **YouTube:** DOM + Vision.
- **ВК:** DOM + API + Vision.
- **Игры/RDP:** Vision only.
- **Незрячий режим:** AT-SPI + голос.
- **Будущее:** MCP — когда появится.

### Интерфейс SiteAdapter

```python
from abc import ABC, abstractmethod

class SiteAdapter(ABC):
    """Универсальный интерфейс для интеграции с сайтом."""

    site: str  # «max», «vk», «youtube»

    # Уровень 1: DOM (основной)
    def dom_list(self) -> list | None:
        return None

    def dom_send(self, target: str, text: str) -> bool | None:
        return None

    def dom_find(self, query: str) -> dict | None:
        return None

    # Уровень 2: API (fallback)
    def api_list(self) -> list | None:
        return None

    def api_send(self, target: str, text: str) -> bool | None:
        return None

    # Уровень 3: Vision (универсально)
    def vision_list(self) -> list | None:
        return None

    def vision_send(self, target: str, text: str) -> bool | None:
        return None

    # Уровень 4: AT-SPI (screen readers)
    def atspi_list(self) -> list | None:
        return None

    # Уровень 5: MCP (будущее)
    def mcp_list(self) -> list | None:
        return None

    # Единая точка входа — chain of responsibility
    def list_items(self) -> list:
        return (
            self.dom_list()
            or self.api_list()
            or self.vision_list()
            or self.atspi_list()
            or self.mcp_list()
            or []
        )

    def send(self, target: str, text: str) -> str:
        if self.dom_send(target, text):
            return f"🌐 [{self.site}] Отправила через DOM"
        if self.api_send(target, text):
            return f"🌐 [{self.site}] Отправила через API"
        if self.vision_send(target, text):
            return f"🌐 [{self.site}] Отправила через Vision"
        return f"🌐 [{self.site}] Не удалось отправить"

    def find(self, query: str) -> dict | None:
        return (
            self.dom_find(query)
            or self.vision_find(query)
            or None
        )
```

### Реестр adapter'ов

```python
ADAPTERS = {
    "max":      MaxAdapter,
    "vk":       VkAdapter,
    "telegram": TelegramAdapter,
    "youtube":  YouTubeAdapter,
    "gmail":    GmailAdapter,
}

def get_adapter(site: str) -> SiteAdapter | None:
    cls = ADAPTERS.get(site)
    return cls() if cls else None
```

### Aura не знает про сайты

**Плохо (сейчас):**
```python
# messenger.py
def get_last_message_preview(self): ...  # только для Макса
```

**Хорошо (после рефакторинга):**
```python
# messenger.py
def list_all(self, site: str) -> list:
    adapter = get_adapter(site)
    return adapter.list_items() if adapter else []
```

**Aura спрашивает:** «что в telegram» → adapter.list_items().

### ProactiveEngine — универсальные триггеры

**Не «max_new_message», а «new_message(site)».**

```python
def new_message_trigger(site: str, get_adapter) -> Trigger:
    adapter = get_adapter(site)
    def condition(state):
        items = adapter.list_items()
        # сравнить с snapshot в state
        ...
    return Trigger(name=f"{site}_new_message", ...)
```

**Регистрируем триггер для каждого сайта.** Один код — N сайтов.

## Философия — почему именно так

### Миссия проекта (manifesto.md)

**Люди с ограничениями — главная аудитория.**

| Аудитория | Что нужно | Уровень |
|---|---|---|
| Незрячие | AT-SPI + голос | Уровень 4 |
| Моторные | Голос + Vision | Уровень 3 |
| Пожилые | DOM + голос | Уровень 1 |
| Ментальные | Proactive + напоминания | Уровень 1 |

**AT-SPI** — **не «плюс»**, а **требование** для миссии. Без него незрячий не сможет.

### Долгосрочно (roadmap)

- **Фаза 23** — кроссбраузерное расширение (MV3 + polyfill).
- **Фаза 24** — Telegram, VK, YouTube adapters.
- **Фаза 25** — AT-SPI adapter (для незрячих).
- **Фаза 26** — MCP adapter (когда появится экосистема).
- **Фаза 27** — Vision-only режим (для игр, RDP, canvas).

**Каждая фаза = один adapter. Aura не меняется.**

## Последствия

### Положительные

- **Один интерфейс** — Aura не знает про сайты.
- **Chain of Responsibility** — 3–5 уровней fallback.
- **Пластичность** — принимает форму любого сайта.
- **Масштабируемость** — 20 сайтов без переписывания Aura.
- **Миссия** — AT-SPI для незрячих.
- **Будущее** — MCP-совместимость.

### Отрицательные

- **Сложнее код** — интерфейс с 15+ методами.
- **Тесты ×N** — для каждого уровня.
- **Двойной-тройной fallback** — медленнее при провале.
- **Дублирование** — каждый adapter пишет 2–3 уровня.

### Риски

- **Sites ban automation** — ВК, Instagram. Митигация: Vision (не детектится).
- **DOM меняется** — adapter ломается. Митигация: тесты + API fallback.
- **AT-SPI медленный** — DBus задержки. Митигация: кэш + асинхрон.
- **MCP не принят** — стандарт молодой. Митигация: не критично, добавляем позже.

## Что НЕ делаем

- ❌ Не пишем свой API-прокси (нарушает ToS).
- ❌ Не обходим капчу автоматически (этика).
- ❌ Не скрейпим чужие данные (privacy).
- ❌ Не делаем всё сразу — по одному adapter.

## Реализация — фазы

| Фаза | Что | Срок |
|---|---|---|
| **16.1** | ADR-016 (этот) + интерфейс SiteAdapter | 30 мин |
| **16.2** | Рефакторинг Макса под SiteAdapter | 2 часа |
| **16.3** | ProactiveEngine: триггеры по site | 1 час |
| **16.4** | Telegram adapter (DOM + Bot API) | 1–2 дня |
| **16.5** | VK adapter (DOM + API) | 1–2 дня |
| **16.6** | YouTube adapter (DOM) | 1 день |
| **16.7** | AT-SPI adapter (миссия) | 2–3 дня |
| **16.8** | MCP adapter (когда появится) | отложено |

**Итого: 1–2 недели на основную часть.**

## Связь

- **ADR-013** — Dialogue Manager (независим от сайта).
- **ADR-014** — Proactive Assistant (триггеры по site).
- **ADR-015** — Calendar from Chats (парсинг — per-site).
- **manifesto.md** — миссия (люди с ограничениями).
- **roadmap.md** — Фазы 23–27.

## Ссылки

- GoF, «Design Patterns», 1994 — Adapter, Chain of Responsibility.
- Fowler, «PEAA», 2002 — Adapter.
- Nygard, «Release It!», 2007 — Graceful degradation.
- Taleb, «Antifragile», 2012.
- AT-SPI documentation (Linux Foundation).
- Anthropic, «Model Context Protocol», 2024.
- Nygard, «Documenting Architecture Decisions», 2011.
