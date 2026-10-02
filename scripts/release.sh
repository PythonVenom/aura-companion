#!/usr/bin/env bash
# Release gate: тег ставится ТОЛЬКО если всё зелёное.
# Лечит ошибки v3.0 #6 (перевешивали тег) и #10 (ADR врал).
set -e
cd "$(dirname "$0")/.."
source venv/bin/activate 2>/dev/null || true

TAG="${1:?usage: release.sh vX.Y [-m message]}"
MSG="${2:-Release $TAG}"

echo "==> 1/5 pytest"
if ! pytest -q 2>&1 | tail -1 | grep -q "passed" || pytest -q 2>&1 | grep -q "failed"; then
    echo "❌ pytest не зелёный — тег отменён"
    exit 1
fi

echo "==> 2/5 git status clean?"
if [ -n "$(git status --porcelain)" ]; then
    echo "❌ грязный working tree — тег отменён"
    git status --short
    exit 1
fi

echo "==> 3/5 ADR-индекс свежий?"
pytest tests/test_adr_index.py -q 2>&1 | tail -1 || { echo "❌ ADR index"; exit 1; }

echo "==> 4/5 HEAD == origin?"
git fetch origin -q
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/master 2>/dev/null || echo "")
if [ "$LOCAL" != "$REMOTE" ]; then
    echo "❌ HEAD != origin/master. Сначала git push."
    exit 1
fi

echo "==> 5/5 tag $TAG"
git tag -a "$TAG" -m "$MSG"
git push origin "$TAG"
echo "✅ $TAG → $(git rev-parse --short HEAD)"
