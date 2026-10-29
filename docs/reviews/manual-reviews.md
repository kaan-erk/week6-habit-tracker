# Manual Code Review Notes

Author: Kaan Erk Toraman (220901564)

## PR #1: Streak Endpoint (`GET /habits/{id}/streak`)

### Initial Agent Implementation Assessment
The agent generated a working endpoint in a single prompt:
- Connected to SQLite, verified habit ID, fetched `day` from checkins, and walked backwards from `date.today()`.
- Added 3 baseline tests in `test_main.py`.

### Line-by-Line Manual Review Findings
1. **Server Clock Coupling & Midnight Race Conditions**:
   `current_day = date.today()` binds the logic to server timezone. If an automated test suite or user runs at 23:59:59, tests could cross midnight and fail intermittently.
   - *Fix applied:* Added optional `today: str | None = Query(...)` parameter with ISO format validation (raising 422 if malformed). Defaults to `date.today()`.
2. **Missing Pydantic Response Model**:
   FastAPI best practice recommends explicit response contracts for OpenAPI documentation and response serialization.
   - *Fix applied:* Created `StreakOut(BaseModel)` with `habit_id: int` and `streak: int`.
3. **Database Query Efficiency**:
   The query `SELECT day FROM checkins WHERE habit_id = ?` loads duplicate check-in records into memory.
   - *Fix applied:* Switched to `SELECT DISTINCT day FROM checkins WHERE habit_id = ?`.
4. **Test Suite Blindspots**:
   The agent's test suite did not test:
   - Check-ins separated by a gap (e.g. today checked in, yesterday missed, 2 days ago checked in -> streak must be 1).
   - Duplicate check-ins on the same calendar day (must only contribute 1 to the streak).
   - Checking in yesterday but NOT today (returns streak 0 per spec).
   - Cross-habit check-in isolation.
   - Month/Year boundary crossing (e.g. Jan 1 to Dec 31).
   - *Fix applied:* Wrote 10 dedicated edge-case test cases in `test_main.py`.

---

## PR #2: Input Validation (`POST /habits` & `POST /habits/{id}/checkin`)

### Initial Agent Implementation Assessment
The agent introduced Pydantic field validators with basic string `.strip()` and `date.fromisoformat()`.

### Line-by-Line Manual Review Findings
1. **`date.fromisoformat()` Quirks on Python 3.11+**:
   `date.fromisoformat()` does not strictly require `YYYY-MM-DD`. It permits basic ISO (`20260922`), ISO week dates (`2026-W39-2`), and `+2026-09-22`. When stored, these non-standard strings break exact string lookups used in streak calculation!
   - *Fix applied:* Enforced strict regex matching `\A[0-9]{4}-[0-9]{2}-[0-9]{2}\Z` before calendar date parsing.
2. **Regex Trailing Newline Vulnerability**:
   When using `^...$`, regex allows trailing newlines (`2026-09-22\n`) because `$` matches before a trailing newline.
   - *Fix applied:* Replaced `^...$` with `\A...\Z` (strict start and end of string).
3. **Unicode Digit Bypass**:
   `\d` in Python regex matches non-ASCII digits (such as Arabic-Indic `٢٠٢٦-٠٩-٢٢` or full-width `２０２６-０９-２２`).
   - *Fix applied:* Replaced `\d` with explicit ASCII `[0-9]`.
4. **Invisible / Zero-Width Unicode Characters**:
   Habit names containing only zero-width characters (e.g., `\u200b`, `\ufeff`, `\u2060`) passed standard `strip()`, allowing visually empty habits.
   - *Fix applied:* Sanitized invisible Unicode characters using regex before checking length.
5. **Ruff TRY004 Linter Rule**:
   Ruff flagged raising `ValueError` when checking `isinstance(v, str)`.
   - *Fix applied:* Changed exception to `TypeError` to satisfy Ruff TRY004.
6. **Database Immutability Verification**:
   - *Fix applied:* Added tests explicitly checking that SQLite table row count remains 0 after validation failures.
