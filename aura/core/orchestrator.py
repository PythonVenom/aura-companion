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

    def __init__(self, tool_router=None, brain=None, dispatcher=None) -> None:
        self.registry = AgentRegistry()
        self.tool_router = tool_router
        self.brain = brain
        self.dispatcher = dispatcher
        self.route_tree = None
        if dispatcher is not None:
            try:
                from aura.core.route_tree import build_route_tree
                self.route_tree = build_route_tree()
            except Exception as e:
                print(f"⚠️ RouteTree init: {e}")
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
            # AURA_STRIP_VOCATIVE_V1 — убрать 'Создатель'
            if response.text:
                import re as _re
                response.text = _re.sub(
                    r',\s*Создатель\b', '', response.text).strip()
                response.text = _re.sub(
                    r'\bСоздатель,?\s*', '', response.text).strip()

            self._last_response = response
            _mem_write(text, response.text)
            return response.text

        if response.status == AgentStatus.NOT_HANDLED:
            return self.fallback_text

        if response.status == AgentStatus.ERROR:
            return f"❌ {response.error or 'Ошибка'}"

        return self.fallback_text

    FACTUAL_PREFIXES = ("погод", "курс ", "новост", "пробк", "гороскоп", "астро")

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
        "какая": "какая погода", "какой": "какой день",
        "какая": "какая погода", "какой": "какой день",
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
            # fuzzy по ключам
            try:
                from difflib import get_close_matches
                m = get_close_matches(w, self._FUZZY_MAP.keys(), n=1, cutoff=0.75)
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
                    prof_name = current().name if current() else "none"
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
