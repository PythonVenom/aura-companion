# Установка Aura — для бати

> **Кому:** Иван Алексеевич (батя)
> **Ноут:** HP Laptop 15-dw1035ur (Pentium 6405U, 8 GB RAM, Intel UHD 620)
> **ОС:** Linux Mint 22.3 Cinnamon
> **Время:** 10-15 минут

---

## Что нужно

- Linux Mint 21/22 или Ubuntu 22.04+
- Интернет
- 3 GB места
- 10-15 минут

---

## Установка

Открой терминал (`Ctrl+Alt+T`). Введи **две команды**:

~~~bash
curl -fsSL https://raw.githubusercontent.com/PythonVenom/aura-companion/master/install_universal.sh -o /tmp/aura.sh
bash /tmp/aura.sh
~~~

Скрипт спросит пароль **один раз** (для установки пакетов).
Дальше всё автоматически — 10-15 минут.

---

## После установки

~~~bash
systemctl --user start aura.service
~~~

Скажи голосом: **«Аура, который час»**.

Или открой браузер: **http://127.0.0.1:8080/ui**

---

## Проверка

~~~bash
systemctl --user status aura.service
~~~

Должно быть `Active: active (running)`.

---

## Если Aura залипла

~~~bash
python3 ~/aura-companion/scripts/aura_ctl.py kill
systemctl --user restart aura.service
~~~

---

## Логи

~~~bash
journalctl --user -u aura.service -f
~~~

(выход — `Ctrl+C`)

---

## Что НЕ делать

- ❌ Не удалять `~/aura-companion/`
- ❌ Не запускать `sudo` без причины
- ❌ Не менять `~/.config/aura/` вручную
- ❌ Не запускать два экземпляра Aura

---

## Если что-то сломалось

**Aura не отвечает:**
~~~bash
systemctl --user restart aura.service
~~~

**Нет звука:**
~~~bash
pactl set-default-sink @DEFAULT_SINK@
~~~

**Микрофон не слышит:**
~~~bash
pactl list sources short
~~~

**Полная переустановка:**
~~~bash
rm -rf ~/aura-companion/venv
cd ~/aura-companion
python3 -m venv venv
source venv/bin/activate
pip install -e .
~~~

---

## Профиль elder-care

У бати автоматически включится **профиль elder** (по железу):
- LLM: **выключен** (Pentium 6405U слабый)
- Агентов: **53** (только elder-care)
- Голос: **Ирина** (Piper)
- Слух: **T-one** (streaming)

**Что работает:**
- Таблетки, падение, SOS
- Звонки, SMS
- Погода, время, напоминания
- Дневник настроения
- Воспоминания

**Что НЕ работает (без LLM):**
- Свободный диалог
- «Расскажи про космос»

---

## Связь

Если что-то не так — позвони сыну.

🛸
