# 🗺️ Архитектурная Карта Aura
1. aura_main.py: Главный цикл (слушает и говорит).
2. orchestrator.py: Мозг. Решает, кто отвечает (MCP, ReAct или LLM).
3. mcp/manager.py: Менеджер MCP-серверов.
4. agents/speaker.py: Голос (Edge-TTS).
5. agents/barge_in.py: VAD перебивание.
