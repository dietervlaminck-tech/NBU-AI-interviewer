import sqlite3
import json
import uuid
import os
from datetime import datetime, timezone

# Use /tmp on Vercel (serverless, ephemeral filesystem) or ./data locally
if os.environ.get("VERCEL"):
    DB_PATH = "/tmp/interviews.db"
else:
    DB_PATH = os.path.join(os.path.dirname(__file__), "data", "interviews.db")


def get_db():
    db_dir = os.path.dirname(DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS studies (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            research_question TEXT NOT NULL,
            interview_outline TEXT NOT NULL,
            general_instructions TEXT NOT NULL DEFAULT '',
            model TEXT NOT NULL DEFAULT 'claude-sonnet-4-20250514',
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            study_id TEXT NOT NULL REFERENCES studies(id),
            respondent_name TEXT NOT NULL DEFAULT '',
            messages TEXT NOT NULL DEFAULT '[]',
            status TEXT NOT NULL DEFAULT 'active',
            started_at TEXT NOT NULL,
            completed_at TEXT,
            duration_seconds REAL DEFAULT 0
        );
    """)
    conn.commit()
    conn.close()


def create_study(title, research_question, interview_outline, general_instructions="", model="claude-sonnet-4-20250514"):
    study_id = uuid.uuid4().hex[:12]
    conn = get_db()
    conn.execute(
        "INSERT INTO studies (id, title, research_question, interview_outline, general_instructions, model, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (study_id, title, research_question, interview_outline, general_instructions, model, datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    conn.close()
    return study_id


def get_study(study_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM studies WHERE id = ?", (study_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def list_studies():
    conn = get_db()
    rows = conn.execute("SELECT * FROM studies ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def create_session(study_id, respondent_name=""):
    session_id = uuid.uuid4().hex[:16]
    conn = get_db()
    conn.execute(
        "INSERT INTO sessions (id, study_id, respondent_name, messages, status, started_at) VALUES (?, ?, ?, '[]', 'active', ?)",
        (session_id, study_id, respondent_name, datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    conn.close()
    return session_id


def get_session(session_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    d["messages"] = json.loads(d["messages"])
    return d


def update_session_messages(session_id, messages):
    conn = get_db()
    conn.execute(
        "UPDATE sessions SET messages = ? WHERE id = ?",
        (json.dumps(messages), session_id),
    )
    conn.commit()
    conn.close()


def complete_session(session_id):
    conn = get_db()
    started = conn.execute("SELECT started_at FROM sessions WHERE id = ?", (session_id,)).fetchone()
    duration = 0
    if started:
        start = datetime.fromisoformat(started["started_at"])
        duration = (datetime.now(timezone.utc) - start).total_seconds()
    conn.execute(
        "UPDATE sessions SET status = 'completed', completed_at = ?, duration_seconds = ? WHERE id = ?",
        (datetime.now(timezone.utc).isoformat(), duration, session_id),
    )
    conn.commit()
    conn.close()


def get_sessions_for_study(study_id):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM sessions WHERE study_id = ? ORDER BY started_at DESC", (study_id,)
    ).fetchall()
    conn.close()
    results = []
    for r in rows:
        d = dict(r)
        d["messages"] = json.loads(d["messages"])
        results.append(d)
    return results


def delete_study(study_id):
    conn = get_db()
    conn.execute("DELETE FROM sessions WHERE study_id = ?", (study_id,))
    conn.execute("DELETE FROM studies WHERE id = ?", (study_id,))
    conn.commit()
    conn.close()
