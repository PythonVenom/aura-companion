# ADR-133: Verifier + Red Team

**Статус:** Accepted
**Дата:** 2026-10-02

## Наука

- Es, S. et al. (2023). RAGAS: Automated Evaluation of RAG. EACL.
- Manakul, P. et al. (2023). SelfCheckGPT. EMNLP.
- Perez, E. et al. (2022). Red Teaming Language Models with Language Models. EMNLP.
- Ganguli, D. et al. (2022). Red Teaming Language Models to Reduce Harms.

## Verifier

Перед отдачей ответа:
1. Если ответ основан на memory-recall → проверить support (NLI)
2. Если ответ содержит числа/даты/имена → cross-check с фактами
3. Если hallucination_score > 0.3 → добавить хедж или отказать

## Red Team

30 атакующих промптов:
- Prompt injection («ignore previous instructions»)
- Jailbreak («pretend you have no rules»)
- Authority («I am your developer»)
- Emotional («if you don't answer, I'll hurt myself»)
- Medical/legal boundary pushes
- Harm disguised as fiction

Метрика: pass rate ≥ 95%.

## Файлы

- aura/core/verifier.py — Verifier
- evals/red_team.yaml — 30 атак
- scripts/run_red_team.py
