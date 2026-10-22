# ADR-128: Hallucination Evaluation

**Статус:** Accepted
**Дата:** 2026-10-02

## Контекст

Мы не знаем hallucination rate Aura. Для семейного ИИ это недопустимо.
Бабушка может спросить «какое лекарство пить?» — Aura не имеет права выдумывать.

## Наука

- TruthfulQA: Lin, S. et al. (2022). Measuring How Models Mimic Human Falsehoods. ACL.
- HaluEval: Li, J. et al. (2023). A Large-Scale Hallucination Evaluation Benchmark. EMNLP.
- RAGAS: Es, S. et al. (2023). Automated Evaluation of Retrieval Augmented Generation.
- FActScore: Min, S. et al. (2023). Fine-grained Atomic Evaluation. EMNLP.
- SelfCheckGPT: Manakul, P. et al. (2023). Zero-Resource Black-Box Hallucination Detection. EMNLP.

## Решение

Три метрики в scripts/run_hallucination_eval.py:

### 1. Faithfulness (RAGAS-style)
Для RAG-ответов: проверяем, что утверждения вытекают из retrieved context.
- Разбиваем ответ на atomic claims
- NLI-модель проверяет entailment с context
- Faithfulness = entailed / total

### 2. Groundedness (SelfCheckGPT)
Для фактов из Social/Semantic memory:
- Задаём один вопрос 5 раз (T=0.7)
- Consistency = agree / total
- Low consistency → hallucination signal

### 3. Truthfulness (TruthfulQA subset)
Для общих вопросов:
- 100 факт-вопросов (health, science, history)
- Правильные / неправильные / unsure
- Metric: accuracy + refusal_rate

## Датасет Aura

evals/hallucination.yaml:
- 30 медицинских (что НЕЛЬЗЯ выдумывать)
- 20 детских (проверка фактичности)
- 30 семейных (факты из Social memory)
- 20 общих (TruthfulQA-style)

## Интеграция в release gate

scripts/scaffold/release.py:
- Шаг 3.5: hallucination rate < 5% (иначе тег блокируется)
- Faithfulness > 0.85
- SelfCheck consistency > 0.9

## Последствия

- (+) знаем, врёт ли Aura
- (+) можем улучшать промпт измеримо
- (+) safety: красный флаг для критичных тем
- (−) +N LLM вызовов в eval (дорого)

## Милстоун

v4.0: датасет + скрипт + метрики
v4.0-beta: интеграция в release gate
v5.0: real-time hallucination detection в runtime

## Ссылки

- Lin (2022), Li (2023), Es (2023), Min (2023), Manakul (2023)
- ADR-116 (Evals v0), ADR-126 (Meta), ADR-127 (Inference)
