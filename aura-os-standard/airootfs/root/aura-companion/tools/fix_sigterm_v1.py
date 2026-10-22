#!/usr/bin/env python3
"""Graceful SIGTERM/SIGINT handler for aura_main (AURA_SIGTERM_FIX_V1)."""
import sys
from pathlib import Path

MAIN = Path.home() / "aura_project" / "aura_main.py"
MARK = "# >>> AURA_SIGTERM_FIX_V1"
src = MAIN.read_text(encoding="utf-8")

if MARK in src:
    print("[skip] already patched")
    sys.exit(0)

# Находим строку "if __name__" и вставляем перед ней блок
anchor = 'if __name__ == "__main__":'
if anchor not in src:
    print("[FAIL] anchor not found")
    sys.exit(1)

shutdown_block = f'''{MARK}
# Graceful shutdown: systemctl --user stop → SIGTERM → корректный выход.
import signal as _signal
import sys as _sys


def _aura_sigterm_handler(_signum, _frame):
    try:
        print("\\n🦾 Аура: SIGTERM, graceful shutdown...", flush=True)
    except Exception:
        pass
    _sys.exit(0)


for _sig in (_signal.SIGTERM, _signal.SIGINT):
    try:
        _signal.signal(_sig, _aura_sigterm_handler)
    except Exception:
        pass

'''

src = src.replace(anchor, shutdown_block + anchor, 1)
MAIN.write_text(src, encoding="utf-8")
print("[ok] aura_main.py: SIGTERM handler added")
