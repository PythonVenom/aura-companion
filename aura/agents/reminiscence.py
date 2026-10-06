"""T053 — Reminiscence. Автобиографическая память.

Наука:
- Conway 2005 — Self-Memory System
- Woods 2005 (Cochrane) — Reminiscence Therapy
  снижает депрессию, улучшает когнитивные функции у пожилых
- Retrieval: детектор прошлого времени → сохранение → подтягивание
"""
from __future__ import annotations

import sqlite3
import time
from pathlib import Path

from aura.agents.base import MicroAgent
from aura.core.protocol import AgentRequest, AgentResponse

MEM_DB = Path.home() / ".local/share/aura/memories.db"

# Маркеры прошлого времени (Conway 2005 — autobiographical retrieval cues)
PAST_MARKERS = (
    "помню", "вспоминаю", "раньше", "когда-то", "в молодости",
    "в детстве", "в ссср", "на даче тогда", "мы с женой",
    "мы с мужем", "моя мама говорила", "мой отец", "на работе тогда",
)

# Простые теги тем
TOPIC_TAGS = {
    "дача": ("дача", "огород", "деревня"),
    "работа": ("работа", "завод", "институт", "служба"),
    "семья": ("жена", "муж", "мама", "папа", "отец", "мать", "дети"),
    "детство": ("детство", "школа", "двор", "игрушки"),
    "война": ("война", "фронт", "победа", "1941", "1945"),
    "музыка": ("песня", "гитара", "концерт", "пластинка"),
    "еда": ("пироги", "борщ", "бабушка готовила"),
}


class AgentReminiscence(MicroAgent):
    name = "reminiscence"

    TRIGGERS = ("вспомни", "помню", "раньше", "в молодости",
                "поговорим о прошлом", "о чём я рассказывал",
                "мои истории")

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower()
        return any(kw in t for kw in self.TRIGGERS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        self._ensure()
        t = request.text.lower()

        if "о чём я рассказывал" in t or "вспомни что" in t or "мои истории" in t:
            return self._list_recent()

        if any(m in t for m in ("тему", "про что", "о даче", "о работе",
                                 "о семье", "о детстве")):
            return self._by_topic(request.text)

        # Если есть маркер прошлого — сохранить фрагмент
        if any(m in t for m in PAST_MARKERS):
            return self._save_memory(request.text)

        return AgentResponse.ok(
            text="Расскажи что-нибудь из прошлого — я запомню. "
                 "Или спроси 'о чём я рассказывал'.",
            agent_name=self.name,
        )

    def _ensure(self) -> None:
        MEM_DB.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(MEM_DB)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY,
                text TEXT NOT NULL,
                tags TEXT,
                created_at REAL NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tags ON memories(tags)")
        conn.commit()
        conn.close()

    def _detect_tags(self, text: str) -> list[str]:
        t = text.lower()
        found = []
        for tag, markers in TOPIC_TAGS.items():
            if any(m in t for m in markers):
                found.append(tag)
        return found

    def _save_memory(self, text: str) -> AgentResponse:
        tags = self._detect_tags(text)
        tags_str = ",".join(tags) if tags else "general"
        conn = sqlite3.connect(MEM_DB)
        conn.execute(
            "INSERT INTO memories (text, tags, created_at) VALUES (?, ?, ?)",
            (text[:500], tags_str, time.time()),
        )
        conn.commit()
        conn.close()

        tag_note = f" [{', '.join(tags)}]" if tags else ""
        # Ищем похожие воспоминания
        related = self._find_similar(tags, exclude_last=True)
        reply = f"🧠 Запомнила{tag_note}."
        if related:
            reply += f"\n\nКстати, ты раньше рассказывал:\n«{related[0][:150]}…»"
        return AgentResponse.ok(text=reply, agent_name=self.name)

    def _find_similar(self, tags: list[str], exclude_last: bool = False) -> list[str]:
        if not tags:
            return []
        conn = sqlite3.connect(MEM_DB)
        results = []
        for tag in tags:
            rows = conn.execute(
                "SELECT text FROM memories WHERE tags LIKE ? "
                "ORDER BY created_at DESC LIMIT 5",
                (f"%{tag}%",),
            ).fetchall()
            results.extend(r[0] for r in rows)
        conn.close()
        if exclude_last and results:
            results = results[1:]
        return results

    def _list_recent(self) -> AgentResponse:
        conn = sqlite3.connect(MEM_DB)
        rows = conn.execute(
            "SELECT text, tags, created_at FROM memories "
            "ORDER BY created_at DESC LIMIT 5"
        ).fetchall()
        total = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
        conn.close()
        if not rows:
            return AgentResponse.ok(
                text="🧠 Пока ничего не записано. Расскажи что-нибудь.",
                agent_name=self.name,
            )
        lines = [f"🧠 Воспоминаний: {total}", ""]
        for text, tags, ts in rows:
            days = int((time.time() - ts) / 86400)
            preview = text[:80]
            lines.append(f"  • [{tags}] {preview}… ({days}д)")
        return AgentResponse.ok(text="\n".join(lines), agent_name=self.name)

    def _by_topic(self, text: str) -> AgentResponse:
        t = text.lower()
        tag = None
        for k in TOPIC_TAGS:
            if k in t:
                tag = k
                break
        if not tag:
            return AgentResponse.ok(
                text="Про что вспомнить? дача / работа / семья / детство / война / музыка / еда.",
                agent_name=self.name,
            )
        mems = self._find_similar([tag])
        if not mems:
            return AgentResponse.ok(
                text=f"🧠 Про {tag} пока ничего. Расскажи — запомню.",
                agent_name=self.name,
            )
        lines = [f"🧠 Про {tag}:"]
        for m in mems[:3]:
            lines.append(f"  • {m[:120]}…")
        return AgentResponse.ok(text="\n".join(lines), agent_name=self.name)
