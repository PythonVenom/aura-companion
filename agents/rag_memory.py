"""
Машинка RAG: Долговременная память (AgentRAGMemory)
Хранит диалоги в ChromaDB, ищет по эмбеддингам через Ollama.
"""

import os
import json
import time
import urllib.request
from datetime import datetime
from agents.base import MicroAgent


class AgentRAGMemory(MicroAgent):
    def __init__(self):
        super().__init__("rag_memory", "Долговременная память (RAG)")
        self.ready = False
        self.client = None
        self.collection = None
        self.embed_model = "nomic-embed-text"
        self.ollama_url = "http://localhost:11434/api/embeddings"

        # Папка для ChromaDB — на HDD, чтобы не забивать SSD
        self.db_path = "/mnt/aura_hdd/aura/rag_db"

        try:
            import chromadb
            os.makedirs(self.db_path, exist_ok=True)
            self.client = chromadb.PersistentClient(path=self.db_path)
            self.collection = self.client.get_or_create_collection(
                name="aura_dialogs",
                metadata={"hnsw:space": "cosine"}
            )
            self.ready = True
            print(f"✅ RAG-память загружена (диалогов: {self.collection.count()})")
        except Exception as e:
            print(f"⚠️ Ошибка RAG: {e}")
            self.ready = False

    def _get_embedding(self, text):
        """Получить эмбеддинг через Ollama"""
        try:
            data = json.dumps({
                "model": self.embed_model,
                "prompt": text
            }).encode('utf-8')

            req = urllib.request.Request(
                self.ollama_url,
                data=data,
                headers={'Content-Type': 'application/json'}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result.get('embedding')
        except Exception as e:
            print(f"⚠️ Ошибка эмбеддинга: {e}")
            return None

    def remember(self, user_text, aura_response):
        """Сохранить диалог в память"""
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
                    "aura": aura_response[:200]
                }],
                ids=[doc_id]
            )
            return f"📝 Запомнила диалог (ID: {doc_id[-6:]})"
        except Exception as e:
            return f"❌ Ошибка сохранения: {e}"

    def search(self, query, n_results=3):
        """Найти похожие диалоги"""
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
                n_results=min(n_results, self.collection.count())
            )

            if not results['documents'] or not results['documents'][0]:
                return "🔍 Ничего не найдено"

            answer = f"🔍 Нашла {len(results['documents'][0])} воспоминаний:\n"
            for i, (doc, meta) in enumerate(zip(results['documents'][0], results['metadatas'][0]), 1):
                ts = meta.get('timestamp', '')[:19]
                answer += f"\n{i}. [{ts}]\n   {doc[:200]}...\n"

            return answer
        except Exception as e:
            return f"❌ Ошибка поиска: {e}"

    def get_stats(self):
        """Статистика памяти"""
        if not self.ready:
            return "❌ RAG-память не готова"
        count = self.collection.count()
        return f"🧠 В памяти {count} диалогов"

    def clear(self):
        """Очистить память (осторожно!)"""
        if not self.ready:
            return "❌ RAG-память не готова"
        try:
            self.client.delete_collection("aura_dialogs")
            self.collection = self.client.get_or_create_collection(
                name="aura_dialogs",
                metadata={"hnsw:space": "cosine"}
            )
            return "🗑️ Память очищена"
        except Exception as e:
            return f"❌ Ошибка очистки: {e}"

    def execute(self, command):
        cmd = command.lower()

        if 'статистика памяти' in cmd or 'сколько помнишь' in cmd:
            return self.get_stats()

        if 'очисти память' in cmd or 'забудь всё' in cmd:
            return self.clear()

        if 'вспомни' in cmd or 'что я говорил' in cmd or 'поиск по памяти' in cmd:
            query = cmd
            for word in ['вспомни', 'что я говорил про', 'что я говорил', 'поиск по памяти', 'найди в памяти']:
                query = query.replace(word, '')
            query = query.strip()
            if not query:
                return "Что вспомнить?"
            return self.search(query)

        return "🧠 RAG-память готова. Команды: вспомни [X], статистика памяти, очисти память"
