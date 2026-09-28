#!/usr/bin/env bash
# Покрытие тестов
set -euo pipefail
cd "$(dirname "$0")/.."
source venv/bin/activate
python -m pytest tests/ -q --cov=aura --cov-report=term-missing --cov-report=html
echo ""
echo "HTML: htmlcov/index.html"
