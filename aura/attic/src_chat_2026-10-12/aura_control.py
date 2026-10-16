"""Aura Control v2.0 — управление ПК с верификацией и lock-файлом."""
import asyncio
import atexit
import datetime
import os
import re
import subprocess
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.demon import Aura

try:
    from bleak import BleakClient, BleakScanner
    BLE_OK = True
except ImportError:
    BLE_OK = False

LIGHT_MAC = "D0:C4:1A:61:D5:11"
LIGHT_CHAR = "00002b11-0000-1000-8000-00805f9b34fb"
LIGHT_NOTIFY = "00002b10-0000-1000-8000-00805f9b34fb"
LOCK_FILE = "/tmp/aura_control.lock"


def _check_lock():
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE) as f:
                old_pid = int(f.read().strip())
            os.kill(old_pid, 0)
            print(f"!!! Aura уже запущена (PID {old_pid}). Убей сначала:")
            print(f"    kill -9 {old_pid} && rm -f {LOCK_FILE}")
            sys.exit(1)
        except (OSError, ValueError):
            pass
    with open(LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))
    atexit.register(lambda: os.path.exists(LOCK_FILE) and os.remove(LOCK_FILE))


class AuraControl:
    def __init__(self, aura):
        self.aura = aura
        self.model = "GE63"
        self.music_dir = os.path.expanduser("~/Music")
        self.video_url = "https://rutube.ru"
        self.state_dir = os.path.expanduser("~/.aura")
        os.makedirs(self.state_dir, exist_ok=True)
        self.state_file = os.path.join(self.state_dir, "state.json")

    def _load_state(self):
        import json
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file) as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_state(self, key, value):
        import json
        state = self._load_state()
        state[key] = value
        with open(self.state_file, "w") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

    def _get_state(self, key):
        return self._load_state().get(key)


    def run(self, cmd):
        return subprocess.run(cmd, shell=True, capture_output=True, text=True)

    # ============ МУЗЫКА ============
    def music_play(self):
        if not os.path.isdir(self.music_dir):
            os.makedirs(self.music_dir, exist_ok=True)
            return self.aura.say(f"Папка {self.music_dir} пустая.")
        self.run("pkill -x mpv"); time.sleep(0.3)
        # Убираем старый IPC
        self.run("rm -f /tmp/mpv-socket")
        # Запускаем с MPRIS (для playerctl) и IPC (для команд)
        self.run(f"mpv --no-video --shuffle --loop-playlist --really-quiet "
                 f"--input-ipc-server=/tmp/mpv-socket "
                 f"--script=/usr/share/mpv/scripts/mpris.so "
                 f"'{self.music_dir}' >/dev/null 2>&1 &")
        self._save_state("last_music_source", "local_mpv")
        return self.aura.say("Врубаю музыку.")
    def music_pause(self):
        self.run("playerctl --player=mpv pause"); return self.aura.say("Пауза.")
    def music_stop(self):
        self.run("pkill -x mpv"); return self.aura.say("Музыка остановлена.")
    def _mpv_cmd(self, command):
        """Отправляет команду в mpv через IPC."""
        import json
        payload = json.dumps({"command": command}) + "\n"
        self.run(f"echo '{payload}' | socat - /tmp/mpv-socket 2>/dev/null || "
                 f"echo '{payload}' | nc -U /tmp/mpv-socket 2>/dev/null")

    def music_next(self):
        self._mpv_cmd(["playlist-next"])
        return self.aura.say("Следующий.")

    def music_prev(self):
        self._mpv_cmd(["playlist-prev"])
        return self.aura.say("Предыдущий.")

    def music_pause(self):
        self._mpv_cmd(["cycle", "pause"])
        return self.aura.say("Пауза.")
    def music_prev(self):
        self.run("playerctl --player=mpv previous"); return self.aura.say("Предыдущий.")
    def volume_up(self):
        self.run("pactl set-sink-volume @DEFAULT_SINK@ +5%"); return self.aura.say("Громче.")
    def volume_down(self):
        self.run("pactl set-sink-volume @DEFAULT_SINK@ -5%"); return self.aura.say("Тише.")
    def volume_set(self, pct):
        self.run(f"pactl set-sink-volume @DEFAULT_SINK@ {pct}%")
        return self.aura.say(f"Громкость: {pct}%.")

    # ============ БРАУЗЕР ============
    def find_browser(self, keyword=None):
        """Ищет окно браузера. Если keyword — ищет по подстроке в title."""
        out = self.run("wmctrl -l").stdout
        browsers = []
        for line in out.splitlines():
            parts = line.split(None, 3)
            if len(parts) < 4: continue
            wid, desktop, host, title = parts
            tl = title.lower()
            if any(b in tl for b in ["firefox", "chrome", "chromium", "brave"]):
                browsers.append((wid, title))
        if not browsers:
            return None
        if keyword:
            kw = keyword.lower()
            for wid, title in browsers:
                if kw in title.lower():
                    return wid
        return browsers[0][0]

    def _activate(self, wid):
        """Активация окна + фокус в центр (для видео)."""
        self.run(f"wmctrl -i -a {wid}")
        time.sleep(0.5)
        self.run(f"xdotool windowraise {wid}")
        time.sleep(0.3)
        self.run(f"xdotool windowfocus {wid}")
        time.sleep(0.4)
        # Двигаем мышь в центр окна и кликаем — фокус на элементе видео
        r = self.run(f"xdotool getwindowgeometry --shell {wid}").stdout
        x = y = w = h = 0
        for line in r.splitlines():
            if line.startswith("X="): x = int(line.split("=")[1])
            if line.startswith("Y="): y = int(line.split("=")[1])
            if line.startswith("WIDTH="): w = int(line.split("=")[1])
            if line.startswith("HEIGHT="): h = int(line.split("=")[1])
        cx, cy = x + w // 2, y + h // 2 + 50  # чуть ниже центра (обычно там видео)
        self.run(f"xdotool mousemove {cx} {cy} click 1")
        time.sleep(0.5)

    def _active_wid(self):
        return self.run("xdotool getactivewindow").stdout.strip()

    def _is_fullscreen(self, wid):
        out = self.run(f"xprop -id {wid} _NET_WM_STATE").stdout
        return "_NET_WM_STATE_FULLSCREEN" in out

    def _browser_wid_by_keyword(self, keyword):
        """Ищет окно браузера с keyword. Fallback — любое окно Firefox."""
        wid = self.find_browser(keyword=keyword)
        if not wid:
            wid = self.find_browser()
        return wid

    # ============ ВИДЕО ============
    def video_open_url(self, url=None):
        """Открыть URL + запомнить окно как текущее видео."""
        url = url or self.video_url
        self.run("pkill -x mpv")
        self.run(f"nohup firefox --new-tab '{url}' >/dev/null 2>&1 &")
        time.sleep(5)
        # Ищем самое свежее окно браузера
        wid = self.find_browser()
        if wid:
            self._save_state("last_video_wid", wid)
            self._activate(wid)
        return self.aura.say(f"Открыла {url}. Запомнила окно.")

    def _get_video_wid(self):
        """Возвращает ID окна видео: из state или поиск."""
        wid = self._get_state("last_video_wid")
        # Проверяем, живое ли окно
        if wid:
            out = self.run(f"xprop -id {wid} WM_NAME 2>/dev/null").stdout
            if out and "no such" not in out.lower():
                return wid
        # Fallback — поиск по ключевым словам
        for kw in ["титан", "titan", "rutube", "youtube", "сериал", "фильм",
                   "мультик", "video", "видео", "watch", "player"]:
            wid = self.find_browser(keyword=kw)
            if wid:
                self._save_state("last_video_wid", wid)
                return wid
        return None

    def video_fullscreen(self):
        """Двойной клик по центру — toggle fullscreen."""
        wid = self._get_video_wid()
        if not wid:
            return self.aura.say("Не нашла окно с видео.")
        self._activate(wid)
        time.sleep(0.6)
        r = self.run(f"xdotool getwindowgeometry --shell {wid}").stdout
        x = y = w = h = 0
        for line in r.splitlines():
            if line.startswith("X="): x = int(line.split("=")[1])
            if line.startswith("Y="): y = int(line.split("=")[1])
            if line.startswith("WIDTH="): w = int(line.split("=")[1])
            if line.startswith("HEIGHT="): h = int(line.split("=")[1])
        cx, cy = x + w // 2, y + h // 2
        self.run(f"xdotool mousemove {cx} {cy}")
        time.sleep(0.3)
        self.run("xdotool click --repeat 2 --delay 120 1")
        time.sleep(0.5)
        return self.aura.say("Развернула.")

    def video_minimize(self):
        """Двойной клик — вернуться из fullscreen + свернуть окно."""
        wid = self._get_video_wid()
        if not wid:
            return self.aura.say("Не нашла окно с видео.")
        self._activate(wid)
        time.sleep(0.6)
        r = self.run(f"xdotool getwindowgeometry --shell {wid}").stdout
        x = y = w = h = 0
        for line in r.splitlines():
            if line.startswith("X="): x = int(line.split("=")[1])
            if line.startswith("Y="): y = int(line.split("=")[1])
            if line.startswith("WIDTH="): w = int(line.split("=")[1])
            if line.startswith("HEIGHT="): h = int(line.split("=")[1])
        cx, cy = x + w // 2, y + h // 2
        # Двойной клик — выйти из fullscreen
        self.run(f"xdotool mousemove {cx} {cy}")
        time.sleep(0.3)
        self.run("xdotool click --repeat 2 --delay 120 1")
        time.sleep(0.7)
        # Свернуть окно
        self.run(f"xdotool windowminimize {wid}")
        return self.aura.say("Свернула видео.")

    def video_play_pause(self):
        """Play/pause по state-окну."""
        wid = self._get_video_wid()
        if not wid:
            return self.aura.say("Не нашла окно с видео.")
        self._activate(wid)
        time.sleep(0.4)
        self.run("xdotool key --clearmodifiers space")
        return self.aura.say("Пауза/воспроизведение.")


    # ============ ВРЕМЯ / ПОГОДА ============
    def what_time(self):
        now = datetime.datetime.now()
        return self.aura.say(f"Сейчас {now.strftime('%H:%M, %d %B %Y')}.")
    def weather(self, city=None):
        """Если city=None — определяет по IP."""
        if city:
            url = f"https://wttr.in/{city}?format=3&lang=ru"
        else:
            url = "https://wttr.in/?format=3&lang=ru"
        r = self.run(f"curl -s --max-time 10 '{url}'")
        text = r.stdout.strip()
        if not text or "Unknown" in text:
            return self.aura.say("Не могу определить погоду.")
        return self.aura.say(text)

    # ============ ОКНА ============
    def focus_window(self, name):
        self.run(f"wmctrl -a '{name}'"); return self.aura.say(f"Фокус на {name}.")
    def list_windows(self): return self.run("wmctrl -l").stdout
    def close_window(self):
        self.run("wmctrl -c :ACTIVE:"); return self.aura.say("Закрываю.")
    def _translate_name(self, name):
        """Переводит русское имя в латинское (если есть)."""
        name_low = name.lower().strip()
        for ru, en in RU_TO_EN.items():
            if ru in name_low:
                return en
        return name_low

    def minimize_by_name(self, name):
        """Сворачивает окна по имени (с транслитерацией)."""
        eng_name = self._translate_name(name)
        r = self.run(f"wmctrl -l | grep -i '{eng_name}'").stdout
        if not r.strip():
            # Пробуем оригинальное имя
            r = self.run(f"wmctrl -l | grep -i '{name}'").stdout
        if not r.strip():
            return self.aura.say(f"Окно '{name}' не найдено.")
        count = 0
        for line in r.splitlines():
            wid = line.split()[0]
            self.run(f"xdotool windowminimize {wid}")
            count += 1
        return self.aura.say(f"Свернула {count} окон '{name}'.")

    def show_all_windows(self):
        """Умный обзор: группирует окна по типам."""
        r = self.run("wmctrl -l").stdout
        categories = {
            "🌐 Браузер": [],
            "💻 Терминал": [],
            "📝 Редактор/IDE": [],
            "💬 Чат": [],
            "🎵 Медиа": [],
            "📁 Файлы": [],
            "🔧 Разное": [],
        }

        # Правила классификации
        rules = [
            ("🌐 Браузер", ["firefox", "chrome", "chromium", "brave", "opera"]),
            ("💻 Терминал", ["terminal", "konsole", "alacritty", "kitty", "term", "zsh"]),
            ("📝 Редактор/IDE", ["code", "vim", "nano", "sublime", "atom", "pycharm"]),
            ("💬 Чат", ["telegram", "discord", "whatsapp", "signal", "slack"]),
            ("🎵 Медиа", ["mpv", "vlc", "spotify", "rhythmbox", "audacious"]),
            ("📁 Файлы", ["dolphin", "nautilus", "thunar", "files", "nemo"]),
        ]

        for line in r.splitlines():
            parts = line.split(None, 3)
            if len(parts) < 4:
                continue
            wid, desktop, host, title = parts

            # Мусор — пропускаем
            low = title.lower()
            if any(skip in low for skip in ["plasmashell", "рабочий стол", "spectacle", "несохран"]):
                continue

            # Классифицируем
            placed = False
            for cat, keywords in rules:
                if any(kw in low for kw in keywords):
                    # Чистим заголовок от "— Mozilla Firefox" в конце
                    clean = title.replace("— Mozilla Firefox", "").strip()
                    clean = clean.replace("Mozilla Firefox", "").strip(" -—")
                    # Обрезаем длинные названия
                    if len(clean) > 50:
                        clean = clean[:47] + "..."
                    categories[cat].append(clean)
                    placed = True
                    break
            if not placed:
                clean = title[:50]
                categories["🔧 Разное"].append(clean)

        # Формируем вывод
        lines = []
        total = 0
        for cat, items in categories.items():
            if items:
                # Убираем дубликаты
                uniq = list(dict.fromkeys(items))
                lines.append(f"{cat} ({len(uniq)}):")
                for item in uniq[:5]:
                    lines.append(f"  • {item}")
                total += len(uniq)

        if not lines:
            return self.aura.say("Окон не найдено.")
        return self.aura.say(f"Обзор — {total} окон:\n" + "\n".join(lines))

    def raise_window(self, name):
        """Поднимает окно по имени (с транслитерацией)."""
        eng_name = self._translate_name(name)
        r = self.run(f"wmctrl -l | grep -i '{eng_name}'").stdout
        if not r.strip():
            r = self.run(f"wmctrl -l | grep -i '{name}'").stdout
        if not r.strip():
            return self.aura.say(f"Окно '{name}' не найдено.")
        # Берём первое окно
        wid = r.splitlines()[0].split()[0]
        self.run(f"wmctrl -i -a {wid}")
        return self.aura.say(f"Подняла '{name}'.")

    def minimize_all(self):
        """Сворачивает все окна кроме активного терминала."""
        # Получаем ID активного окна (терминал с Aura)
        active = self.run("xdotool getactivewindow").stdout.strip()
        # Сворачиваем все, кроме активного
        r = self.run("wmctrl -l").stdout
        count = 0
        for line in r.splitlines():
            wid = line.split()[0]
            if wid != active and not wid.startswith("0x00600"):  # пропускаем plasmashell
                self.run(f"xdotool windowminimize {wid}")
                count += 1
        return self.aura.say(f"Свернула {count} окон.")

    def minimize(self):
        self.run("xdotool getactivewindow windowminimize")
        return self.aura.say("Свернул.")


    def switch_workspace(self, n):
        self.run(f"wmctrl -s {n}"); return self.aura.say(f"Рабочий стол {n}.")

    def screenshot(self):
        os.makedirs(os.path.expanduser("~/Pictures"), exist_ok=True)
        path = os.path.expanduser("~/Pictures/aura_shot.png")
        self.run(f"scrot {path}")
        return self.aura.say(f"Скриншот: {path}")

    # ============ ЯРКОСТЬ ============
    def brightness_up(self, step=10):
        self.run(f"brightnessctl set +{step}%"); return self.aura.say(f"Яркость +{step}%.")
    def brightness_down(self, step=10):
        self.run(f"brightnessctl set {step}%-"); return self.aura.say(f"Яркость -{step}%.")
    def brightness_set(self, pct):
        pct = max(1, min(100, int(pct)))
        self.run(f"brightnessctl set {pct}%"); return self.aura.say(f"Яркость: {pct}%.")

    # ============ КЛАВИАТУРА ============
    def kbd_preset(self, preset):
        r = self.run(f"msi-perkeyrgb --model {self.model} -p {preset}")
        if r.returncode != 0: return self.aura.say(f"Ошибка: {r.stderr.strip()[:80]}")
        return self.aura.say(f"Клава: {preset}.")
    def kbd_color(self, hex_color):
        hex_color = hex_color.lstrip("#")
        r = self.run(f"msi-perkeyrgb --model {self.model} -s {hex_color}")
        if r.returncode != 0: return self.aura.say(f"Ошибка: {r.stderr.strip()[:80]}")
        return self.aura.say(f"Клава: #{hex_color}.")
    def kbd_off(self):
        self.run(f"msi-perkeyrgb --model {self.model} -d"); return self.aura.say("Подсветка выкл.")

    # ============ BLE ============
    def _run_async(self, coro):
        import threading
        result, error = [None], [None]
        def runner():
            try: result[0] = asyncio.run(coro)
            except Exception as e: error[0] = e
        t = threading.Thread(target=runner, daemon=True); t.start(); t.join(timeout=15)
        if error[0]: raise error[0]
        return result[0]
    async def _ble_scan_async(self, timeout=5):
        if not BLE_OK: return None
        devs = await BleakScanner.discover(timeout=timeout)
        return [(d.address, d.name) for d in devs]
    def scan_ble(self):
        if not BLE_OK: return self.aura.say("bleak не установлен.")
        try:
            devs = self._run_async(self._ble_scan_async())
            if not devs: return self.aura.say("BLE не найдено.")
            lines = "\n".join(f"  {m}  {n}" for m, n in devs if n)
            return self.aura.say(f"BLE:\n{lines}")
        except Exception as e:
            return self.aura.say(f"Ошибка BLE: {e}")
    async def _ble_write_async(self, payload):
        async with BleakClient(LIGHT_MAC) as client:
            await client.write_gatt_char(LIGHT_CHAR, payload, response=False)

    def _tuya_packet(self, command, data=b''):
        """Tuya BLE пакет: 55 AA VER CMD LEN DATA CRC(4)"""
        header = bytes([0x55, 0xAA, 0x00, command, len(data)]) + data
        # CRC8 (Tuya использует crc8 с полином 0x07, init 0x00)
        crc8 = 0
        for b in header:
            crc8 ^= b
            for _ in range(8):
                crc8 = (crc8 << 1 ^ 7) & 255 if crc8 & 128 else crc8 << 1 & 255
        return header + bytes([crc8])

    def _tuya_dp(self, dp_id, value):
        """DP (Data Point) пакет: 55 AA VER CMD LEN DP_ID TYPE LEN VALUE CRC"""
        if isinstance(value, bool):
            data = bytes([dp_id, 0x01, 0x00, 0x01 if value else 0x00])
        elif isinstance(value, int) and value <= 255:
            data = bytes([dp_id, 0x02, 0x00, 0x00, value & 0xFF])
        else:
            data = bytes([dp_id, 0x02, 0x00, 0x00, value & 0xFF])
        header = bytes([0x55, 0xAA, 0x00, 0x06, len(data)]) + data
        crc8 = 0
        for b in header:
            crc8 ^= b
            for _ in range(8):
                crc8 = (crc8 << 1 ^ 7) & 255 if crc8 & 128 else crc8 << 1 & 255
        return header + bytes([crc8])

    def light_on(self):
        if not LIGHT_MAC: return self.aura.say("MAC лампы не указан.")
        try:
            # DP 1 = switch, value = True
            pkt = self._tuya_dp(1, True)
            self._run_async(self._ble_write_async(pkt))
            return self.aura.say("Лампа вкл.")
        except Exception as e:
            return self.aura.say(f"Ошибка: {e}")

    def light_off(self):
        if not LIGHT_MAC: return self.aura.say("MAC лампы не указан.")
        try:
            pkt = self._tuya_dp(1, False)
            self._run_async(self._ble_write_async(pkt))
            return self.aura.say("Лампа выкл.")
        except Exception as e:
            return self.aura.say(f"Ошибка: {e}")


PRESETS = ["aqua", "chakra", "default", "disco", "drain", "freeway", "rainbow-split", "roulette"]

RU_COLORS = {
    "красн": "ff0000", "оранж": "ff8000", "желт": "ffff00",
    "зелен": "00ff00", "голуб": "4080ff", "син": "0000ff",
    "фиолет": "8000ff", "розов": "ff00ff", "бирюз": "00ffff",
    "мятн": "00ff80", "бел": "ffffff", "черн": "000000",
}

# Транслитерация русских имён приложений
RU_TO_EN = {
    "фаерфокс": "firefox", "фаер": "firefox", "файрфокс": "firefox",
    "хром": "chrome", "хромиум": "chromium",
    "терминал": "terminal", "консоль": "terminal", "терм": "terminal",
    "телеграм": "telegram", "телега": "telegram",
    "дискорд": "discord", "стим": "steam",
    "код": "code", "вскод": "code", "студия": "code",
    "музыка": "mpv", "плеер": "mpv",
    "делайм": "deepseek", "дипсик": "deepseek",
}

PRESETS = ["aqua", "chakra", "default", "disco", "drain", "freeway", "rainbow-split", "roulette"]

# Русские названия цветов → HEX
RU_COLORS = {
    "красн": "ff0000", "оранж": "ff8000", "желт": "ffff00",
    "зелен": "00ff00", "голуб": "4080ff", "син": "0000ff",
    "фиолет": "8000ff", "розов": "ff00ff", "бирюз": "00ffff",
    "мятн": "00ff80", "бел": "ffffff", "черн": "000000",
}

PRESETS = ["aqua", "chakra", "default", "disco", "drain", "freeway", "rainbow-split", "roulette"]


def handle(aura, cmd):
    c = AuraControl(aura)
    cmd = cmd.strip().lower()

    # ВИДЕО / МУЛЬТИК / СЕРИАЛ (универсально)
    video_words = ["фильм", "видео", "рутуб", "rutube", "ютуб", "youtube",
                   "сериал", "мультик", "мультфильм", "титан", "titan"]
    if any(w in cmd for w in video_words):
        if "сверн" in cmd or "уменьш" in cmd: return c.video_minimize()
        if "разверн" in cmd or "весь экран" in cmd: return c.video_fullscreen()
        if "продолж" in cmd: return c.video_play_pause()
        if "пауза" in cmd or "стоп" in cmd: return c.video_play_pause()
        if "открой" in cmd or "включи" in cmd:
            url = "https://youtube.com" if ("youtube" in cmd or "ютуб" in cmd) else c.video_url
            return c.video_open_url(url)
        # если просто "разверни фильм" / "сверни сериал" — уже отработано выше
        return c.video_fullscreen()

    # МУЗЫКА
    if "музык" in cmd or "трек" in cmd:
        if "стоп" in cmd or "выкл" in cmd: return c.music_stop()
        if "пауза" in cmd: return c.music_pause()
        if "след" in cmd: return c.music_next()
        if "пред" in cmd: return c.music_prev()
        return c.music_play()
    if cmd == "пауза": return c.music_pause()
    if "след" in cmd: return c.music_next()
    if "пред" in cmd: return c.music_prev()

    # ЗВУК
    if "громче" in cmd: return c.volume_up()
    if "тише" in cmd: return c.volume_down()
    if "громкость" in cmd or "звук" in cmd:
        m = re.search(r"(\d+)", cmd)
        if m: return c.volume_set(int(m.group(1)))

    # ВРЕМЯ / ПОГОДА
    if "сколько времени" in cmd or "который час" in cmd: return c.what_time()
    if "погод" in cmd:
        m = re.search(r"в ([а-яa-z]+)", cmd)
        if m:
            return c.weather(m.group(1))
        return c.weather()  # авто по IP

    # ОКНА
    # ОБЗОР / СПИСОК ОКОН
    if "обзор" in cmd or "список окон" in cmd or "покажи окна" in cmd:
        return c.show_all_windows()

    # ПОДНЯТЬ / РАЗВЕРНУТЬ ОКНО
    if "подними" in cmd or "поднять" in cmd or "покажи" in cmd or "разверни" in cmd:
        m = re.search(r"(подними|поднять|покажи|разверни)\s+(.+)", cmd)
        if m:
            name = m.group(2).strip()
            if name not in ("все", "всё"):
                return c.raise_window(name)

    # СВЕРНУТЬ
    if "сверни все" in cmd or "сверни всё" in cmd:
        return c.minimize_all()
    if "сверни" in cmd:
        m = re.search(r"сверни\s+(.+)", cmd)
        if m:
            name = m.group(1).strip()
            if name not in ("окно", "все", "всё"):
                return c.minimize_by_name(name)
        return c.minimize()
    if "закрой" in cmd: return c.close_window()
    if "список окон" in cmd: return c.list_windows()
    if "фокус" in cmd:
        name = cmd.replace("фокус", "").replace("окн", "").strip()
        if name: return c.focus_window(name)
    if "скрин" in cmd: return c.screenshot()
    if "стол" in cmd:
        m = re.search(r"(\d)", cmd)
        if m: return c.switch_workspace(int(m.group(1)) - 1)

    # ЯРКОСТЬ
    if "ярче" in cmd: return c.brightness_up()
    if "темнее" in cmd: return c.brightness_down()
    if "яркость" in cmd and "ламп" not in cmd:
        m = re.search(r"(\d+)", cmd)
        if m: return c.brightness_set(int(m.group(1)))

    # КЛАВА (русские цвета + HEX + пресеты)
    if "подсветк" in cmd or "клава" in cmd or "клавиатур" in cmd:
        m = re.search(r"#?([0-9a-f]{6})", cmd)
        if m: return c.kbd_color(m.group(1))
        for ru, hex_color in RU_COLORS.items():
            if ru in cmd: return c.kbd_color(hex_color)
        for p in PRESETS:
            if p in cmd: return c.kbd_preset(p)
        if "выкл" in cmd or "off" in cmd: return c.kbd_off()
        return c.aura.say("Какой цвет? Красный, синий, зелёный, жёлтый, белый, фиолетовый...")

    # ЛАМПА
    if "ламп" in cmd or "свет" in cmd:
        if "скан" in cmd or "поиск" in cmd: return c.scan_ble()
        if "вкл" in cmd: return c.light_on()
        if "выкл" in cmd: return c.light_off()

    return aura.say("Не поняла. Скажи иначе.")


async def main():
    aura = Aura()
    print(f"=== {aura.name} Control v2.0 ===")
    print("ВИДЕО:  разверни фильм / сверни фильм / продолжи фильм")
    print("МУЗЫКА: музыка / пауза / следующий / стоп музыка")
    print("ЗВУК:   громче / тише / громкость 50")
    print("ВРЕМЯ:  сколько времени   |   ПОГОДА: погода / погода в Питере")
    print("ОКНА:   свернуть / закрыть / список окон / фокус <имя>")
    print("СТОЛЫ:  стол 1..9   |   ЭКРАН: ярче / темнее / яркость 50")
    print("КЛАВА:  подсветка disco / aqua / ff0000 / выкл")
    print("ЛАМПА:  лампа скан / лампа вкл / лампа выкл")
    print("СКРИН:  скриншот   |   ВЫХОД: Ctrl+C")
    print()
    try:
        while True:
            try:
                cmd = input("Ты: ").strip()
            except EOFError:
                break
            if cmd.lower() in ("exit", "quit", "выход"): break
            if not cmd: continue
            print(f"Аура: {handle(aura, cmd)}\n")
    except KeyboardInterrupt:
        print("\n=== Aura вышла. Пока, брат. ===")


if __name__ == "__main__":
    _check_lock()
    asyncio.run(main())
