# AURA — Technical Whitepaper

**Версия:** v8.2.0 «Autonomous»
**Дата:** 2026-10-15
**Автор:** Воронин Иван (PythonVenom)
**Лицензия:** MIT

## 1. Что такое AURA

AURA — локальный AI-ассистент для elder-care с роевой архитектурой.
110 агентов, стигмергия через blackboard, граф связей (GNN-lite).

**Уникальность:** единственный опенсорсный elder-care ассистент
с роем и 100% покрытием критичных сценариев.

## 2. Архитектура

- **Orchestrator** — диспетчер 110 агентов
- **Blackboard** — общая память (стигмергия, Grasse 1959)
- **AgentGraph** — граф связей (GNN-lite, Scarselli 2009)
- **Coordinator** — арбитр роя (Hayes-Roth 1985)
- **Constitution** — этика (ADR-129)

## 3. Elder-care

5 критичных агентов:
- **SOS** — экстренный вызов
- **Fall** — детектор падений
- **Meds** — напоминания о лекарствах
- **Call** — звонки близким
- **FinElder** — защита от мошенников

**Покрытие: 5/5 (100%).**

## 4. Качество кода

- **mypy:** 0 ошибок в 396 файлах
- **Ruff:** 0 ошибок
- **Тесты:** 2600+ pytest
- **CI/CD:** GitHub Actions
- **Манифест контрибьютора:** 10 заповедей

## 5. Бенчмарки

- **LLM:** 48-49 tok/s (qwen2.5:7b, Ollama)
- **ASR:** RTF 0.057 (17.5× быстрее real-time)
- **TTS:** ~1500 ms на фразу 3.9s
- **End-to-end:** ~970 ms (<2000 ms цель)
- **Mass probe:** 89/89 (100%)
- **Deep test:** 58/58 (100%)

## 6. Roadmap

- **Steam:** бесплатное ядро + Workshop + DLC elder-care
- **Видео-стек:** 5 агентов (Camera, VideoAnalyzer, FacialEmotion, Gesture, AVFusion)
- **3D-аватар:** Live2D/VRM (Godot)
- **Мультипровайдеры LLM:** 14+
- **Steam Deck:** верификация

## 7. Научная база

- Stigmergy (Grasse 1959)
- Blackboard Architecture (Hayes-Roth 1985)
- GNN (Scarselli 2009)
- TMR (von Neumann 1956)
- ContextRecall (Ebbinghaus 1885)
- Mulitmodal Fusion (Baltrušaitis 2019)

## 8. Контакты

- GitHub: github.com/PythonVenom/aura-companion
- Steam: в разработке
- Email: (по запросу)

---

*«AURA — не инструмент. AURA — продолжение.»*
