# Usage metrics and the daily question limit

## How it works

- The chat asks for an email address (after showing the privacy notice) before
  the first question. It is stored in the browser and sent with every question.
- `POST /ask` and `POST /ask/stream` reject a request without a valid email
  (HTTP 422/400).
- Each email can ask **100 questions per day** (US Central calendar day).
  Greetings and "what can you do?" are free. Question 101 gets a polite
  "daily limit reached" message instead of an answer, and the chat disables
  its input until the next day.
- Counting is atomic in the database, so parallel requests cannot overshoot
  the limit.
- If the usage tables cannot be updated (any database error other than the
  cluster still resuming), the question is **allowed** and the failure is
  logged (`quota: usage update failed`), rather than locking everyone out.

Code: `backend/rag/quota.py` (limit and tables), `backend/rag/ask.py`
(`_consume_quota`), `frontend/src/components/chat/WelcomeGate.tsx` (email
screen), `frontend/src/components/chat/data.ts` (privacy notice text).

### Settings

| Environment variable (Lambda) | Default | Meaning |
|---|---|---|
| `DAILY_QUESTION_LIMIT` | `100` | Questions per email per day |
| `QUOTA_TIMEZONE` | `America/Chicago` | Time zone that defines "a day" |

If you change the limit, also change `DAILY_QUESTION_LIMIT` in
`frontend/src/components/chat/data.ts` (used in the privacy text and footer).

### Limits of this protection

The email is **not verified**, so someone determined can invent a new
address to get another 100 questions. The CloudFront WAF rule (500 `/ask`
requests per 5 minutes per IP) remains the backstop against automated abuse,
and the AWS Budgets alerts flag unusual Bedrock spend. If abuse shows up in
the metrics, the next step is email verification (a one-time code by email,
e.g. Amazon Cognito or SES), which needs SES production access from the
account admin.

## Where the data lives

Two tables in the Aurora database `ciroh` (created automatically on first
use, also in `backend/database/schema_aws.sql`):

| Table | One row per | Columns |
|---|---|---|
| `chat_users` | email | `email`, `first_seen`, `last_seen`, `total_questions` |
| `chat_usage` | email per day | `email`, `usage_date`, `questions` |

Question text is **not** stored here. It appears only in the Lambda log
groups (`/ciroh-docuhub/ciroh-docuhub-ask` and `.../ciroh-docuhub-ask-stream`,
`TELEMETRY` lines), which keep logs for 30 days. Emails are not written to
the logs.

## Viewing the metrics

In CloudShell, after the usual setup (`cd ~/ciroh && source scripts/cloudshell_setup.sh`):

```bash
python scripts/usage_report.py                  # last 14 days + top 15 users
python scripts/usage_report.py --days 30 --top 50
python scripts/usage_report.py --csv usage.csv  # per-email-per-day rows
```

Example output:

```
All time: 42 users, 913 questions (since 2026-10-13)

Last 14 days (US Central dates)
date          users  questions  at limit
2026-10-20       11         87         0
...

Top 15 users in the last 14 days
   140   6 days  last 2026-10-20  someone@ua.edu
```

Or query directly in the RDS console's Query Editor (database `ciroh`,
secret `CIROH-DocuHub/aurora/master`), e.g.:

```sql
SELECT usage_date, count(*) AS users, sum(questions) AS questions
FROM chat_usage GROUP BY usage_date ORDER BY usage_date DESC LIMIT 30;
```

## Removing someone's data

```sql
DELETE FROM chat_usage WHERE email = 'person@example.edu';
DELETE FROM chat_users WHERE email = 'person@example.edu';
```
