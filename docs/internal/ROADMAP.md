# Aura — Internal Roadmap (НЕ ПУБЛИКОВАТЬ)

> Мир видит только то, что мы уже умеем. Куда идём — сюрприз.

## Стратегия

Aura = **локальный семейный ИИ-медиатор**, который:
1. Работает на **любом** железе (Tier 0..3)
2. Сам определяет железо и конфигурируется (Apple-подход)
3. Работает без сети (edge-first)
4. Никогда не заменяет привычное — только усиливает (прослойка над Алисой)

## Tier-архитектура (наука 0)

| Tier | RAM | LLM | RAM бюджет | Для кого |
|------|-----|-----|------------|----------|
| 0    | <2GB | нет | ~85 MB | MCU, часы, батя без сети |
| 0+   | 2-4GB | qwen2.5:0.5b | ~500 MB | Батин ноут (сеть) |
| 1    | 4-8GB | qwen2.5:1.5b | ~2 GB | Edge ноут |
| 2    | 8-16GB | qwen2.5:3b | ~4 GB | Домашний ноут |
| 3    | 16+GB | qwen2.5:7b | ~8 GB | Десктоп/сервер |

## Наука оптимизации (ADR-139, 151-153)

- Quantization: GPTQ, AWQ, BitNet 1.58-bit
- Keyword Spotting: DS-CNN 20KB (не full ASR)
- fastText intent classifier (не LLM)
- Template engine (90% команд — мгновенно)
- Speculative Decoding (SLED)
- Prompt Cache (Gim 2023)
- Streaming LLM

## Метрики

| Tier | TTFT | p95 | CPU |
|------|------|-----|-----|
| 0 | 0ms | 10ms | <5% |
| 1 | 500ms | 2s | 20-40% |
| 3 | 200ms | 1s | 60% |

## v5.0 — в работе
- Meta-memory (10-й слой) ✅
- NLU embeddings (ADR-132) ✅
- Verifier + Red Team (ADR-133) ✅
- Self-config: hardware_detect, model_selector, profiler, caches (ADR-151-153) 🟡
- Tier 0: intent_classifier, templates, tier0_orchestrator (ADR-152) 🟡

## v6.0 — план
- A. Self-Modification (Darwin Gödel Machine)
- B. Adaptive Computation Time
- C. MoE Router
- D. Homeostasis + Drives
- E. Self-Evaluation Loop

## v7.0 — план
- Affective Computing
- Theory of Mind
- Hebbian Memory

## v8.0 — план
- Evals v3 (LoCoMo, MT-Bench)
- Chaos Engineering
- HA
- Plugin SDK
- i18n ICU + RTL

## v9.0 — план
- Remote Brain (edge ↔ cloud, P2P via Exo) — ОТЛОЖЕНО
- Community
- Multi-user
- Deployment (Docker, install scripts)

## Принцип

Каждая версия закрывает >=1 🔴 дыру. CARMA >= +100.
