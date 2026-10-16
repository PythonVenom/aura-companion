"""Intent Router — Fast Path для Aura. Без LLM."""
import re

from aura_control import PRESETS, RU_COLORS, AuraControl


class IntentRouter:
    def __init__(self, aura):
        self.aura = aura
        self.c = AuraControl(aura)
        self.rules = self._build()

    def _build(self):
        c = self.c
        R = []
        R.append((re.compile(r"фильм|видео|рутуб|rutube|ютуб|youtube|сериал|мультик|мультфильм|титан|titan"), self.video))
        R.append((re.compile(r"музык|трек"), self.music))
        R.append((re.compile(r"^пауза$"), lambda m: c.music_pause()))
        R.append((re.compile(r"след"), lambda m: c.music_next()))
        R.append((re.compile(r"пред"), lambda m: c.music_prev()))
        R.append((re.compile(r"громче"), lambda m: c.volume_up()))
        R.append((re.compile(r"тише"), lambda m: c.volume_down()))
        R.append((re.compile(r"громкость|звук"), self.volume))
        R.append((re.compile(r"сколько времени|который час"), lambda m: c.what_time()))
        R.append((re.compile(r"погод"), self.weather))
        R.append((re.compile(r"обзор|список окон|покажи окна"), lambda m: c.show_all_windows()))
        R.append((re.compile(r"подними|поднять|покажи|разверни"), self.raise_win))
        R.append((re.compile(r"сверни все|сверни всё"), lambda m: c.minimize_all()))
        R.append((re.compile(r"сверни"), self.minimize))
        R.append((re.compile(r"закрой"), lambda m: c.close_window()))
        R.append((re.compile(r"фокус"), self.focus))
        R.append((re.compile(r"скрин"), lambda m: c.screenshot()))
        R.append((re.compile(r"стол"), self.workspace))
        R.append((re.compile(r"ярче"), lambda m: c.brightness_up()))
        R.append((re.compile(r"темнее"), lambda m: c.brightness_down()))
        R.append((re.compile(r"яркость"), self.brightness))
        R.append((re.compile(r"подсветк|клава|клавиатур"), self.kbd))
        R.append((re.compile(r"ламп|свет"), self.light))
        return R

    def route(self, cmd):
        cmd = cmd.strip().lower()
        for pattern, handler in self.rules:
            m = pattern.search(cmd)
            if m:
                result = handler(m)
                if result is not None:
                    return result
        return None

    def video(self, m):
        c, cmd = self.c, m.string
        if "сверн" in cmd or "уменьш" in cmd: return c.video_minimize()
        if "разверн" in cmd or "весь экран" in cmd: return c.video_fullscreen()
        if "продолж" in cmd or "пауза" in cmd or "стоп" in cmd: return c.video_play_pause()
        if "открой" in cmd or "включи" in cmd:
            url = "https://youtube.com" if ("youtube" in cmd or "ютуб" in cmd) else c.video_url
            return c.video_open_url(url)
        return c.video_fullscreen()

    def music(self, m):
        c, cmd = self.c, m.string
        if "стоп" in cmd or "выкл" in cmd: return c.music_stop()
        if "пауза" in cmd: return c.music_pause()
        if "след" in cmd: return c.music_next()
        if "пред" in cmd: return c.music_prev()
        return c.music_play()

    def volume(self, m):
        r = re.search(r"(\d+)", m.string)
        if r: return self.c.volume_set(int(r.group(1)))
        return None

    def weather(self, m):
        r = re.search(r"в ([а-яa-z]+)", m.string)
        if r: return self.c.weather(r.group(1))
        return self.c.weather()

    def raise_win(self, m):
        r = re.search(r"(подними|поднять|покажи|разверни)\s+(.+)", m.string)
        if r:
            name = r.group(2).strip()
            if name not in ("все", "всё"):
                return self.c.raise_window(name)
        return None

    def minimize(self, m):
        r = re.search(r"сверни\s+(.+)", m.string)
        if r:
            name = r.group(1).strip()
            if name not in ("окно", "все", "всё"):
                return self.c.minimize_by_name(name)
        return self.c.minimize()

    def focus(self, m):
        name = m.string.replace("фокус", "").replace("окн", "").strip()
        if name: return self.c.focus_window(name)
        return None

    def workspace(self, m):
        r = re.search(r"(\d)", m.string)
        if r: return self.c.switch_workspace(int(r.group(1)) - 1)
        return None

    def brightness(self, m):
        if "ламп" in m.string: return None
        r = re.search(r"(\d+)", m.string)
        if r: return self.c.brightness_set(int(r.group(1)))
        return None

    def kbd(self, m):
        c, cmd = self.c, m.string
        r = re.search(r"#?([0-9a-f]{6})", cmd)
        if r: return c.kbd_color(r.group(1))
        for ru, hex_color in RU_COLORS.items():
            if ru in cmd: return c.kbd_color(hex_color)
        for p in PRESETS:
            if p in cmd: return c.kbd_preset(p)
        if "выкл" in cmd or "off" in cmd: return c.kbd_off()
        return self.aura.say("Какой цвет? Красный, синий, зелёный, жёлтый, белый, фиолетовый...")

    def light(self, m):
        c, cmd = self.c, m.string
        if "скан" in cmd or "поиск" in cmd: return c.scan_ble()
        if "вкл" in cmd: return c.light_on()
        if "выкл" in cmd: return c.light_off()
        return None
