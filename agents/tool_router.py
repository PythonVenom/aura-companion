"""
Машинка Tool: Маршрутизатор инструментов (AgentToolRouter)
LLM сама решает, какой агент вызвать, через tool calling.
"""

import json
import urllib.request
from agents.base import MicroAgent


class AgentToolRouter(MicroAgent):
    def __init__(self):
        super().__init__("tool_router", "Маршрутизатор инструментов")
        self.model = "qwen2.5:7b-instruct-q4_K_M"
        self.ollama_url = "http://localhost:11434/api/chat"

        # Реестр инструментов: имя → (описание, функция-исполнитель)
        self.tools = {}
        self.tool_defs = []

        # Системный промпт
        self.system_prompt = (
            "Ты — Аура, семейный ИИ-компаньон. У тебя есть инструменты (tools).\n\n"
            "ПРАВИЛА ВЫБОРА ИНСТРУМЕНТА:\n"
            "1. Если команда — просьба сделать действие (открой, закрой, включи, выключи, найди, покажи, какие, список) — вызови ПОДХОДЯЩИЙ инструмент.\n"
            "2. 'какие песни', 'какая музыка', 'список музыки' → list_music\n"
            "3. 'какие фильмы', 'список фильмов' → list_movies\n"
            "4. 'включи песню X', 'включи трек X' → play_music с query=X\n"
            "5. 'включи фильм X' → play_movie с query=X\n"
            "6. 'открой X' (где X — приложение) → open_app с name=X\n"
            "7. 'какие функции', 'что ты умеешь' → list_functions\n"
            "8. 'открой вк', 'открой вконтакте' → open_vk\n"
            "9. 'заблокируй экран' → lock_screen\n"
            "10. 'выключи пк' → power_off\n\n"
            "ЗАПРЕЩЕНО:\n"
            "- Вызывать инструмент, если команда НЕПОНЯТНА или ОБРЕЗАНА (например 'какие есть пе').\n"
            "- Вызывать list_functions, если пользователь НЕ просит 'функции' или 'что ты умеешь'.\n"
            "- Угадывать. Если не уверена — ответь текстом 'Не поняла команду'.\n\n"
            "Отвечай ВСЕГДА на русском. Будь краткой."
        )

        print("✅ ToolRouter загружен")

    def register(self, name, description, parameters, handler):
        """
        Зарегистрировать инструмент.
        name — имя (get_time, get_weather)
        description — что делает
        parameters — dict: {param_name: type}
        handler — функция-исполнитель
        """
        self.tools[name] = handler

        self.tool_defs.append({
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        p: {"type": t} for p, t in parameters.items()
                    },
                    "required": list(parameters.keys())
                }
            }
        })

    def route(self, user_text):
        """LLM решает, что делать"""
        if not self.tool_defs:
            return None

        try:
            data = json.dumps({
                "model": self.model,
                "messages": [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_text}
                ],
                "tools": self.tool_defs,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "num_predict": 150,
                }
            }).encode('utf-8')

            req = urllib.request.Request(
                self.ollama_url,
                data=data,
                headers={'Content-Type': 'application/json'}
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode('utf-8'))

            message = result.get('message', {})
            tool_calls = message.get('tool_calls', [])

            if not tool_calls:
                # LLM ответила текстом — но может быть "play_music {json}"
                content = message.get('content', '')
                
                # Пробуем распарсить: <tool_name> <json>
                import re
                match = re.match(r'^\s*(\w+)\s+(\{.*\})\s*$', content.strip(), re.DOTALL)
                if match:
                    tool_name = match.group(1)
                    try:
                        tool_args = json.loads(match.group(2))
                        # Проверяем, что инструмент существует
                        if tool_name in self.tools:
                            try:
                                result_text = self.tools[tool_name](**tool_args)
                            except Exception as e:
                                result_text = f"❌ Ошибка вызова {tool_name}: {e}"
                            return {
                                "type": "tool",
                                "tool": tool_name,
                                "args": tool_args,
                                "response": result_text
                            }
                    except json.JSONDecodeError:
                        pass
                
                # Не распарсилось — возвращаем как текст
                return {
                    "type": "text",
                    "response": content
                }

            # LLM вызвала инструмент
            call = tool_calls[0]
            func_name = call['function']['name']
            func_args = call['function'].get('arguments', {})

            if isinstance(func_args, str):
                try:
                    func_args = json.loads(func_args)
                except:
                    func_args = {}

            if func_name not in self.tools:
                return {
                    "type": "error",
                    "response": f"❌ Инструмент '{func_name}' не найден"
                }

            # Вызываем
            handler = self.tools[func_name]
            try:
                result_text = handler(**func_args)
            except Exception as e:
                result_text = f"❌ Ошибка вызова {func_name}: {e}"

            return {
                "type": "tool",
                "tool": func_name,
                "args": func_args,
                "response": result_text
            }

        except Exception as e:
            return {
                "type": "error",
                "response": f"❌ Ошибка ToolRouter: {e}"
            }

    def execute(self, command):
        result = self.route(command)
        if result:
            return result.get('response', '')
        return "🤖 ToolRouter: нет инструментов"
