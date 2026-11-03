"""Local human-review record store. Approval never triggers remediation."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

_DDL = """
CREATE TABLE IF NOT EXISTS recommendation_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id TEXT NOT NULL,
    decision TEXT NOT NULL CHECK(decision IN ('APPROVED', 'REJECTED')),
    reviewer TEXT NOT NULL,
    note TEXT NOT NULL,
    reviewed_at TEXT NOT NULL
);
"""


def _connect(path: str | Path) -> sqlite3.Connection:
    if str(path) != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.execute(_DDL)
    return connection


def add_review(
    path: str | Path, report_id: str, decision: str, reviewer: str, note: str
) -> None:
    """Persist a HUMAN recommendation review only, never an operational authorization."""
    if decision not in ("APPROVED", "REJECTED"):
        raise ValueError("Review decision must be APPROVED or REJECTED")
    if not report_id.strip() or not reviewer.strip():
        raise ValueError("Report ID and named human reviewer are required")
    if not note.strip():
        raise ValueError("A rationale is required to create an auditable review")
    with _connect(path) as connection:
        connection.execute(
            """INSERT INTO recommendation_reviews
               (report_id, decision, reviewer, note, reviewed_at)
               VALUES (?, ?, ?, ?, ?)""",
            (
                report_id.strip(),
                decision,
                reviewer.strip(),
                note.strip(),
                datetime.now(timezone.utc).isoformat(),
            ),
        )


def get_reviews(path: str | Path, report_id: str) -> list[dict[str, str]]:
    with _connect(path) as connection:
        rows = connection.execute(
            """SELECT decision, reviewer, note, reviewed_at
               FROM recommendation_reviews WHERE report_id = ?
               ORDER BY id DESC""",
            (report_id,),
        ).fetchall()
    return [
        {"decision": row[0], "reviewer": row[1], "note": row[2], "reviewed_at": row[3]}
        for row in rows
    ]
