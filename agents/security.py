"""
Машинка 70: Безопасность (AgentSecurity)
"""

import subprocess
from agents.base import MicroAgent


class AgentSecurity(MicroAgent):
    def __init__(self):
        super().__init__("security", "Безопасность Ауры")
        self.suspicious = ['nc', 'nmap', 'hydra', 'sqlmap', 'metasploit', 'john', 'aircrack']
        self.last_scan = None

    def scan_processes(self):
        try:
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            found = []
            for proc in result.stdout.split('\n'):
                for susp in self.suspicious:
                    if susp in proc.lower():
                        found.append(proc.strip())

            if found:
                report = "🚨 Обнаружены подозрительные процессы:\n"
                for p in found[:5]:
                    report += f"  - {p[:80]}\n"
                return report
            return "✅ Система чиста"
        except:
            return "❌ Ошибка сканирования"

    def check_ports(self):
        try:
            result = subprocess.run(['ss', '-tuln'], capture_output=True, text=True)
            ports = []
            for line in result.stdout.split('\n'):
                if 'LISTEN' in line:
                    parts = line.split()
                    if len(parts) > 4:
                        port = parts[4].split(':')[-1]
                        ports.append(port)
            if ports:
                return f"🔓 Открытые порты: {', '.join(ports[:10])}"
            return "🔒 Открытых портов нет"
        except:
            return "❌ Не удалось проверить порты"

    def execute(self, command):
        cmd = command.lower()
        if 'проверь' in cmd:
            if 'порт' in cmd:
                return self.check_ports()
            return self.scan_processes()
        return "🛡️ Безопасность готова"
