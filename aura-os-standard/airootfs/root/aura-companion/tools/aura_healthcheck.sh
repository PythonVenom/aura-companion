#!/bin/bash
set -e
echo "AURA HEALTHCHECK"
FAIL=0
if systemctl --user is-active --quiet aura-kernel.service; then
    echo "  OK kernel: active"
else
    echo "  FAIL kernel: inactive"
    FAIL=1
fi
if [ -x "$HOME/.local/bin/piper" ] || command -v piper >/dev/null 2>&1; then
    echo "  OK piper: found"
else
    echo "  WARN piper: not found (espeak fallback)"
fi
VOICE="$HOME/aura_project/voices/ru_RU-irina-medium.onnx"
if [ -f "$VOICE" ]; then
    echo "  OK voice model: found"
else
    echo "  FAIL voice model: missing"
    FAIL=1
fi
AVAIL=$(df -BG "$HOME" | tail -1 | awk '{print $4}' | tr -d "G")
if [ "$AVAIL" -gt 5 ]; then
    echo "  OK disk: ${AVAIL}G free"
else
    echo "  WARN disk: ${AVAIL}G free (low)"
fi
if [ $FAIL -eq 0 ]; then
    echo "  GREEN ALL OK"
    exit 0
else
    echo "  RED PROBLEMS"
    exit 1
fi
