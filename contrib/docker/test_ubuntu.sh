#!/usr/bin/env bash
# Тест PAL на чистой Ubuntu через Docker
set -euo pipefail

echo "=== Test PAL on Ubuntu (Docker) ==="

docker run --rm -v "$(pwd):/app" -w /app ubuntu:24.04 bash -c "
    apt-get update -qq
    apt-get install -y --no-install-recommends python3.12 python3-pip portaudio19-dev
    pip install --break-system-packages pytest
    python3 -c 'from aura.platform.ubuntu import UbuntuAudio; print(\"Ubuntu PAL ok\")'
    python3 -m pytest tests/test_pal_ubuntu.py -q
"

echo "=== OK ==="
