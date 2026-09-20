"""
Машинка 51: Выживальщик (AgentSurvivor)
"""

import subprocess
from agents.base import MicroAgent


class AgentSurvivor(MicroAgent):
    def __init__(self):
        super().__init__("survivor", "Выживальщик")
        self.ready = True

    def execute(self, command):
        cmd = command.lower()
        if 'код' in cmd or 'среду' in cmd or 'среда' in cmd:
            if 'открой' in cmd or 'выдели' in cmd:
                subprocess.Popen(['code-oss'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return "Офлайн: среда разработки открыта."
            elif 'закрой' in cmd:
                subprocess.run(['pkill', '-f', 'code-oss'], check=False)
                return "Офлайн: среда разработки закрыта."
        elif 'терминал' in cmd:
            if 'открой' in cmd:
                subprocess.Popen(['gnome-terminal'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return "Офлайн: терминал открыт."
            elif 'закрой' in cmd:
                subprocess.run(['pkill', '-f', 'gnome-terminal'], check=False)
                return "Офлайн: терминал закрыт."
        if 'музык' in cmd or 'звук' in cmd:
            if 'громче' in cmd:
                subprocess.run(['pactl', 'set-sink-volume', '@DEFAULT_SINK@', '+10%'], check=False)
                return "Офлайн: громкость увеличена."
            elif 'тише' in cmd:
                subprocess.run(['pactl', 'set-sink-volume', '@DEFAULT_SINK@', '-10%'], check=False)
                return "Офлайн: громкость уменьшена."
        elif 'файл' in cmd or 'архив' in cmd:
            if 'открой' in cmd:
                subprocess.Popen(['nautilus'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return "Офлайн: файловый менеджер открыт."
        return "Офлайн: не поняла. Для действия скажи: открой код, терминал, звук, файл."
