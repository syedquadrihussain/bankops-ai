import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "bankops.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS reviews (
    review_id TEXT PRIMARY KEY,
    question TEXT NOT NULL,
    results_json TEXT NOT NULL,
    review_status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    decided_at TEXT,
    reviewer TEXT
);

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    event TEXT NOT NULL,
    review_id TEXT NOT NULL,
    actor TEXT NOT NULL,
    detail TEXT
);

CREATE TRIGGER IF NOT EXISTS audit_log_no_update
BEFORE UPDATE ON audit_log
BEGIN
    SELECT RAISE(ABORT, 'audit_log is append-only');
END;

CREATE TRIGGER IF NOT EXISTS audit_log_no_delete
BEFORE DELETE ON audit_log
BEGIN
    SELECT RAISE(ABORT, 'audit_log is append-only');
END;
"""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _db_path() -> str:
    return os.getenv("BANKOPS_DB", str(DEFAULT_DB_PATH))


@contextmanager
def _connection():
    conn = sqlite3.connect(_db_path())
    conn.row_factory = sqlite3.Row
    try:
        conn.executescript(SCHEMA)
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _write_audit(conn, event: str, review_id: str, actor: str, detail=None):
    conn.execute(
        "INSERT INTO audit_log (created_at, event, review_id, actor, detail) "
        "VALUES (?, ?, ?, ?, ?)",
        (utc_now(), event, review_id, actor, detail),
    )


def _row_to_record(row) -> dict:
    return {
        "review_id": row["review_id"],
        "question": row["question"],
        "results": json.loads(row["results_json"]),
        "review_status": row["review_status"],
        "created_at": row["created_at"],
        "decided_at": row["decided_at"],
        "reviewer": row["reviewer"],
    }


def create_review(question: str, results: list) -> str:
    review_id = str(uuid4())
    with _connection() as conn:
        conn.execute(
            "INSERT INTO reviews (review_id, question, results_json, "
            "review_status, created_at) VALUES (?, ?, ?, 'pending_review', ?)",
            (review_id, question, json.dumps(results), utc_now()),
        )
        _write_audit(conn, "review_created", review_id, "system")
    return review_id


def get_review(review_id: str):
    with _connection() as conn:
        row = conn.execute(
            "SELECT * FROM reviews WHERE review_id = ?", (review_id,)
        ).fetchone()
    return None if row is None else _row_to_record(row)


def decide_review(review_id: str, new_status: str, reviewer: str):
    """Return (outcome, record). Outcome: decided, not_found, already_decided."""
    with _connection() as conn:
        cursor = conn.execute(
            "UPDATE reviews SET review_status = ?, reviewer = ?, decided_at = ? "
            "WHERE review_id = ? AND review_status = 'pending_review'",
            (new_status, reviewer, utc_now(), review_id),
        )
        row = conn.execute(
            "SELECT * FROM reviews WHERE review_id = ?", (review_id,)
        ).fetchone()
        if row is None:
            return "not_found", None
        if cursor.rowcount == 0:
            _write_audit(
                conn, "decision_refused", review_id, reviewer,
                "review already decided",
            )
            return "already_decided", None
        _write_audit(conn, "review_" + new_status, review_id, reviewer)
        return "decided", _row_to_record(row)


def get_audit_log(review_id: str) -> list:
    with _connection() as conn:
        rows = conn.execute(
            "SELECT created_at, event, actor, detail FROM audit_log "
            "WHERE review_id = ? ORDER BY id",
            (review_id,),
        ).fetchall()
    return [dict(row) for row in rows]
