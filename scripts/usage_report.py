"""Print chatbot usage metrics: who is using it and how much.

Reads the chat_users / chat_usage tables that backend/rag/quota.py keeps in
Aurora (one row per email, and one per email per day). Run it in CloudShell
after `source scripts/cloudshell_setup.sh`:

    python scripts/usage_report.py            # last 14 days, top 15 users
    python scripts/usage_report.py --days 30 --top 50
    python scripts/usage_report.py --csv usage.csv   # per-email-per-day rows

The cluster may be paused; the first query waits up to ~30s for it to resume.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from aws.stack_outputs import load_stack_outputs_into_env  # noqa: E402


def _query(db, sql, params=()):
    rows = db.execute_query(sql, params, fetch=True)
    if rows is None:
        sys.exit("Query failed. Has anyone asked a question since the usage tables were added?")
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--days", type=int, default=14, help="How many recent days to show.")
    parser.add_argument("--top", type=int, default=15, help="How many top users to list.")
    parser.add_argument("--csv", help="Also write per-email-per-day rows for the period to this CSV file.")
    args = parser.parse_args()

    load_stack_outputs_into_env()
    from database.rds_data_client import RdsDataApiManager

    with RdsDataApiManager() as db:
        if not db.ping(wait_seconds=30):
            sys.exit("Could not reach the database (still resuming?). Try again in a minute.")

        totals = _query(
            db,
            "SELECT count(*) AS users, coalesce(sum(total_questions), 0) AS questions, "
            "min(first_seen)::date AS since FROM chat_users",
        )[0]
        print(f"All time: {totals['users']} users, {totals['questions']} questions (since {totals['since']})\n")

        print(f"Last {args.days} days (US Central dates)")
        print(f"{'date':<12}{'users':>7}{'questions':>11}{'at limit':>10}")
        daily = _query(
            db,
            "SELECT u.usage_date::text AS day, count(*) AS users, sum(u.questions) AS questions, "
            "count(*) FILTER (WHERE u.questions >= %s) AS at_limit "
            "FROM chat_usage u WHERE u.usage_date > current_date - %s "
            "GROUP BY u.usage_date ORDER BY u.usage_date DESC",
            (int(_daily_limit()), args.days),
        )
        for row in daily:
            print(f"{row['day']:<12}{row['users']:>7}{row['questions']:>11}{row['at_limit']:>10}")
        if not daily:
            print("(no questions in this period)")

        print(f"\nTop {args.top} users in the last {args.days} days")
        top = _query(
            db,
            "SELECT email, sum(questions) AS questions, count(*) AS active_days, max(usage_date)::text AS last_day "
            "FROM chat_usage WHERE usage_date > current_date - %s "
            "GROUP BY email ORDER BY questions DESC LIMIT %s",
            (args.days, args.top),
        )
        for row in top:
            print(f"{row['questions']:>6}  {row['active_days']:>3} days  last {row['last_day']}  {row['email']}")

        if args.csv:
            rows = _query(
                db,
                "SELECT usage_date::text AS day, email, questions FROM chat_usage "
                "WHERE usage_date > current_date - %s ORDER BY usage_date DESC, questions DESC",
                (args.days,),
            )
            with open(args.csv, "w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=["day", "email", "questions"])
                writer.writeheader()
                writer.writerows(rows)
            print(f"\nWrote {len(rows)} rows to {args.csv}")


def _daily_limit() -> int:
    sys.path.insert(0, str(ROOT / "backend" / "rag"))
    from quota import DAILY_QUESTION_LIMIT

    return DAILY_QUESTION_LIMIT


if __name__ == "__main__":
    main()
