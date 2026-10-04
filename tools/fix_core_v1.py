#!/usr/bin/env python3
"""P1+P2: убрать вокатив из fallback + Guard перед LLM."""
from pathlib import Path
import sys

MAIN = Path.home() / "aura_project" / "aura" / "core" / "orchestrator.py"
src = MAIN.read_text(encoding="utf-8")

# Idempotency: если _is_factual_intent уже есть — skip
if "_is_factual_intent" in src:
    print("[skip] already patched")
    sys.exit(0)

# === P1: fallback_text без вокатива ===
old1 = '        self.fallback_text = "Не расслышала, Создатель, повторите"'
new1 = '        self.fallback_text = "Не расслышала. Повтори, пожалуйста."  # AURA_CORE_FIX_V1'
if old1 not in src:
    print("[FAIL] P1: fallback_text not found")
    sys.exit(1)
src = src.replace(old1, new1, 1)
print("[ok] P1: fallback_text без вокатива")

# === P2a: добавить _is_factual_intent перед last_silent ===
old2 = '    def last_silent(self) -> bool:'
new2 = '''    FACTUAL_PREFIXES = ("погод", "курс ", "новост", "пробк", "гороскоп", "астро")

    def _is_factual_intent(self, text: str) -> bool:
        """True = факт-запрос, LLM не должен отвечать. AURA_CORE_FIX_V1."""
        t = text.lower()
        return any(p in t for p in self.FACTUAL_PREFIXES)

    def last_silent(self) -> bool:'''
if old2 not in src:
    print("[FAIL] P2a: last_silent not found")
    sys.exit(1)
src = src.replace(old2, new2, 1)
print("[ok] P2a: _is_factual_intent added")

# === P2b: guard перед brain ===
old3 = '''            # 3. Brain
            if self.brain is not None:'''
new3 = '''            # 3. GUARD (AURA_CORE_FIX_V1): не отдавать в LLM факт-запросы без агента
            if self._is_factual_intent(text):
                return "Пока не умею это. Скажи иначе или попроси другое."
            # 3. Brain
            if self.brain is not None:'''
if old3 not in src:
    print("[FAIL] P2b: Brain block not found")
    sys.exit(1)
src = src.replace(old3, new3, 1)
print("[ok] P2b: guard added")

MAIN.write_text(src, encoding="utf-8")
print("--- P1+P2 DONE ---")
