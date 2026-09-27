#!/usr/bin/env bash
# Aura — бенчмарки голосового цикла.
# Baseline: Intel Coffee Lake-H + NVIDIA GTX 1070M (2016).
set -e
cd "$(dirname "$0")/.."

mkdir -p benchmarks/results
OUT=benchmarks/results/$(date +%Y%m%d-%H%M%S).md
mkdir -p benchmarks/results

{
echo "# Aura Benchmark — $(date -Iseconds)"
echo ""
echo "## Hardware"
echo '```'
echo "CPU: $(lscpu | grep -iE 'model name' | head -1 | cut -d: -f2- | xargs)"
echo "GPU: $(nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader 2>/dev/null || echo 'no NVIDIA')"
echo "RAM: $(free -h | grep Mem | awk '{print $2}')"
echo '```'
echo ""

# 1. LLM
echo "## LLM (Ollama qwen2.5:7b-instruct-q4_K_M)"
echo '```'
for i in 1 2 3; do
  ollama run qwen2.5:7b-instruct-q4_K_M "ответь одним словом: тест" --verbose 2>&1 | grep -E "eval rate|prompt eval rate|total duration" | sed "s/^/run $i: /"
done
echo '```'
echo ""

# 2. ASR — TODO: подключить когда T-one доступен через CLI
echo "## ASR (T-one streaming)"
echo "TODO: нужен отдельный скрипт для загрузки wav и замера."
echo ""

# 3. TTS — TODO: Piper
echo "## TTS (Piper ru_RU-irina-medium)"
echo "TODO: замер синтеза фразы."
echo ""

# 4. End-to-end
echo "## End-to-end (voice → ответ)"
echo "TODO: замер полного цикла."
echo ""

echo "## Ожидание на AMD Strix Halo"
echo "- LLM: 7B Q4 — 5–10× быстрее (\~250 tok/s)"
echo "- LLM: 32B Q4 — ожидаем 50–80 tok/s (умещается в unified memory)"
echo "- Энергопотребление: 40–55 W vs 90 W у GTX 1070M"
} | tee "$OUT"

echo ""
echo "Saved: $OUT"
