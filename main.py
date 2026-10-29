"""Habit Tracker — starter app for Week 6.

A tiny FastAPI service for habits and daily check-ins. You'll add features on
branches, open PRs, and compare your manual review with an AI reviewer.

Run:
    pip install -r requirements.txt
    uvicorn main:app --reload
Test:
    pytest
"""

import re
import sqlite3
from contextlib import closing
from datetime import date
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator

DB_PATH = Path(__file__).parent / "habits.db"

app = FastAPI(title="Habit Tracker")

# Strict ISO calendar date: YYYY-MM-DD with ASCII-only digits
# We use [0-9] rather than \d to prevent matching Unicode/non-ASCII digits.
# We use \A and \Z rather than ^ and $ because $ matches before a trailing newline.
ISO_DATE_REGEX = re.compile(r"\A[0-9]{4}-[0-9]{2}-[0-9]{2}\Z")

# Invisible and zero-width characters that appear blank in user interfaces
INVISIBLE_CHARS_REGEX = re.compile(r"[\u200B-\u200D\uFEFF\u2060\u00A0]")


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with closing(get_db()) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS habits (
                id   INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS checkins (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                habit_id INTEGER NOT NULL,
                day      TEXT NOT NULL,
                FOREIGN KEY (habit_id) REFERENCES habits (id)
            )""")
        conn.commit()


init_db()


class HabitIn(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def validate_habit_name(cls, v: str) -> str:
        if not isinstance(v, str):
            raise TypeError("Habit name must be a string")
        # Strip whitespace and invisible zero-width characters
        cleaned = INVISIBLE_CHARS_REGEX.sub("", v).strip()
        if not cleaned:
            raise ValueError(
                "Habit name cannot be empty or contain only invisible characters"
            )
        if len(cleaned) > 100:
            raise ValueError("Habit name cannot exceed 100 characters")
        return cleaned


class CheckinIn(BaseModel):
    day: str  # Strictly formatted ISO calendar date: YYYY-MM-DD

    @field_validator("day")
    @classmethod
    def validate_checkin_day(cls, v: str) -> str:
        if not isinstance(v, str):
            raise TypeError("Day must be a string")
        # Strict ASCII YYYY-MM-DD regex check.
        # This is load-bearing: Python 3.11+ date.fromisoformat() also accepts
        # basic ISO (20260922) and ISO week dates (2026-W39-2), which break
        # string-based day lookups and streak calculations.
        if not ISO_DATE_REGEX.match(v):
            raise ValueError(
                "Day must strictly follow YYYY-MM-DD format with ASCII digits (e.g. '2026-09-22')"
            )
        try:
            date.fromisoformat(v)
        except ValueError:
            raise ValueError(
                f"'{v}' is not a valid calendar date (e.g. check month/day bounds or leap year)"
            )
        return v


@app.post("/habits")
def create_habit(habit: HabitIn):
    with closing(get_db()) as conn:
        cur = conn.execute("INSERT INTO habits (name) VALUES (?)", (habit.name,))
        conn.commit()
        return {"id": cur.lastrowid, "name": habit.name}


@app.get("/habits")
def list_habits():
    with closing(get_db()) as conn:
        rows = conn.execute("SELECT id, name FROM habits ORDER BY id").fetchall()
    return [dict(r) for r in rows]


@app.post("/habits/{habit_id}/checkin")
def add_checkin(habit_id: int, checkin: CheckinIn):
    with closing(get_db()) as conn:
        habit = conn.execute(
            "SELECT id FROM habits WHERE id = ?", (habit_id,)
        ).fetchone()
        if habit is None:
            raise HTTPException(status_code=404, detail="unknown habit")
        conn.execute(
            "INSERT INTO checkins (habit_id, day) VALUES (?, ?)",
            (habit_id, checkin.day),
        )
        conn.commit()
    return {"habit_id": habit_id, "day": checkin.day}


@app.get("/habits/{habit_id}/checkins")
def list_checkins(habit_id: int):
    with closing(get_db()) as conn:
        rows = conn.execute(
            "SELECT day FROM checkins WHERE habit_id = ? ORDER BY day",
            (habit_id,),
        ).fetchall()
    return [r["day"] for r in rows]
