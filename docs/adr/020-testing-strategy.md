# ADR-020: Testing Strategy

**Дата:** 2026-09-28
**Статус:** Принято

## Контекст

Перед публичным релизом нужна чёткая стратегия тестирования.
Сейчас 897 тестов, но нет единого документа о подходе.

## Решение

### Уровни тестов

| Уровень | Что | Скорость | Покрытие |
|---|---|---|---|
| Unit | Логика агентов | <1 мс | 80%+ |
| Integration | Взаимодействие | 10-100 мс | ключевые пути |
| E2E | Полный цикл | 1-5 сек | smoke |

### Философия

1. **TDD** — тесты до кода
2. **Small batch** — один тест = одно поведение
3. **Mock границ** — Firefox bridge, Ollama, ASR — мокаются
4. **Без hardware** — в CI нет микрофона, GPU, Firefox
5. **Fast feedback** — весь прогон <10 сек

### Исключения в CI

Следующие тесты игнорируются (требуют X11/hardware):
-  — нужен X11
-  — нужен X11
-  — нужен screenshot
-  — тяжёлые зависимости

Они запускаются локально. Это **сознательный trade-off**: CI должен быть быстрым и стабильным.

### Coverage

Целевое покрытие: **85%**.
- Ниже 70% — блокер
- Выше 85% — не гонимся (YAGNI)

### Инструменты

- ============================= test session starts ==============================
platform linux -- Python 3.12.13, pytest-9.1.1, pluggy-1.6.0
rootdir: /home/pythonvenom/aura_project
configfile: pyproject.toml
testpaths: tests
plugins: asyncio-1.4.0, anyio-4.15.1
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 897 items

tests/test_app_launcher.py ...............                               [  1%]
tests/test_at_spi.py .......                                             [  2%]
tests/test_audio_pult.py ..............                                  [  4%]
tests/test_audio_router.py ........................                      [  6%]
tests/test_aura_main.py ................                                 [  8%]
tests/test_barge_in.py ......                                            [  9%]
tests/test_bootstrap.py ..............                                   [ 10%]
tests/test_brain.py .........                                            [ 11%]
tests/test_browser_tabs.py .......................................       [ 16%]
tests/test_calendar_trigger.py ...                                       [ 16%]
tests/test_chat_actions.py ....                                          [ 16%]
tests/test_chat_sense.py ..........                                      [ 17%]
tests/test_chat_sense_auto.py ............                               [ 19%]
tests/test_chat_sense_search.py .....                                    [ 19%]
tests/test_checklist.py ...........                                      [ 21%]
tests/test_checklist_trigger.py ....                                     [ 21%]
tests/test_cli.py ....                                                   [ 21%]
tests/test_context_memory.py ..............                              [ 23%]
tests/test_date_parse.py .......................                         [ 26%]
tests/test_dialog_manager_full.py .........                              [ 27%]
tests/test_dialogue_manager.py ............                              [ 28%]
tests/test_dm_bug6.py ..                                                 [ 28%]
tests/test_dm_bug8.py ...                                                [ 28%]
tests/test_error_handling.py ..                                          [ 29%]
tests/test_focus_switch.py .........                                     [ 30%]
tests/test_fsm.py ........                                               [ 31%]
tests/test_fsm_full.py ......                                            [ 31%]
tests/test_functions.py .............                                    [ 33%]
tests/test_heartbeat.py .......                                          [ 34%]
tests/test_internet.py .....................                             [ 36%]
tests/test_journal.py .........................                          [ 39%]
tests/test_listener_streaming.py ......                                  [ 39%]
tests/test_max_trigger.py .......                                        [ 40%]
tests/test_media_pause.py ......................                         [ 43%]
tests/test_media_pause_routing.py ....                                   [ 43%]
tests/test_media_pult.py .....                                           [ 44%]
tests/test_media_router.py ....                                          [ 44%]
tests/test_media_search.py ............................                  [ 47%]
tests/test_media_state.py .....                                          [ 48%]
tests/test_messenger.py ....................                             [ 50%]
tests/test_messenger_own.py .....                                        [ 50%]
tests/test_modules.py ........                                           [ 51%]
tests/test_mouse.py ..................                                   [ 53%]
tests/test_music_ducker.py .........                                     [ 54%]
tests/test_music_local.py .......................                        [ 57%]
tests/test_orchestrator.py .......                                       [ 58%]
tests/test_pal.py ...........                                            [ 59%]
tests/test_parallel_universe.py ...........                              [ 60%]
tests/test_power.py ...............                                      [ 62%]
tests/test_proactive.py ............                                     [ 63%]
tests/test_proactive_full.py ........                                    [ 64%]
tests/test_rag_memory.py .........................                       [ 67%]
tests/test_recovery.py ...                                               [ 67%]
tests/test_registry.py .....................                             [ 70%]
tests/test_reply_context.py ....                                         [ 70%]
tests/test_screen_reader.py ..................                           [ 72%]
tests/test_security.py .........                                         [ 73%]
tests/test_status.py ..........                                          [ 74%]
tests/test_system_check.py .........                                     [ 75%]
tests/test_task_manager.py ............                                  [ 76%]
tests/test_telegram.py ..............                                    [ 78%]
tests/test_text_editor.py ..............                                 [ 80%]
tests/test_time.py ......................................                [ 84%]
tests/test_tool_router.py ............                                   [ 85%]
tests/test_trigger_bug9.py ....                                          [ 86%]
tests/test_unanswered_extracts_events.py ..                              [ 86%]
tests/test_updates.py .............                                      [ 87%]
tests/test_vault.py ..........                                           [ 88%]
tests/test_vision.py .........                                           [ 89%]
tests/test_vk_music.py .............................                     [ 93%]
tests/test_vk_web.py .................                                   [ 94%]
tests/test_window_control.py ...................                         [ 97%]
tests/test_window_manager.py ..........................                  [100%]

============================= 897 passed in 8.57s ============================== — основной раннер
-  — async тесты
-  — coverage
-  — property-based (опционально)
-  — mutation testing (опционально)

## Последствия

**Плюсы:**
- Единый подход
- Быстрый CI
- Высокое покрытие

**Минусы:**
- Не всё покрыто в CI
- Mock-границы могут расходиться с real

## Связанные

- ADR-010: Definition of Done
