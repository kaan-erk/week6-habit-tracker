# Week 6 Writeup: AI Code Review & Testing (Habit Tracker)

- **Student Name**: Kaan Erk Toraman
- **Student ID**: 220901564
- **Student Email**: 220901564@stu.istinye.edu.tr
- **Course**: AI-Augmented Software Engineering (İstinye University)
- **Repository**: [https://github.com/kaan-erk/week6-habit-tracker](https://github.com/kaan-erk/week6-habit-tracker)

---

## 1. The Two Pull Requests

Both features were implemented from [`docs/TASKS.md`](docs/TASKS.md) on isolated feature branches, developed with agentic one-shot implementations followed by disciplined line-by-line human reviews, and reviewed by an independent AI reviewer. Both pull requests are kept open so all review comments and diffs remain visible:

| PR # | Feature | Branch | Commits | Link |
|---|---|---|---|---|
| **#1** | **Streak Endpoint** (`GET /habits/{id}/streak`) | `feature/streak` | 1. Agent one-shot implementation<br>2. Manual code review fixes | [PR #1](https://github.com/kaan-erk/week6-habit-tracker/pull/1) |
| **#2** | **Input Validation** (Name & Day validation) | `feature/validation` | 1. Agent one-shot implementation<br>2. Manual code review fixes | [PR #2](https://github.com/kaan-erk/week6-habit-tracker/pull/2) |

---

## 2. Guardrails Setup (Part I)

Deterministic guardrails serve as the non-negotiable first line of defense before any human or AI review takes place.

### Commands & Automated Scripts
```bash
# Windows
.\scripts\check.bat
# or in PowerShell:
.\scripts\check.ps1

# Linux / macOS
./scripts/check.sh
```

### What Each Guardrail Catches
1. **Black (`black --check .`)**: Catches deviations from standard PEP 8 formatting, inconsistent indentation, quote discrepancies, and irregular whitespace.
2. **Ruff (`ruff check .`)**: Catches unused imports (`F401`), unsorted import blocks (`I001`), anti-patterns, incorrect exception typing (e.g. `TRY004`), and undefined variables.
3. **Pytest (`pytest -v`)**: Executes unit and integration test suites, ensuring regressions, broken contracts, edge cases, and HTTP error statuses are caught instantly.

### Continuous Integration (CI) & Failure Demonstration
- **GitHub Actions CI** ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)) automatically triggers on every `push` and `pull_request`, running Black, Ruff, and Pytest.
- **Evidence of Failing Guardrails**: Demonstrated in [`docs/evidence/guardrails.txt`](docs/evidence/guardrails.txt) and via branch [`demo/failing-guardrails`](https://github.com/kaan-erk/week6-habit-tracker/tree/demo/failing-guardrails) where a failing test halts the pipeline and fails the build.

---

## 3. Human Review vs. AI Review Comparison

### PR #1: Streak Endpoint (`GET /habits/{id}/streak`)

| Aspect / Topic | My Human Manual Review | AI Code Review | Evaluation & Outcome |
|---|---|---|---|
| **Server Clock & Timezone Decoupling** | Spotted that `date.today()` binds calculations to server time, risking midnight test flakiness; added optional `today` query parameter with validation. | Commended the `today` parameter for test determinism; suggested bounding `today` to prevent far-future dates (`9999-12-31`). | **Tie / Complementary**: Human identified and fixed the architecture flaw; AI suggested a defense-in-depth bound. |
| **FastAPI Response Contract** | Added explicit `StreakOut(BaseModel)` for strict schema validation and accurate OpenAPI generation. | Validated response model adherence and noted contract safety. | **Human**: Caught the missing schema contract before PR creation. |
| **Native Query Parameter Parsing** | Implemented custom `date.fromisoformat` try/except block. | Pointed out that FastAPI supports `today: date | None = None` natively in query params to automate parsing. | **AI**: Identified an idiomatic FastAPI optimization that simplifies manual parsing logic. |
| **Comprehensive Test Coverage** | Added 10 tests: gaps in streak, same-day duplicate check-ins, cross-habit isolation, and year/month boundary traversal. | Praised year boundary and cross-habit tests; verified test coverage. | **Human**: Designed and implemented test matrix for boundary conditions. |

### PR #2: Input Validation (`POST /habits` & `POST /habits/{id}/checkin`)

| Aspect / Topic | My Human Manual Review | AI Code Review | Evaluation & Outcome |
|---|---|---|---|
| **Regex End-of-String Anchors (`\A` / `\Z`)** | Discovered during test execution that `^...$` allows trailing newlines (`2026-09-22\n`) because `$` matches before newline; replaced with `\A` and `\Z`. | Explicitly highlighted and applauded the `\A` and `\Z` catch, noting it blocks sneaky trailing newline bypasses. | **Human**: Caught by running dynamic tests; AI verified and explained the security implication statically. |
| **ASCII vs Unicode Digits (`[0-9]` vs `\d`)** | Hand-tested non-ASCII numerals (`٢٠٢٦-٠٩-٢٢`, `２０２６-０９-２２`); changed regex from `\d` to `[0-9]`. | Confirmed that `[0-9]` prevents Unicode digit confusion that standard regex `\d` permits. | **Tie**: Human implemented and verified; AI provided static confirmation. |
| **Zero-Width / Invisible Character Exploits** | Realized `\u200b`, `\ufeff`, and `\u2060` bypass standard `.strip()`; added regex sanitization. | Praised protection against invisible character exploits in user interfaces. | **Human**: Found subtle UI bypass vector and fixed it. |
| **Ruff Exception Typing (`TRY004`)** | Replaced `ValueError` with `TypeError` when checking input type to satisfy linter rule. | Noted strict compliance with Ruff static analysis standards. | **Human + Guardrail**: Linter flagged the issue; human applied the fix. |
| **Database Immutability** | Asserted in tests that SQLite row counts remain 0 after rejected validation requests. | Highlighted database immutability testing as a best practice against orphaned data. | **Human**: Wrote regression assertions verifying clean DB state. |

---

## 4. What I Learned

Deterministic guardrails and LLM code reviews operate at fundamentally complementary layers of software engineering. Tools like `black`, `ruff`, and `pytest` deliver immediate, binary, and infallible verdicts on formatting, static syntax, and known test contracts, acting as an indispensable gatekeeper that prevents trivial errors from wasting review time. In contrast, an AI reviewer excels at spotting structural blind spots, suggesting framework-native idioms (such as FastAPI date query parsing), and analyzing edge-case implications. However, because static AI reviews cannot execute code, they can overlook runtime subtleties like regex newline matching or accidental test passes. Going forward, my heuristic is to always let deterministic guardrails enforce baseline correctness first, using AI reviews as an inquisitive second pair of eyes whose findings must be verified against reproducible tests.
