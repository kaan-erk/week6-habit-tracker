@echo off
setlocal

set "PYTHON_EXE=python"
if exist ".venv\Scripts\python.exe" set "PYTHON_EXE=.venv\Scripts\python.exe"

echo === [1/3] Checking formatting with Black ===
%PYTHON_EXE% -m black --check .
if %errorlevel% neq 0 exit /b %errorlevel%

echo === [2/3] Linting with Ruff ===
%PYTHON_EXE% -m ruff check .
if %errorlevel% neq 0 exit /b %errorlevel%

echo === [3/3] Running tests with Pytest ===
%PYTHON_EXE% -m pytest -v
if %errorlevel% neq 0 exit /b %errorlevel%

echo === All deterministic guardrails passed! ===
