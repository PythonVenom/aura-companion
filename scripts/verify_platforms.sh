#!/bin/bash
# Cross-platform verification (F-027)
cd "$(dirname "$0")/.."
source venv/bin/activate 2>/dev/null

echo "=== Платформа ==="
uname -a
python3 --version

echo ""
echo "=== Импорт platform-модулей ==="
for mod in aura.platform aura.platform.linux aura.platform.windows aura.platform.macos aura.platform.ubuntu; do
    if python3 -c "import $mod" 2>/dev/null; then
        echo "  ✅ $mod"
    else
        echo "  ❌ $mod"
    fi
done

echo ""
echo "=== PAL тесты ==="
pytest tests/test_pal.py tests/test_pal_windows.py tests/test_pal_macos.py -q --tb=line 2>&1 | tail -3

echo ""
echo "=== Capabilities ==="
python3 -c "from aura.core.capabilities import CLASSES; [print(f'  {n}: {len(c)} caps') for n, c in CLASSES.items()]"
