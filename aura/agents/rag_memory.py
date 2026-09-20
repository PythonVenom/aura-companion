"""
Агент долговременной памяти (RAG).

Хранит диалоги в ChromaDB, ищет по эмбеддингам через Ollama.

Мигрирован из agents/rag_memory.py (монолит).
Изменения при миграции:
- Контракт BaseAgent: can_handle / handle (для команд пользователя)
- remember() остаётся публичным методом — его дёргает aura_main.py
  после каждого ответа Ауры. Это событие, а не команда.
- check_ready() — публичный, чтобы главный цикл знал состояние.

ВАЖНО:
- db_path НЕ меняется — монолит и модуль делят одну базу на HDD.
- collection НЕ меняется — иначе RAG-память раздвоится.
- Зависимость от Ollama (localhost:11434) — живая. Если Ollama
  не запущен, все операции вернут ошибку, но агент не упадёт.

Наука:
- Команды (что говорит пользователь) → can_handle / handle
- События (что делает система) → публичные методы
- Никаких import __main__, никаких ссылок на оркестратор
"""

from __future__ import annotations

import json
import os
import time
import urllib.request
from datetime import datetime

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


class AgentRAGMemory(BaseAgent):
    """
    RAG-память диалогов.

    Обрабатывает запросы:
    - "вспомни X" / "что я говорил про X" / "найди в памяти X"
    - "статистика памяти" / "сколько помнишь"
    - "очисти память" / "забудь всё"

    Плюс публичный метод remember(user, aura) — вызывается
    из главного цикла после каждого ответа Ауры.
    """

    name = "rag_memory"

    # Ключевые слова для can_handle
    SEARCH_KEYWORDS = ("вспомни", "что я говорил", "поиск по памяти", "найди в памяти")
    STATS_KEYWORDS = ("статистика памяти", "сколько помнишь")
    CLEAR_KEYWORDS = ("очисти память", "забудь всё")

    # Хардкод путей — не меняем при миграции, чтобы не раздвоить базу
    DB_PATH = "/mnt/aura_hdd/aura/rag_db"
    COLLECTION_NAME = "aura_dialogs"
    EMBED_MODEL = "nomic-embed-text"
    OLLAMA_URL = "http://localhost:11434/api/embeddings"

    def __init__(self) -> None:
        self.ready = False
        self.client = None
        self.collection = None
        self._init_chroma()

    def _init_chroma(self) -> None:
        """Инициализация ChromaDB. При ошибке агент остаётся ready=False."""
        try:
            import chromadb

            os.makedirs(self.DB_PATH, exist_ok=True)
            self.client = chromadb.PersistentClient(path=self.DB_PATH)
            self.collection = self.client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )
            self.ready = True
            print(f"✅ RAG-память загружена (диалогов: {self.collection.count()})")
        except Exception as e:
            print(f"⚠️ Ошибка RAG: {e}")
            self.ready = False

    def check_ready(self) -> bool:
        """Публичный метод — главный цикл спрашивает состояние."""
        return self.ready

    # --- Публичные методы (события) ---

    def remember(self, user_text: str, aura_response: str) -> str:
        """
        Сохранить диалог в память.

        Вызывается из aura_main.py после каждого ответа Ауры.
        Возвращает текст статуса (для логирования), не AgentResponse.
        """
        if not self.ready:
            return "❌ RAG-память не готова"

        try:
            combined = f"Пользователь: {user_text}\nАура: {aura_response}"
            embedding = self._get_embedding(combined)
            if not embedding:
                return "❌ Не удалось получить эмбеддинг"

            doc_id = f"dialog_{int(time.time() * 1000)}"

            self.collection.add(
                documents=[combined],
                embeddings=[embedding],
                metadatas=[{
                    "timestamp": datetime.now().isoformat(),
                    "user": user_text[:200],
                    "aura": aura_response[:200],
                }],
                ids=[doc_id],
            )
            return f"📝 Запомнила диалог (ID: {doc_id[-6:]})"
        except Exception as e:
            return f"❌ Ошибка сохранения: {e}"

    # --- Контракт BaseAgent (команды) ---

    def can_handle(self, request: AgentRequest) -> bool:
        text = request.text.lower()
        return any(
            kw in text
            for kw in self.SEARCH_KEYWORDS + self.STATS_KEYWORDS + self.CLEAR_KEYWORDS
        )

    async def handle(self, request: AgentRequest) -> AgentResponse:
        cmd = request.text.lower()

        if any(kw in cmd for kw in self.STATS_KEYWORDS):
            return AgentResponse.ok(text=self.get_stats(), agent_name=self.name)

        if any(kw in cmd for kw in self.CLEAR_KEYWORDS):
            return AgentResponse.ok(text=self.clear(), agent_name=self.name)

        if any(kw in cmd for kw in self.SEARCH_KEYWORDS):
            query = cmd
            for word in [
                "вспомни", "что я говорил про", "что я говорил",
                "поиск по памяти", "найди в памяти",
            ]:
                query = query.replace(word, "")
            query = query.strip()
            if not query:
                return AgentResponse.ok(
                    text="Что вспомнить?", agent_name=self.name
                )
            return AgentResponse.ok(
                text=self.search(query), agent_name=self.name
            )

        return AgentResponse.not_handled(agent_name=self.name)

    # --- Публичные операции над памятью ---

    def search(self, query: str, n_results: int = 3) -> str:
        """Найти похожие диалоги."""
        if not self.ready:
            return "❌ RAG-память не готова"

        if self.collection.count() == 0:
            return "📭 Память пуста — нечего искать"

        try:
            embedding = self._get_embedding(query)
            if not embedding:
                return "❌ Не удалось получить эмбеддинг"

            results = self.collection.query(
                query_embeddings=[embedding],
                n_results=min(n_results, self.collection.count()),
            )

            if not results["documents"] or not results["documents"][0]:
                return "🔍 Ничего не найдено"

            answer = f"🔍 Нашла {len(results['documents'][0])} воспоминаний:\n"
            for i, (doc, meta) in enumerate(
                zip(results["documents"][0], results["metadatas"][0]), 1
            ):
                ts = meta.get("timestamp", "")[:19]
                answer += f"\n{i}. [{ts}]\n   {doc[:200]}...\n"

            return answer
        except Exception as e:
            return f"❌ Ошибка поиска: {e}"

    def get_stats(self) -> str:
        """Статистика памяти."""
        if not self.ready:
            return "❌ RAG-память не готова"
        count = self.collection.count()
        return f"🧠 В памяти {count} диалогов"

    def clear(self) -> str:
        """Очистить память (осторожно!)."""
        if not self.ready:
            return "❌ RAG-память не готова"
        try:
            self.client.delete_collection(self.COLLECTION_NAME)
            self.collection = self.client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )
            return "🗑️ Память очищена"
        except Exception as e:
            return f"❌ Ошибка очистки: {e}"

    # --- Внутренние методы ---

    def _get_embedding(self, text: str) -> list[float] | None:
        """Получить эмбеддинг через Ollama."""
        try:
            data = json.dumps({
                "model": self.EMBED_MODEL,
                "prompt": text,
            }).encode("utf-8")

            req = urllib.request.Request(
                self.OLLAMA_URL,
                data=data,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result.get("embedding")
        except Exception as e:
            print(f"⚠️ Ошибка эмбеддинга: {e}")
            return None


__all__ = ["AgentRAGMemory"]
