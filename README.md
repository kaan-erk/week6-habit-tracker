# Week 6 — Habit Tracker (AI Code Review & Testing)

A lightweight FastAPI + SQLite service for habits and daily check-ins, developed with agentic workflows, deterministic guardrails, and disciplined human + AI code reviews.

## Student Information
- **Student Name**: Kaan Erk Toraman
- **Student ID**: 220901564
- **Student Email**: 220901564@stu.istinye.edu.tr
- **Course**: AI-Augmented Software Engineering (İstinye University)

## Setup & Running
```bash
python -m venv .venv
# Activate venv:
# Windows (PowerShell): .\.venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate

pip install -r requirements.txt
pytest
uvicorn main:app --reload
```

## Deterministic Guardrails
Run the guardrail check script locally:
```bash
# Windows
.\scripts\check.bat
# or in PowerShell:
.\scripts\check.ps1

# Linux / macOS
./scripts/check.sh
```

The guardrails enforce:
1. **Formatting**: `black --check .` (PEP 8 code formatting)
2. **Linting**: `ruff check .` (Static analysis, unused imports, common antipatterns)
3. **Testing**: `pytest -v` (Full test suite execution)

CI is configured via GitHub Actions (`.github/workflows/ci.yml`) to run these deterministic checks on every push and pull request.
