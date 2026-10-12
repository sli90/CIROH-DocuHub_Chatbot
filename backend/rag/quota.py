"""Per-email daily question limit and usage metrics.

Every question to /ask or /ask/stream must carry the asker's email address.
Each email may ask DAILY_QUESTION_LIMIT questions per calendar day
(QUOTA_TIMEZONE, so the count resets at local midnight). This caps how much
one user can run up Bedrock token costs; the per-IP WAF rate limit on
CloudFront remains the backstop against someone cycling made-up addresses.

Two tables in the same Aurora database as the knowledge base double as the
usage metrics (see docs/USAGE_METRICS.md for queries):
  chat_users  - one row per email: first/last seen, lifetime question count
  chat_usage  - one row per email per day: questions asked that day

Only the email and the counts are stored here; question text is not.
"""

from __future__ import annotations

import os
import re
from typing import Optional

DAILY_QUESTION_LIMIT = int(os.getenv("DAILY_QUESTION_LIMIT", "100"))
QUOTA_TIMEZONE = os.getenv("QUOTA_TIMEZONE", "America/Chicago")

_EMAIL = re.compile(r"^[^@\s]{1,64}@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}$")

_DDL = (
    """CREATE TABLE IF NOT EXISTS chat_users (
        email TEXT PRIMARY KEY,
        first_seen TIMESTAMPTZ NOT NULL DEFAULT now(),
        last_seen TIMESTAMPTZ NOT NULL DEFAULT now(),
        total_questions INTEGER NOT NULL DEFAULT 0
    )""",
    """CREATE TABLE IF NOT EXISTS chat_usage (
        email TEXT NOT NULL,
        usage_date DATE NOT NULL,
        questions INTEGER NOT NULL DEFAULT 0,
        PRIMARY KEY (email, usage_date)
    )""",
)

# Counts the question only while under the limit (the conditional DO UPDATE
# returns no row once the limit is reached), and records the user in the
# same statement. Atomic, so concurrent requests can't overshoot the limit.
_CONSUME_SQL = """
WITH bump AS (
    INSERT INTO chat_usage (email, usage_date, questions)
    VALUES (%s, (now() AT TIME ZONE %s)::date, 1)
    ON CONFLICT (email, usage_date)
    DO UPDATE SET questions = chat_usage.questions + 1
    WHERE chat_usage.questions < %s
    RETURNING questions
), seen AS (
    INSERT INTO chat_users (email, total_questions)
    SELECT %s, 1 FROM bump
    ON CONFLICT (email)
    DO UPDATE SET last_seen = now(), total_questions = chat_users.total_questions + 1
)
SELECT questions FROM bump
"""

_tables_ready = False


def normalize_email(raw: Optional[str]) -> Optional[str]:
    """Lower-cased, trimmed email, or None if it doesn't look like one."""
    if not raw:
        return None
    email = raw.strip().lower()
    if len(email) > 254 or not _EMAIL.match(email):
        return None
    return email


def _ensure_tables(db) -> None:
    global _tables_ready
    if _tables_ready:
        return
    for ddl in _DDL:
        db.execute_query(ddl)
    _tables_ready = True


def consume_question(db, email: str) -> dict:
    """Count one question against `email`'s daily limit.

    Returns {"allowed", "used", "limit", "remaining"}. If the usage tables
    can't be read (anything other than the database still resuming, which
    raises DatabaseUnavailableError), the question is allowed rather than
    locking everyone out; WAF still rate-limits per IP.
    """
    _ensure_tables(db)
    rows = db.execute_query(
        _CONSUME_SQL,
        (email, QUOTA_TIMEZONE, DAILY_QUESTION_LIMIT, email),
        fetch=True,
    )
    if rows is None:
        print("quota: usage update failed; allowing the question")
        return {"allowed": True, "used": None, "limit": DAILY_QUESTION_LIMIT, "remaining": None}
    if not rows:
        return {"allowed": False, "used": DAILY_QUESTION_LIMIT, "limit": DAILY_QUESTION_LIMIT, "remaining": 0}
    used = int(rows[0]["questions"])
    return {
        "allowed": True,
        "used": used,
        "limit": DAILY_QUESTION_LIMIT,
        "remaining": max(DAILY_QUESTION_LIMIT - used, 0),
    }
