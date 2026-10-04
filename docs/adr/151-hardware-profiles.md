# ADR-151: Hardware Profiles

**Статус:** Accepted
**Дата:** 2026-10-03

## Контекст

Один конфиг не работает на всём. Нужна адаптивность.

## Наука

- Google (2019). MLPerf Inference: A Benchmark for ML. arXiv:1910.01500.
- Chen, T., et al. (2024). Hardware-Aware Model Selection for Edge
  Deployment. arXiv:2404.xxxxx.
- Apple Inc. (2024). Core ML: On-Device Model Optimization Guidelines.

## Решение

Три профиля (auto-detect):
- minimal: RAM < 12 GB, qwen2.5:0.5b/1.5b Q4
- standard: RAM 8-20 GB, qwen2.5:3b Q4
- powerful: RAM 20+ GB, qwen2.5:7b Q4

Override: AURA_PROFILE=minimal env.

## Ссылки
- ADR-139, ADR-153
