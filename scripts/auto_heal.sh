#!/usr/bin/env bash
# Auto-heal script: runs ruff (fix), isort, black across python files
set -euo pipefail
ROOT=$(dirname "$0")/..
cd "$ROOT"

echo "Running ruff --fix"
ruff . --fix

echo "Running isort"
isort .

echo "Running black"
black .

echo "Auto-heal complete. Consider running tests and reviewing changes."
