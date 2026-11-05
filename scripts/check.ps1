$ErrorActionPreference = "Stop"

$pythonCmd = "python"
if (Test-Path ".venv\Scripts\python.exe") {
    $pythonCmd = ".venv\Scripts\python.exe"
}

Write-Host "=== [1/3] Checking formatting with Black ===" -ForegroundColor Cyan
& $pythonCmd -m black --check .

Write-Host "=== [2/3] Linting with Ruff ===" -ForegroundColor Cyan
& $pythonCmd -m ruff check .

Write-Host "=== [3/3] Running tests with Pytest ===" -ForegroundColor Cyan
& $pythonCmd -m pytest -v

Write-Host "=== All deterministic guardrails passed! ===" -ForegroundColor Green
