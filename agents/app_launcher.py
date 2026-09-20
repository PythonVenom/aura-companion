"""
Машинка App: Запуск приложений (AgentAppLauncher)
Ищет .desktop, запускает через gtk-launch, закрывает через pkill.
"""

import os
import subprocess
import glob
from agents.base import MicroAgent


class AgentAppLauncher(MicroAgent):
    def __init__(self):
        super().__init__("app_launcher", "Запуск приложений")
        self.app_dirs = [
            "/usr/share/applications",
            "/usr/local/share/applications",
            os.path.expanduser("~/.local/share/applications"),
            "/var/lib/flatpak/exports/share/applications",
            os.path.expanduser("~/.local/share/flatpak/exports/share/applications"),
        ]
        self.apps_cache = {}
        self._scan_apps()
        print(f"✅ AppLauncher: найдено {len(self.apps_cache)} приложений")

    def _scan_apps(self):
        """Сканировать .desktop файлы"""
        for d in self.app_dirs:
            if not os.path.exists(d):
                continue
            for f in glob.glob(f"{d}/*.desktop"):
                try:
                    name = None
                    exec_cmd = None
                    with open(f, 'r', encoding='utf-8', errors='ignore') as fh:
                        for line in fh:
                            if line.startswith("Name=") and not name:
                                name = line.split("=", 1)[1].strip()
                            elif line.startswith("Exec=") and not exec_cmd:
                                exec_cmd = line.split("=", 1)[1].strip()
                                # Убираем параметры %U, %F и т.п.
                                exec_cmd = exec_cmd.split("%")[0].strip()

                    if name and exec_cmd:
                        key = name.lower()
                        if key not in self.apps_cache:
                            self.apps_cache[key] = {
                                "name": name,
                                "exec": exec_cmd,
                                "file": f,
                            }
                except:
                    pass

    def find_app(self, query):
        """Найти приложение по имени"""
        query_lower = query.lower().strip()
        if not query_lower:
            return None

        # Точное совпадение
        if query_lower in self.apps_cache:
            return self.apps_cache[query_lower]

        # Частичное совпадение
        for name, info in self.apps_cache.items():
            if query_lower in name or name in query_lower:
                return info

        return None

    def open_app(self, name):
        """Открыть приложение"""
        app = self.find_app(name)
        if not app:
            return f"❌ Приложение '{name}' не найдено"

        try:
            # Используем gtk-launch или прямой exec
            cmd = app['exec'].split()
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return f"✅ Открыл: {app['name']}"
        except Exception as e:
            # Fallback — gtk-launch
            try:
                desktop_name = os.path.basename(app['file']).replace('.desktop', '')
                subprocess.Popen(['gtk-launch', desktop_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return f"✅ Открыл: {app['name']}"
            except:
                return f"❌ Не удалось открыть '{app['name']}': {e}"

    def close_app(self, name):
        """Закрыть приложение (case-insensitive, fuzzy)"""
        import difflib

        app = self.find_app(name)

        # Собираем кандидатов на убийство
        candidates = []

        if app:
            exec_first = app['exec'].split()[0]
            exec_basename = os.path.basename(exec_first)
            candidates.append(exec_basename)
            candidates.append(app['name'])

        # Fuzzy-поиск по всем приложениям
        all_names = list(self.apps_cache.keys())
        matches = difflib.get_close_matches(name.lower(), all_names, n=3, cutoff=0.5)
        for m in matches:
            candidates.append(self.apps_cache[m]['name'])
            exec_first = self.apps_cache[m]['exec'].split()[0]
            candidates.append(os.path.basename(exec_first))

        # Прямое имя
        candidates.append(name)
        # 1. Пробуем Flatpak (если приложение из Flatpak)
        try:
            flatpak_result = subprocess.run(
                ['flatpak', 'list', '--app', '--columns=application,name'],
                capture_output=True, text=True, timeout=5
            )
            name_lower = name.lower()
            for line in flatpak_result.stdout.split('\n'):
                if not line.strip():
                    continue
                parts = line.split('\t')
                if len(parts) >= 2:
                    app_id, app_name = parts[0], parts[1]
                    # Совпадение по имени или ID
                    if name_lower in app_name.lower() or name_lower in app_id.lower():
                        subprocess.run(['flatpak', 'kill', app_id], check=False)
                        return f"✅ Закрыл: {app_name}"
        except:
            pass

        # Исключения — общие имена, которые НЕ надо убивать
        BLACKLIST = ['flatpak', 'telegram-desktop', 'chrome', 'browser', 'java', 'python', 'sh', 'bash']

        # Пробуем убить (case-insensitive)
        killed = False
        for cand in candidates:
            if not cand:
                continue
            if cand.lower() in BLACKLIST:
                continue
            try:
                # pkill с -i (case-insensitive) и -x (точное совпадение)
                result = subprocess.run(['pkill', '-ix', cand], check=False, capture_output=True)
                if result.returncode == 0:
                    killed = True
                    return f"✅ Закрыл: {cand}"
                # Если -x не сработал — пробуем -if (по полной строке)
                result = subprocess.run(['pkill', '-if', cand], check=False, capture_output=True)
                if result.returncode == 0:
                    killed = True
                    return f"✅ Закрыл: {cand}"
            except:
                pass

        if not killed:
            return f"❌ Процесс '{name}' не найден"
        return f"✅ Закрыл: {name}"

    def list_apps(self, filter_text=""):
        """Список приложений"""
        filter_lower = filter_text.lower().strip()
        apps = []
        for name, info in self.apps_cache.items():
            if not filter_lower or filter_lower in name:
                apps.append(info['name'])

        apps.sort()

        if not apps:
            return f"❌ Не найдено приложений по '{filter_text}'"

        result = f"📱 Приложений: {len(apps)}\n\n"
        for i, name in enumerate(apps[:50], 1):
            result += f"{i}. {name}\n"

        if len(apps) > 50:
            result += f"\n... и ещё {len(apps) - 50}"

        return result

    def execute(self, command):
        cmd = command.lower().strip()

        if 'открой' in cmd or 'запусти' in cmd:
            name = cmd.replace('открой', '').replace('запусти', '').strip()
            if not name:
                return "Что открыть?"
            return self.open_app(name)

        if 'закрой' in cmd:
            name = cmd.replace('закрой', '').strip()
            if not name:
                return "Что закрыть?"
            return self.close_app(name)

        if 'список приложений' in cmd or 'какие приложения' in cmd:
            filter_text = cmd.replace('список приложений', '').replace('какие приложения', '').strip()
            return self.list_apps(filter_text)

        return "📱 AppLauncher готов. Команды: открой X, закрой X, список приложений"
