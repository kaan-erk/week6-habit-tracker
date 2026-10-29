from contextlib import closing

import pytest
from fastapi.testclient import TestClient

from main import DB_PATH, app, get_db, init_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    if DB_PATH.exists():
        DB_PATH.unlink()
    init_db()
    yield
    if DB_PATH.exists():
        DB_PATH.unlink()


def test_create_and_list_habit():
    r = client.post("/habits", json={"name": "Read 20 minutes"})
    assert r.status_code == 200
    hid = r.json()["id"]
    r2 = client.get("/habits")
    assert r2.status_code == 200
    assert any(h["id"] == hid for h in r2.json())


def test_checkin_flow():
    hid = client.post("/habits", json={"name": "Stretch"}).json()["id"]
    r = client.post(f"/habits/{hid}/checkin", json={"day": "2026-09-22"})
    assert r.status_code == 200
    r2 = client.get(f"/habits/{hid}/checkins")
    assert r2.json() == ["2026-09-22"]


def test_checkin_unknown_habit_404():
    r = client.post("/habits/99999/checkin", json={"day": "2026-09-22"})
    assert r.status_code == 404


# ==============================================================================
# HABIT NAME VALIDATION TESTS
# ==============================================================================


@pytest.mark.parametrize(
    "invalid_name",
    [
        "",  # Empty string
        "   ",  # Whitespace only
        "\t\n  \r",  # Mixed whitespace
        "\u200b\u200c\u200d",  # Zero-width spaces / joiners
        "\ufeff\u2060",  # Byte order mark and word joiner
    ],
)
def test_create_habit_rejects_empty_or_invisible_names(invalid_name):
    r = client.post("/habits", json={"name": invalid_name})
    assert r.status_code == 422
    assert "invisible" in r.text or "empty" in r.text

    # Verify nothing was saved to database
    with closing(get_db()) as conn:
        count = conn.execute("SELECT count(*) FROM habits").fetchone()[0]
        assert count == 0


def test_create_habit_trims_whitespace():
    r = client.post("/habits", json={"name": "   Meditate daily   "})
    assert r.status_code == 200
    assert r.json()["name"] == "Meditate daily"

    # Verify trimmed name is stored in DB and listed
    r2 = client.get("/habits")
    assert r2.json()[0]["name"] == "Meditate daily"


def test_create_habit_length_bounds():
    # 100 characters: valid boundary
    name_100 = "A" * 100
    r = client.post("/habits", json={"name": name_100})
    assert r.status_code == 200
    assert r.json()["name"] == name_100

    # 101 characters: rejected boundary
    name_101 = "B" * 101
    r_bad = client.post("/habits", json={"name": name_101})
    assert r_bad.status_code == 422
    assert "100 characters" in r_bad.text


# ==============================================================================
# CHECK-IN DAY VALIDATION TESTS
# ==============================================================================


@pytest.mark.parametrize(
    "malformed_day",
    [
        "2026-9-22",  # Missing leading zero in month
        "2026-09-2",  # Missing leading zero in day
        "2026/09/22",  # Slash delimiters
        "22-09-2026",  # Reversed day-month-year
        "tomorrow",  # Natural language
        "20260922",  # Basic ISO (no hyphens) accepted by date.fromisoformat on 3.11+
        "2026-W39-2",  # ISO week date accepted by date.fromisoformat on 3.11+
        "+2026-09-22",  # Leading plus sign
        "2026-09-22\n",  # Trailing newline
        " 2026-09-22 ",  # Leading/trailing whitespace
        "٢٠٢٦-٠٩-٢٢",  # Arabic-Indic non-ASCII digits (matches \d in regex without [0-9])
        "２０２６-０９-２２",  # Full-width Unicode digits
    ],
)
def test_checkin_rejects_malformed_day_formats(malformed_day):
    hid = client.post("/habits", json={"name": "Workout"}).json()["id"]
    r = client.post(f"/habits/{hid}/checkin", json={"day": malformed_day})
    assert r.status_code == 422
    assert "YYYY-MM-DD" in r.text or "ASCII digits" in r.text

    # Verify no checkin row was stored
    r2 = client.get(f"/habits/{hid}/checkins")
    assert r2.json() == []


@pytest.mark.parametrize(
    "invalid_calendar_day",
    [
        "2026-02-30",  # February 30th does not exist
        "2026-04-31",  # April only has 30 days
        "2026-13-01",  # Month 13 does not exist
        "2026-00-10",  # Month 0 does not exist
        "2026-05-00",  # Day 0 does not exist
        "2026-05-32",  # Day 32 does not exist
        "2025-02-29",  # 2025 is not a leap year
    ],
)
def test_checkin_rejects_impossible_calendar_dates(invalid_calendar_day):
    hid = client.post("/habits", json={"name": "Reading"}).json()["id"]
    r = client.post(f"/habits/{hid}/checkin", json={"day": invalid_calendar_day})
    assert r.status_code == 422
    assert "not a valid calendar date" in r.text


def test_checkin_accepts_leap_year_feb_29():
    hid = client.post("/habits", json={"name": "Leap day run"}).json()["id"]
    # 2024 is a leap year
    r = client.post(f"/habits/{hid}/checkin", json={"day": "2024-02-29"})
    assert r.status_code == 200
    assert r.json() == {"habit_id": hid, "day": "2024-02-29"}
