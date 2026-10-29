#!/usr/bin/env bash
set -e

echo "=== [1/3] Checking formatting with Black ==="
black --check .

echo "=== [2/3] Linting with Ruff ==="
ruff check .

echo "=== [3/3] Running tests with Pytest ==="
pytest -v

echo "=== All deterministic guardrails passed! ==="
