# ADR-021: Flash-install

**Дата:** 2026-09-28
**Статус:** Принято

## Контекст

ADR-019 описал три уровня установки. Сейчас реализуем Уровень 1 — Flash-install для нетехнических пользователей.

## Решение

### Архитектура

USB flash содержит:
- Arch ISO + Aura
- install-aura.sh (auto-installer)
- aura_project (копия репо)
- systemd: auto-install.service

### Процесс для пользователя

1. Вставить флешку
2. Загрузиться с неё (F12/F2 при старте)
3. Ответить на 2 вопроса: диск и подтверждение
4. Ждать 5-10 мин
5. Перезагрузка — готовая Aura

### Компоненты

- contrib/flash/install-aura.sh — auto-installer
- contrib/flash/mkarchiso-profile.txt — инструкция
- contrib/flash/make_flash_image.sh — сборщик

### Что НЕ делаем (YAGNI)

- GUI-установщик
- Dual-boot
- Кастомизация ОС
- Шифрование диска

## Требования

- Флешка 8+ ГБ
- Целевой диск (полное стирание)
- Интернет не нужен

## Последствия

Плюсы: бабушка может установить сама, zero-config, offline.
Минусы: образ ~2.5 ГБ, только GPT/EFI.

## Связанные

- ADR-019: Installation Experience
- ADR-017: Platform Abstraction Layer
