from datetime import date

import pytest
from fastapi.testclient import TestClient

from main import DB_PATH, app, init_db

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


def test_streak_zero_when_no_checkins():
    hid = client.post("/habits", json={"name": "Meditate"}).json()["id"]
    r = client.get(f"/habits/{hid}/streak")
    assert r.status_code == 200
    assert r.json() == {"habit_id": hid, "streak": 0}


def test_streak_consecutive_days_with_anchor():
    hid = client.post("/habits", json={"name": "Walk 10k steps"}).json()["id"]
    anchor = "2026-10-15"
    days = ["2026-10-15", "2026-10-14", "2026-10-13"]
    for d in days:
        r = client.post(f"/habits/{hid}/checkin", json={"day": d})
        assert r.status_code == 200

    r = client.get(f"/habits/{hid}/streak?today={anchor}")
    assert r.status_code == 200
    assert r.json() == {"habit_id": hid, "streak": 3}


def test_streak_zero_if_checked_in_yesterday_but_not_today():
    """Per spec, streak is the current run of consecutive days up to and including today."""
    hid = client.post("/habits", json={"name": "Journaling"}).json()["id"]
    anchor = "2026-10-15"
    r = client.post(f"/habits/{hid}/checkin", json={"day": "2026-10-14"})
    assert r.status_code == 200

    r = client.get(f"/habits/{hid}/streak?today={anchor}")
    assert r.status_code == 200
    assert r.json()["streak"] == 0


def test_streak_broken_by_gap():
    hid = client.post("/habits", json={"name": "Code review"}).json()["id"]
    anchor = "2026-10-15"
    # Today checked in, yesterday missed, 2 days ago checked in -> streak is 1
    for d in ["2026-10-15", "2026-10-13"]:
        r = client.post(f"/habits/{hid}/checkin", json={"day": d})
        assert r.status_code == 200

    r = client.get(f"/habits/{hid}/streak?today={anchor}")
    assert r.status_code == 200
    assert r.json()["streak"] == 1


def test_streak_duplicate_checkins_counted_once():
    hid = client.post("/habits", json={"name": "Drink water"}).json()["id"]
    anchor = "2026-10-15"
    # Duplicate checkins on same days
    for d in ["2026-10-15", "2026-10-15", "2026-10-14", "2026-10-14"]:
        r = client.post(f"/habits/{hid}/checkin", json={"day": d})
        assert r.status_code == 200

    r = client.get(f"/habits/{hid}/streak?today={anchor}")
    assert r.status_code == 200
    assert r.json()["streak"] == 2


def test_streak_cross_habit_isolation():
    h1 = client.post("/habits", json={"name": "Habit 1"}).json()["id"]
    h2 = client.post("/habits", json={"name": "Habit 2"}).json()["id"]
    anchor = "2026-10-15"

    client.post(f"/habits/{h1}/checkin", json={"day": "2026-10-15"})
    client.post(f"/habits/{h2}/checkin", json={"day": "2026-10-15"})
    client.post(f"/habits/{h2}/checkin", json={"day": "2026-10-14"})

    r1 = client.get(f"/habits/{h1}/streak?today={anchor}")
    r2 = client.get(f"/habits/{h2}/streak?today={anchor}")
    assert r1.json()["streak"] == 1
    assert r2.json()["streak"] == 2


def test_streak_year_boundary_crossing():
    hid = client.post("/habits", json={"name": "Daily plank"}).json()["id"]
    anchor = "2026-01-02"
    for d in ["2026-01-02", "2026-01-01", "2025-12-31", "2025-12-30"]:
        r = client.post(f"/habits/{hid}/checkin", json={"day": d})
        assert r.status_code == 200

    r = client.get(f"/habits/{hid}/streak?today={anchor}")
    assert r.status_code == 200
    assert r.json()["streak"] == 4


def test_streak_malformed_today_param_422():
    hid = client.post("/habits", json={"name": "Run"}).json()["id"]
    r = client.get(f"/habits/{hid}/streak?today=invalid-date")
    assert r.status_code == 422


def test_streak_default_today_server_date():
    hid = client.post("/habits", json={"name": "Yoga"}).json()["id"]
    today = date.today().isoformat()
    client.post(f"/habits/{hid}/checkin", json={"day": today})
    r = client.get(f"/habits/{hid}/streak")
    assert r.status_code == 200
    assert r.json()["streak"] == 1


def test_streak_unknown_habit_404():
    r = client.get("/habits/99999/streak")
    assert r.status_code == 404
