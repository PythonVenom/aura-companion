"""
Машинка 48: Мозг (AgentBrain)
"""

import json
import urllib.request
from agents.base import MicroAgent


class AgentBrain(MicroAgent):
    def __init__(self):
        super().__init__("brain", "Мозг Ауры")
        self.model = "qwen2.5:7b-instruct-q4_K_M"
        self.context_history = []
        self.system_prompt = (
            "Ты — Аура, семейный ИИ-компаньон. "
            "Отвечай ВСЕГДА на русском языке. "
            "НИКОГДА не используй китайский, английский или другие языки. "
            "Будь дружелюбной, без подхалимства.\n\n"
            "ПРАВИЛА:\n"
            "1. Если просят рассказать историю, сказку, анекдот — расскажи развёрнуто (10-20 предложений).\n"
            "2. Если задают простой вопрос — ответь кратко (1-3 предложения).\n"
            "3. Если просят объяснить — объясни понятно, но без воды."
        )

    def ask(self, question):
        try:
            self.context_history.append({"role": "user", "content": question})
            if len(self.context_history) > 10:
                self.context_history = self.context_history[-10:]

            messages = [{"role": "system", "content": self.system_prompt}]
            messages.extend(self.context_history)

            data = json.dumps({
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 700,
                    "num_ctx": 4096
                }
            }).encode('utf-8')

            req = urllib.request.Request(
                'http://localhost:11434/api/chat',
                data=data,
                headers={'Content-Type': 'application/json'}
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode('utf-8'))
                response_text = result.get('message', {}).get('content', 'Я не поняла вопрос.')
                self.context_history.append({"role": "assistant", "content": response_text})
                return response_text
        except Exception as e:
            return f"❌ Ошибка: {e}"

    def get_latest_response(self):
        return None

    def execute(self, command):
        return self.ask(command)
