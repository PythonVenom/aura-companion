"""
Оркестратор Ауры.

Заменяет AuraCore.process() из монолита.
По науке:
- Один роутер (реестр агентов)
- Никаких if/elif
- Async/await
- Легко тестируется

Оркестратор НЕ знает про:
- T-one (слух)
- Piper (голос)
- Ollama (LLM)
- Конкретных агентов

Он знает только про:
- AgentRegistry
- AgentRequest / AgentResponse
"""

from __future__ import annotations

import asyncio

from aura.core.protocol import AgentRequest, AgentResponse, AgentStatus
from aura.core.registry import AgentRegistry
from aura.core.intent_parser import IntentParser


# CONSTITUTION_HOOK + MEMORY_HOOK_V4 — v4.0 orchestrator integration (ADR-122, 123, 124)
def _mem_read(text: str):
    """Recall из всех слоёв + context manager."""
    try:
        from aura.core.memory import recall
        return recall(text, n=8)
    except Exception:
        return []

def _mem_write(user_text: str, aura_text: str):
    """EXTRACTOR_RUNTIME (ADR-122): работа + эпизод + semantic + social."""
    try:
        from aura.core.context_manager import get_context_manager
        cm = get_context_manager()
        cm.push("user", user_text)
        cm.push("aura", aura_text)
    except Exception as e:
        # F-006: не глотать (раздел 17 промта)
        import logging
        logging.getLogger('aura.orchestrator').warning(
            'orchestrator error: %s', e)
    try:
        from aura.core.memory.episodic import get_episodic
        get_episodic().remember(user_text, aura_text)
    except Exception as e:
        # F-006: не глотать (раздел 17 промта)
        import logging
        logging.getLogger('aura.orchestrator').warning(
            'orchestrator error: %s', e)
    # EXTRACTOR_RUNTIME: semantic + social в фоне (thread)
    try:
        import threading
        def _bg():
            try:
                from aura.core.memory.extractor import apply_semantic, apply_social
                apply_semantic(user_text)
                apply_social(user_text)
            except Exception as e:
                # F-006: не глотать (раздел 17 промта)
                import logging
                logging.getLogger('aura.orchestrator').warning(
                    'orchestrator error: %s', e)
        threading.Thread(target=_bg, daemon=True).start()
    except Exception as e:
        # F-006: не глотать (раздел 17 промта)
        import logging
        logging.getLogger('aura.orchestrator').warning(
            'orchestrator error: %s', e)


class Orchestrator:
    """
    Оркестратор: принимает текст, возвращает ответ.

    Использование:
        orch = Orchestrator()
        orch.register(AgentTime())
        orch.register(AgentPower())

        response = await orch.process("который час")
    """

    def __init__(self, tool_router=None, brain=None, dispatcher=None, procedural=None, mcp_manager=None) -> None:
        self.registry = AgentRegistry()
        self.tool_router = tool_router
        self.brain = brain
        self.procedural = procedural
        self.mcp_manager = mcp_manager
        self.dispatcher = dispatcher
        self.route_tree = None
        if dispatcher is not None:
            try:
                from aura.core.route_tree import build_route_tree
                self.route_tree = build_route_tree()
            except Exception as e:
                print(f"⚠️ RouteTree init: {e}")
        self.intent_parser = IntentParser()
        self.fallback_text = "Не расслышала. Повтори, пожалуйста."  # AURA_CORE_FIX_V1
        self._last_response: AgentResponse | None = None

    def register(self, agent) -> None:
        """Зарегистрировать агента."""
        self.registry.register(agent)

    async def process(self, text: str) -> str:
        """
        Обработать текст.

        1. Найти агента через реестр
        2. Если найден — выполнить handle()
        3. Если не найден — fallback
        """

        if self.mcp_manager is not None:
            
            # Очищаем поисковый запрос от лишних слов
            clean_search = text.lower()
            for w in ["найди", "поищи", "в интернете", "пожалуйста", "сегодня", "мне", "последние", "новости", "про", "о", "об"]:
                clean_search = clean_search.replace(w, "")
            clean_search = " ".join(clean_search.split()).strip()

            if any(w in text.lower() for w in ["файл", "readme", "прочитай", "list", "find", "cat", "grep", "директор", "база", "sql", "таблиц", "users", "test.db", "database", "найди", "поищи", "новости", "курс", "погода", "кто такой", "что такое", "гугл", "интернет", "создай", "запиши", "сохрани", "сделай"]):
                print(f"🔍 [Search] Очищенный запрос: '{clean_search}'")
                import logging
                logging.getLogger("aura.orchestrator").debug(f"MCP Fallback attempt (tools loaded: {len(self.mcp_manager.tools)})")
                mcp_res = await self._try_mcp_fallback(text)
                if mcp_res:
                    _mem_write(text, mcp_res)
                    return mcp_res
        text = self._normalize(text)  # AURA_FUZZY_V1
        request = AgentRequest(text=text)

        # observability (ADR-112)
        try:
            from aura.observability import log, new_trace
            new_trace("process")
            log("input", text=text[:120])
        except Exception as e:
            # F-006: не глотать (раздел 17 промта)
            import logging
            logging.getLogger('aura.orchestrator').warning(
                'orchestrator error: %s', e)

        # Constitution (ADR-129) — резервная проверка (Tier0 уже проверил)
        try:
            from aura.core.constitution import check as _const_check
            allowed, refusal, rule_id = _const_check(text)
            if not allowed:
                try:
                    from aura.observability import log as _log
                    _log("constitution.refuse", rule=rule_id, text=text[:120])
                except Exception as e:
                    # F-006: не глотать (раздел 17 промта)
                    import logging
                    logging.getLogger('aura.orchestrator').warning(
                        'orchestrator error: %s', e)
                _mem_write(text, refusal)
                return refusal
        except Exception as e:
            # F-006: не глотать (раздел 17 промта)
            import logging
            logging.getLogger('aura.orchestrator').warning(
                'orchestrator error: %s', e)

        # ReAct ветка (ADR-123) — для многошаговых запросов
        try:
            from aura.core.react_loop import react_loop, should_use_react
            if should_use_react(text):
                r = await asyncio.to_thread(react_loop, text)
                answer = r.get("answer") or self.fallback_text
                _mem_write(text, answer)
                return answer
        except Exception as e:
            print(f"⚠️ ReAct: {e}")

        # Intent Parser (Декомпозиция)
        if self._is_complex_goal(text):
            plan = self.intent_parser.parse(text)
            if plan.get("steps"):
                results = []
                for step in plan["steps"]:
                    agent_id = step.get("agent")
                    step_text = step.get("text", text)
                    args = step.get("args", {})
                    # Ищем агента по id
                    a = next((ag for ag in self.registry._agents if ag.name == agent_id), None)
                    if a:
                        try:
                            req = AgentRequest(text=step_text, args=args)
                            resp = await a.handle(req)
                            if resp and resp.text:
                                results.append(f"[{agent_id}] {resp.text}")
                        except Exception as e:
                            results.append(f"[{agent_id}] Ошибка: {e}")
                if results:
                    final_text = "\n".join(results)
                    _mem_write(text, final_text)
                    return final_text


        if self._is_complex_goal(text):
            if self.procedural is not None:
                proc = self.procedural.recall(text)
                if proc is not None:
                    replay = await self._replay_procedure(proc, text)
                    if replay is not None:
                        _mem_write(text, replay)
                        return replay



        agent = self.registry.find(request)


        if agent is None:
            # 2. TIER0_FASTPATH (ADR-152): 90% простых команд — мгновенно
            #    (только если ни один агент не взял И dispatcher есть)
            if self.dispatcher is None:
                return self.fallback_text
            try:
                from aura.core.tier0_orchestrator import get_tier0
                t0 = get_tier0().process(text)
                if t0.source in ("dispatcher", "template"):
                    try:
                        from aura.observability import log as _log
                        _log("tier0.hit", source=t0.source, intent=t0.intent)
                    except Exception as e:
                        # F-006: не глотать (раздел 17 промта)
                        import logging
                        logging.getLogger('aura.orchestrator').warning(
                            'orchestrator error: %s', e)
                    _mem_write(text, t0.response)
                    return t0.response
            except Exception as e:
                print(f"⚠️ Tier0: {e}")

            # 3. RouteTree → dispatcher (быстрый regex-роутинг)
            if self.route_tree is not None and self.dispatcher is not None:
                try:
                    routed = self.route_tree.handle(text, {})
                    if routed and isinstance(routed, dict):
                        route = routed.get("route", "")
                        action = routed.get("action", "")
                        args = routed.get("args", {}) or {}
                        if route and route != "ask" and action:
                            cap = f"{route}.{action}"
                            ok, result = self.dispatcher.dispatch(cap, args)
                            if ok:
                                _mem_write(text, str(result))
                                return result
                except Exception as e:
                    print(f"⚠️ RouteTree: {e}")
            # 3. ToolRouter
            if self.tool_router is not None:
                try:
                    result = await asyncio.to_thread(self.tool_router.route, text)
                    if result:
                        t = result.get("type")
                        rtext = result.get("response", "")
                        if t in ("tool", "text") and rtext and len(rtext) > 2:
                            return rtext
                except Exception as e:
                    print(f"⚠️ ToolRouter: {e}")

            # MCP Fallback (до Brain)
            if self.mcp_manager is not None and self.brain is not None:
                mcp_result = await self._try_mcp_fallback(text)
                if mcp_result:
                    _mem_write(text, mcp_result)
                    return mcp_result

            # 3. GUARD (AURA_CORE_FIX_V1): не отдавать в LLM факт-запросы без агента
            if self._is_factual_intent(text):
                return "Пока не умею это. Скажи иначе или попроси другое."
            # 3. Brain
            if self.brain is not None:
                try:
                    result = await asyncio.to_thread(self.brain.ask, text)
                    if result and not result.startswith("❌"):
                        return result
                except Exception as e:
                    print(f"⚠️ Brain: {e}")
            return self.fallback_text

        try:
            response = await agent.handle(request)
        except Exception as e:
            return f"❌ Ошибка агента {agent.name}: {e}"

        if response.status == AgentStatus.OK:
            # AURA_STRIP_VOCATIVE_V1 — убрать 'Капитан'
            if response.text:
                import re as _re
                response.text = _re.sub(
                    r',\s*Капитан\b', '', response.text).strip()
                response.text = _re.sub(
                    r'\bКапитан,?\s*', '', response.text).strip()

            self._last_response = response
            _mem_write(text, response.text)
            return response.text

        if response.status == AgentStatus.NOT_HANDLED:
            # AURA_NOT_HANDLED_TO_BRAIN_V1: агент не взял → отдаём brain
            if self.brain is not None:
                try:
                    result = await asyncio.to_thread(self.brain.ask, text)
                    if result and not result.startswith("❌"):
                        self._last_response = response
                        _mem_write(text, result)
                        return result
                except Exception as e:
                    print(f"⚠️ Brain fallback: {e}")
            return self.fallback_text

        if response.status == AgentStatus.ERROR:
            return f"❌ {response.error or 'Ошибка'}"

        return self.fallback_text



    def _enrich_with_context(self, text: str) -> str:
        """Добавляет инфу об активном окне в запрос к LLM."""
        try:
            from aura.core.context_capture import format_context_for_prompt
            ctx = format_context_for_prompt()
            if ctx and len(ctx) > 5:
                return f"{ctx}\n\nЗапрос: {text}"
        except Exception as e:
            pass
        return text

    def _is_complex_goal(self, text: str) -> bool:
        """Эвристика: сложная цель требующая декомпозиции."""
        t = text.lower()
        triggers = ["чтобы", "подготовь", "сделай", "хочу", "уборк", "встреч"]
        return len(t.split()) > 3 and any(x in t for x in triggers)


    def _is_complex_goal(self, text: str) -> bool:
        t = text.lower()
        triggers = ["чтобы", "подготовь", "сделай", "хочу", "уборк", "встреч"]
        return len(t.split()) > 3 and any(x in t for x in triggers)

    async def _replay_procedure(self, proc, new_goal: str) -> str | None:
        from aura.core.procedural_memory import goal_hash
        from aura.contracts.agent import AgentRequest, AgentStatus

        if proc.goal_hash == goal_hash(new_goal):
            steps = proc.steps
        else:
            steps = await self._adapt_steps(proc.steps, new_goal)
            if steps is None:
                self.procedural.mark_failed(proc)
                return None

        results = []
        for step in steps:
            agent_name = step.get("agent", "")
            step_text = step.get("text") or step.get("step_text") or ""
            agent = next((a for a in self.registry._agents if a.name == agent_name), None)
            if agent is None:
                self.procedural.mark_failed(proc)
                return None
            try:
                resp = await agent.handle(AgentRequest(text=step_text))
            except Exception:
                self.procedural.mark_failed(proc)
                return None
            if resp.status != AgentStatus.OK:
                self.procedural.mark_failed(proc)
                return None
            if resp.text: results.append(resp.text)

        return " · ".join(results) if results else None

    async def _adapt_steps(self, template_steps: list[dict], new_goal: str) -> list[dict] | None:
        import asyncio, json, urllib.request, re
        prompt = f"Ты адаптируешь план. Дан шаблон шагов и новая цель.\nШаблон: {json.dumps(template_steps, ensure_ascii=False)}\nНовая цель: {new_goal}\nВерни JSON-массив той же длины. Поля agent не меняй. Поле text перепиши под новую цель. Только JSON."
        def _call():
            req = urllib.request.Request("http://localhost:11434/api/generate", data=json.dumps({"model": "qwen2.5:3b-instruct-q3_K_M", "prompt": prompt, "stream": False, "format": "json", "options": {"temperature": 0.0}}).encode("utf-8"), headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=10) as r: return json.loads(r.read().decode("utf-8"))
        try:
            resp = await asyncio.to_thread(_call)
            parsed = json.loads(resp.get("response", "[]"))
            if isinstance(parsed, list) and len(parsed) == len(template_steps): return parsed
        except Exception: pass
        return None

    async def _try_mcp_fallback(self, text: str) -> str | None:
        """MCP Chaining: Многошаговое выполнение через ReAct-цикл."""
        import asyncio, json, urllib.request, re, os
        
        cwd = os.getcwd()
        
        tools_list = []
        for name, data in self.mcp_manager.tools.items():
            schema = data["schema"]
            desc = schema.get("description", "No description")
            props = schema.get("inputSchema", {}).get("properties", {})
            args_desc = ", ".join(props.keys()) if props else "none"
            tools_list.append(f"- {name}: {desc} (args: {args_desc})")
        
        if not tools_list:
            return None
            
        tools_str = "\n".join(tools_list)
        
        history = []
        max_steps = 3
        called_tools = set()
        
        for step in range(max_steps):
            context_str = ""
            for i, h in enumerate(history):
                context_str += f"Step {i+1} Tool: {h['tool']}\nResult: {h['result']}\n\n"
            if not context_str:
                context_str = "No steps taken yet."

            prompt = (
                "You are an AI agent executing a multi-step plan. You have access to tools.\n"
                f"Available tools:\n{tools_str}\n\n"
                f"Current working directory: {cwd}\n"
                f"User request: {text}\n\n"
                f"History of previous steps:\n{context_str}\n"
                "RULES:\n"
                "1. If you need to perform an action, return JSON: {\"tool\": \"tool_name\", \"args\": {...}}\n"
                "2. If the task is fully completed, or if a tool failed and you cannot fix it, return: {\"tool\": \"done\"}\n"
                "3. DO NOT repeat the same tool call twice. If you see an error in history, use a different tool or return done.\n"
                f"4. If you write a file, use absolute path like '{cwd}/filename.txt'.\n"
                "5. Do NOT wrap JSON in markdown. Return ONLY valid JSON.\n"
                "--- EXAMPLES ---\n"
                "User: Read README.md\n"
                f"Assistant: {{\"tool\": \"read_file\", \"args\": {{\"path\": \"{cwd}/README.md\"}}}}\n"
                "User: Save data to file\n"
                f"Assistant: {{\"tool\": \"write_file\", \"args\": {{\"path\": \"{cwd}/output.txt\", \"content\": \"Data\"}}}}\n"
                "------------------\n"
                "Assistant: "
            )
            
            def _call_llm(p=prompt):
                req = urllib.request.Request(
                    "http://localhost:11434/api/generate",
                    data=json.dumps({
                        "model": "qwen2.5:7b-instruct-q4_K_M",
                        "prompt": p,
                        "stream": False,
                        "format": "json",
                        "options": {"temperature": 0.0}
                    }).encode("utf-8"),
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=30) as r:
                    return json.loads(r.read().decode("utf-8"))
                    
            try:
                resp = await asyncio.to_thread(_call_llm)
                raw_str = resp.get("response", "{}").strip()
                
                if raw_str.startswith("```json"): raw_str = raw_str[7:]
                if raw_str.endswith("```"): raw_str = raw_str[:-3]
                raw_str = raw_str.strip()
                
                raw = json.loads(raw_str)
                tool_name = raw.get("tool")
                
                if tool_name == "done" or tool_name == "none":
                    print(f"🔌 [MCP Chain] Завершено за {step} шагов.")
                    break
                
                if tool_name in called_tools:
                    print(f"🔌 [MCP Chain] Детект зацикливания на {tool_name}. Остановка.")
                    break
                    
                if tool_name and tool_name in self.mcp_manager.tools:
                    called_tools.add(tool_name)
                    args = raw.get("args", {})
                    
                    if tool_name == "search_news":
                        q = args.get("query", text)
                        args = {"query": q}
                    
                    if "path" in args:
                        path_val = str(args["path"])
                        if "/path/to/" in path_val:
                            filename = os.path.basename(path_val)
                            args["path"] = os.path.join(cwd, filename)
                        elif not path_val.startswith("/"):
                            args["path"] = os.path.join(cwd, path_val)

                    print(f"🔌 [MCP Chain] Шаг {step+1}: Вызов {tool_name} с {args}")
                    result = await self.mcp_manager.call(tool_name, args)
                    raw_result = json.dumps(result, ensure_ascii=False)
                    
                    clean_text = raw_result
                    try:
                        parsed = json.loads(raw_result)
                        if isinstance(parsed, dict) and "content" in parsed:
                            texts = [c.get("text", "") for c in parsed["content"] if c.get("type") == "text"]
                            clean_text = "\n".join(texts)
                    except Exception:
                        pass
                        
                    history.append({"tool": tool_name, "result": clean_text[:1000]})
                    
                else:
                    print(f"🔌 [MCP Chain] Неизвестный инструмент: {tool_name}")
                    break
                    
            except Exception as e:
                print(f"⚠️ MCP Chain error: {type(e).__name__}: {e}")
                break

        if history:
            final_prompt = (
                f"Пользователь спросил: '{text}'.\n"
                f"Вот лог выполненных действий:\n" + "\n".join([f"Шаг {i+1} ({h['tool']}): {h['result']}" for i, h in enumerate(history)]) + "\n\n"
                f"Сформулируй краткий итоговый ответ для пользователя на русском языке. Ответь, что было сделано и какой результат."
            )
            try:
                def _call_fmt():
                    req = urllib.request.Request(
                        "http://localhost:11434/api/generate",
                        data=json.dumps({"model": "qwen2.5:7b-instruct-q4_K_M", "prompt": final_prompt, "stream": False, "options": {"temperature": 0.3}}).encode("utf-8"),
                        headers={"Content-Type": "application/json"}
                    )
                    with urllib.request.urlopen(req, timeout=30) as r:
                        return json.loads(r.read().decode("utf-8")).get("response", "").strip()
                return await asyncio.to_thread(_call_fmt)
            except Exception:
                pass
                
        return None


    def _is_factual_intent(self, text: str) -> bool:
        """True = факт-запрос, LLM не должен отвечать. AURA_CORE_FIX_V1."""
        t = text.lower()
        return any(p in t for p in self.FACTUAL_PREFIXES)

    # AURA_FUZZY_V1 — нормализация fuzzy-ошибок ASR
    _FUZZY_MAP = {
        "скольо": "сколько", "скольковреме": "сколько времени",
        "скольковремя": "сколько времени", "скок": "сколько",
        "време": "времени", "время": "времени",
        "коь": "который", "который час": "который час",
        "деньнед": "день недели", "деньнеделю": "день недели",
        "число": "какое число", "погод": "погода",
        "музы": "музыку", "муз": "музыку", "включи музы": "включи музыку",
        # "какая": "какая погода",  # FIX: ломало "какая гарнитура"
    }

    def _normalize(self, text: str) -> str:
        """Нормализация fuzzy-ошибок ASR. AURA_FUZZY_V1."""
        if not text:
            return text
        t = text.lower().strip()
        words = t.split()
        out = []
        for w in words:
            # точное совпадение
            if w in self._FUZZY_MAP:
                out.append(self._FUZZY_MAP[w])
                continue
            # AURA_FUZZY_V2: не фаззить короткие слова (<=4 букв)
            # иначе "как" → "какой" (0.857 similarity, ложный матч).
            if len(w) <= 4:
                out.append(w)
                continue
            # fuzzy по ключам — cutoff выше для надёжности
            try:
                from difflib import get_close_matches
                m = get_close_matches(w, self._FUZZY_MAP.keys(), n=1, cutoff=0.85)
                if m:
                    out.append(self._FUZZY_MAP[m[0]])
                    continue
            except Exception as e:
                # F-006: не глотать (раздел 17 промта)
                import logging
                logging.getLogger('aura.orchestrator').warning(
                    'orchestrator error: %s', e)
            out.append(w)
        return " ".join(out)

    # AURA_GARBAGE_FILTER_V1 — не пускать мусор в LLM
    @staticmethod
    def _is_garbage(text: str) -> bool:
        """True = мусор (коротко / без гласных / странные символы)."""
        t = (text or "").strip().lower()
        if len(t) < 3:
            return True
        # нет русских или латинских гласных
        vowels = set("аеёиоуыэюяaeiou")
        if not any(c in vowels for c in t):
            return True
        # >40% небуквенных символов
        letters = sum(1 for c in t if c.isalpha())
        return letters / max(len(t), 1) < 0.5

    @staticmethod
    def _non_russian(text: str) -> bool:
        """True = в ответе есть CJK/арабица/др. — это не русский."""
        if not text:
            return False
        for c in text:
            o = ord(c)
            # CJK (китайский/японский/корейский)
            if 0x4E00 <= o <= 0x9FFF or 0x3040 <= o <= 0x30FF or 0xAC00 <= o <= 0xD7AF:
                return True
            # арабский
            if 0x0600 <= o <= 0x06FF:
                return True
        return False

    def last_silent(self) -> bool:
        """True = последний ответ был silent (ADR-048)."""
        return bool(self._last_response and self._last_response.silent)

    async def process_request(self, request: AgentRequest) -> AgentResponse:
        """Обработать AgentRequest напрямую (для тестов).

        Capability-check (Saltzer & Schroeder 1975, least privilege):
        перед вызовом агента проверяем, разрешена ли операция
        для текущего capability-профиля.

        Fail-open для unmapped агентов (раздел 20 промта: backward compat).
        TODO: через 2-3 итерации → fail-closed.
        """
        # Intent Parser (Декомпозиция)
        if self._is_complex_goal(text):
            plan = self.intent_parser.parse(text)
            if plan.get("steps"):
                results = []
                for step in plan["steps"]:
                    agent_id = step.get("agent")
                    step_text = step.get("text", text)
                    args = step.get("args", {})
                    # Ищем агента по id
                    a = next((ag for ag in self.registry._agents if ag.name == agent_id), None)
                    if a:
                        try:
                            req = AgentRequest(text=step_text, args=args)
                            resp = await a.handle(req)
                            if resp and resp.text:
                                results.append(f"[{agent_id}] {resp.text}")
                        except Exception as e:
                            results.append(f"[{agent_id}] Ошибка: {e}")
                if results:
                    final_text = "\n".join(results)
                    _mem_write(text, final_text)
                    return final_text


        if self._is_complex_goal(text):
            if self.procedural is not None:
                proc = self.procedural.recall(text)
                if proc is not None:
                    replay = await self._replay_procedure(proc, text)
                    if replay is not None:
                        _mem_write(text, replay)
                        return replay



        agent = self.registry.find(request)


        if agent is None:
            return AgentResponse.not_handled()

        # Capability-check
        try:
            from aura.core.capabilities import (
                AGENT_CAPABILITIES,
                current,
                require,
            )
            agent_name = getattr(agent, "name", None)
            if agent_name:
                cap = AGENT_CAPABILITIES.get(agent_name)
                if cap and not require(cap):
                    prof_name = current().name if current() else "none"  # type: ignore[union-attr]
                    import logging
                    logging.getLogger("aura.orchestrator").warning(
                        "Capability denied: agent=%s cap=%s profile=%s",
                        agent_name, cap, prof_name,
                    )
                    return AgentResponse.denied(
                        f"Профиль {prof_name!r} не имеет доступа к {agent_name!r}"
                    )
        except ImportError:
            pass  # capabilities не установлен — fail-open

        return await agent.handle(request)

    def __len__(self) -> int:
        return len(self.registry)


__all__ = ["Orchestrator"]
