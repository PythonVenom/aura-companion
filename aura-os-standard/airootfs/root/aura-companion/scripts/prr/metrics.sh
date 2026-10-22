#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/../.."
source venv/bin/activate 2>/dev/null || true
echo "=== METRICS ==="
echo "ADR:        $(ls docs/adr/[0-9][0-9][0-9]-*.md 2>/dev/null | wc -l)"
echo "Tests:      $(pytest -q 2>&1 | tail -1)"
echo "Handlers:   $(python3 -c 'from aura.core import dispatcher; print(len(dispatcher.list_registered()))' 2>/dev/null)"
echo "Routes:     $(python3 -c 'from aura.core.route_tree import build_route_tree; print(len(build_route_tree().children))' 2>/dev/null)"
echo "Py files:   $(find aura scripts tests -name '*.py' 2>/dev/null | wc -l)"
echo "LOC:        $(find aura scripts -name '*.py' 2>/dev/null | xargs wc -l 2>/dev/null | tail -1)"
echo "Commit:     $(git rev-parse --short HEAD)"
echo "Tag:        $(git describe --tags --abbrev=0 2>/dev/null || echo none)"
