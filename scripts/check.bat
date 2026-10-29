@echo off
echo === [1/3] Checking formatting with Black ===
black --check .
if %errorlevel% neq 0 exit /b %errorlevel%

echo === [2/3] Linting with Ruff ===
ruff check .
if %errorlevel% neq 0 exit /b %errorlevel%

echo === [3/3] Running tests with Pytest ===
pytest -v
if %errorlevel% neq 0 exit /b %errorlevel%

echo === All deterministic guardrails passed! ===
