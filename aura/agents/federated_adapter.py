"""T-fed-1 — LoRA-adapter на диалогах.

Наука:
- LoRA (Hu et al. 2021, Microsoft) — Low-Rank Adaptation
- Federated Learning (McMahan 2017, Google) — FedAvg
- PEFT / llama.cpp LoRA

Идея: собрать локальные диалоги (journal, emotion, memory) →
JSONL dataset → обучение LoRA через llama.cpp.
Данные НЕ покидают устройство. Обучение локально.
"""
from __future__ import annotations
import json
import sqlite3
import time
from pathlib import Path

from aura.agents.base import MicroAgent
from aura.core.protocol import AgentRequest, AgentResponse


ADAPTER_DIR = Path.home() / ".local/share/aura/lora"
JOURNAL_DB = Path.home() / ".local/share/aura/journal.db"
MEM_DB = Path.home() / ".local/share/aura/memories.db"
TWIN_DB = Path.home() / ".local/share/aura/health_twin.db"


class AgentFederatedAdapter(MicroAgent):
    name = "federated_adapter"

    TRIGGERS = ("loRA", "lora", "дообуч", "обучись", "fine-tune",
                "federated", "федерат", "персонализац")

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower()
        return any(kw in t for kw in self.TRIGGERS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        self._ensure()
        t = request.text.lower()

        if "статус" in t or "сколько" in t:
            return self._status()
        if "собери" in t or "собрать" in t or "dataset" in t:
            return self._collect()
        if "обучи" in t or "train" in t:
            return self._train()
        if "очист" in t or "сброс" in t:
            return self._clear()

        return AgentResponse.ok(
            text="LoRA adapter. "
                 "'собери датасет' / 'обучи' / 'статус' / 'очисти'",
            agent_name=self.name,
        )

    def _ensure(self) -> None:
        ADAPTER_DIR.mkdir(parents=True, exist_ok=True)

    def _collect_samples(self) -> list[dict]:
        """Собрать диалоги из journal + memories + health_twin."""
        samples: list[dict] = []

        # 1. Journal entries
        if JOURNAL_DB.exists():
            try:
                conn = sqlite3.connect(JOURNAL_DB)
                rows = conn.execute(
                    "SELECT text FROM entries ORDER BY id DESC LIMIT 500"
                ).fetchall()
                conn.close()
                for (text,) in rows:
                    if text and len(text) > 10:
                        samples.append({
                            "instruction": "Пользователь пишет в дневник.",
                            "input": "",
                            "output": text[:500],
                        })
            except Exception:
                pass

        # 2. Memories (autobiography)
        if MEM_DB.exists():
            try:
                conn = sqlite3.connect(MEM_DB)
                rows = conn.execute(
                    "SELECT text, tags FROM memories ORDER BY id DESC LIMIT 500"
                ).fetchall()
                conn.close()
                for text, tags in rows:
                    if text and len(text) > 10:
                        samples.append({
                            "instruction": f"Воспоминание [{tags}].",
                            "input": "",
                            "output": text[:500],
                        })
            except Exception:
                pass

        # 3. Health twin events (facts, не диалоги)
        if TWIN_DB.exists():
            try:
                conn = sqlite3.connect(TWIN_DB)
                rows = conn.execute(
                    "SELECT kind, subject, payload FROM events "
                    "ORDER BY id DESC LIMIT 300"
                ).fetchall()
                conn.close()
                for kind, subject, payload in rows:
                    try:
                        p = json.loads(payload)
                        text = p.get("text") or str(p)
                    except Exception:
                        text = str(payload)
                    if text and len(text) > 5:
                        samples.append({
                            "instruction": f"Событие: {kind} / {subject}.",
                            "input": "",
                            "output": text[:300],
                        })
            except Exception:
                pass

        return samples

    def _write_jsonl(self, samples: list[dict]) -> Path:
        """Записать JSONL в формате llama.cpp finetune."""
        ts = time.strftime("%Y%m%d-%H%M%S")
        out = ADAPTER_DIR / f"dataset-{ts}.jsonl"
        with out.open("w", encoding="utf-8") as f:
            for s in samples:
                # формат llama.cpp: text-стиль
                text = f"### Instruction:\n{s['instruction']}\n\n### Response:\n{s['output']}"
                f.write(json.dumps({"text": text}, ensure_ascii=False) + "\n")
        return out

    def _collect(self) -> AgentResponse:
        samples = self._collect_samples()
        if not samples:
            return AgentResponse.ok(
                text="📦 Нет данных для обучения. Пообщайся с Aura, потом 'собери датасет'.",
                agent_name=self.name,
            )
        out = self._write_jsonl(samples)
        return AgentResponse.ok(
            text=f"📦 Собрано {len(samples)} примеров → {out.name}",
            agent_name=self.name,
        )

    def _train(self) -> AgentResponse:
        """Запустить llama-finetune (если есть). Иначе — инструкция."""
        import shutil
        if not shutil.which("llama-finetune"):
            return AgentResponse.ok(
                text=(
                    "⚠️ llama-finetune не установлен.\n"
                    "1. Собери датасет: 'собери датасет'\n"
                    "2. Установи llama.cpp с finetune\n"
                    "3. llama-finetune -m model.gguf -f dataset.jsonl -o lora.gguf"
                ),
                agent_name=self.name,
            )
        return AgentResponse.ok(
            text="⚠️ Обучение долгое (≥1ч). Запускать в терминале — см. docs/FEDERATED.md",
            agent_name=self.name,
        )

    def _status(self) -> AgentResponse:
        datasets = list(ADAPTER_DIR.glob("dataset-*.jsonl"))
        adapters = list(ADAPTER_DIR.glob("*.gguf"))
        return AgentResponse.ok(
            text=f"📦 LoRA: {len(datasets)} датасетов, {len(adapters)} адаптеров.",
            agent_name=self.name,
        )

    def _clear(self) -> AgentResponse:
        n = 0
        for f in ADAPTER_DIR.glob("dataset-*.jsonl"):
            f.unlink()
            n += 1
        return AgentResponse.ok(
            text=f"🗑️ Удалено {n} датасетов. Адаптеры сохранены.",
            agent_name=self.name,
        )
