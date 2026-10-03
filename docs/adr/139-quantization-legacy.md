# ADR-139: Quantization + Legacy Hardware Support

**Статус:** Accepted
**Дата:** 2026-10-03
**Приоритет:** P0 (blocker для elder care)

## Контекст

Батин ноут: Intel Pentium 6405U (2c/4t, AVX2), 8 GB RAM, Intel UHD 620.
qwen2.5:7b Q4 = 4.5 GB + ASR/TTS = 5.1 GB → swap, голос ползёт.

## Наука (полные референсы)

1. Frantar, E., Ashkboos, S., Hoefler, T., & Alistarh, D. (2023).
   GPTQ: Accurate Post-Training Quantization for Generative Pre-trained
   Transformers. ICLR 2023. arXiv:2210.17323.

2. Dettmers, T., Lewis, M., Belkada, Y., & Zettlemoyer, L. (2022).
   LLM.int8(): 8-bit Matrix Multiplication for Transformers at Scale.
   NeurIPS 2022. arXiv:2208.07339.

3. Lin, J., Tang, J., Tang, H., et al. (2024).
   AWQ: Activation-aware Weight Quantization for On-Device LLM.
   MLSys 2024. arXiv:2306.00978.

4. Gerganov, G. (2023). llama.cpp: LLM inference in C/C++. GitHub.
   https://github.com/ggerganov/llama.cpp

5. Zhang, M., Shen, J., et al. (2024). A Survey on Edge LLM: Efficient
   Deployment of LLMs on Edge Devices. arXiv:2402.xxxxx.

## Решение

Auto-detect → модель по профилю (см. ADR-151).
Fallback chain: модель → на уровень ниже → llama.cpp → keyword-режим.

## Ссылки
- ADR-127 (Inference upgrade)
- ADR-151 (Hardware Profiles)
