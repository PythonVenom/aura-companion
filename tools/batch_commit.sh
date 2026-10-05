#!/usr/bin/env bash
# Aura batch commit — AST + pytest + mark done + commit + push.
# Наука: Ohno 1988 (batch size), Goldratt 1984 (bottleneck).

set -euo pipefail

cd ~/aura_project
source venv/bin/activate

TASKS="${1:-}"
MSG="${2:-batch commit}"

log() { printf "\033[1;34m[batch]\033[0m %s\n" "$*"; }

# 1. AST всех изменённых .py
log "AST check..."
CHANGED=$(git diff --name-only HEAD | grep '\.py$' || true)
if [ -n "$CHANGED" ]; then
    echo "$CHANGED" | while read -r f; do
        python3 -c "import ast; ast.parse(open('$f').read())" || exit 1
    done
    log "AST OK ($(echo "$CHANGED" | wc -l) файлов)"
fi

# 2. Pytest
log "pytest..."
pytest -q --tb=short 2>&1 | tail -3

# 3. Mark done (если ID переданы)
if [ -n "$TASKS" ]; then
    log "Mark done: $TASKS"
    python3 <<PYEOF
import json
from pathlib import Path
p = Path.home()/"aura_project/.aura/tasks.json"
d = json.loads(p.read_text(encoding="utf-8"))
ids = "$TASKS".split(",")
for tid in ids:
    for t in d["tasks"]:
        if t["id"] == tid.strip():
            t["state"] = "done"
p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
done = sum(1 for t in d["tasks"] if t["state"]=="done")
print(f"  → {done}/{d['total']} ({done*100//d['total']}%)")
PYEOF
fi

# 4. Commit + push
log "Commit + push..."
git add -A
if git diff --cached --quiet; then
    log "Нечего коммитить."
    exit 0
fi
git commit -m "$MSG"
git push origin master
log "Готово."
