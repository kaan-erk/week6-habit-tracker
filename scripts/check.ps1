$ErrorActionPreference = "Stop"

Write-Host "=== [1/3] Checking formatting with Black ===" -ForegroundColor Cyan
black --check .

Write-Host "=== [2/3] Linting with Ruff ===" -ForegroundColor Cyan
ruff check .

Write-Host "=== [3/3] Running tests with Pytest ===" -ForegroundColor Cyan
pytest -v

Write-Host "=== All deterministic guardrails passed! ===" -ForegroundColor Green
