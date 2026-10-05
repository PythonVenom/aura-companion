# Aura Standard — устанавливаемый ISO

Установка Arch + KDE + Aura за 5 минут. 4 профиля.

## Сборка

    sudo pacman -S archiso
    cd aura-os-standard
    sudo ./build.sh

## Запись и запуск

    sudo dd if=out/aura-standard-*.iso of=/dev/sdX bs=4M status=progress

Загружаешься → `aura-installer` → выбор профиля → archinstall.

## Профили

| Профиль | Для кого | Особенности |
|---|---|---|
| **Elder** | Пожилые | Крупный UI, Aura из коробки, 3 кнопки |
| **Rolling** | Разработчики | Полный стек, ollama, git, deps |
| **Kid** | Дети | Ограничения, игры, Aura для детей |
| **Media** | Медиа | Kodi, автозапуск, пульт |
| **Custom** | Обычные | Стандартный archinstall |

## После установки

Первый запуск → `aura-first-run` → диалог знакомства.
Aura задаёт вопросы, сохраняет профиль, адаптируется.

## Наука

- archiso (Arch Wiki)
- archinstall JSON config (Arch Wiki)
- Progressive disclosure (Nielsen 1993)
- First-run wizard (Microsoft 2015)

## Roadmap

- v7.9: Live ISO ✅, PKGBUILD ✅, Standard (эта задача)
- v8.0: AuraOS (полный, с авто-installer)
