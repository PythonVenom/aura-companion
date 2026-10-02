#!/usr/bin/env python3
import secrets, os
from pathlib import Path
p = Path.home() / ".config/aura/bridge_token"
p.parent.mkdir(parents=True, exist_ok=True)
if p.exists():
    print(f"[skip] {p} уже есть")
else:
    p.write_text(secrets.token_hex(32), encoding="utf-8")
    os.chmod(p, 0o600)
    print(f"[ok] {p} создан, права 600")
