"""End-to-end test of the deployed chatbot, through CloudFront, like a browser.

Checks that a question without an email is refused, streams one answer from
/ask/stream (the path the chat uses), sends a few on-topic questions and one
off-topic question to /ask, and reports status, latency, route and sources.
Questions are counted against --email's daily limit like any user's.
The site URL is read from the CirohStack outputs (needs AWS credentials),
or pass it with --url.

Usage:
    python scripts/smoke_test.py
    python scripts/smoke_test.py --url https://dxxxxxxxxxxxx.cloudfront.net
    python scripts/smoke_test.py --question "How do I install NGIAB?"

Run automatically after every CI deploy (.github/workflows/deploy.yml).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_QUESTIONS = [
    "What is NextGen In A Box?",
    "How do I get access to CIROH cloud computing resources?",
]
OFF_TOPIC_QUESTION = "Write me a Python script that reverses a linked list."
# Shows up in scripts/usage_report.py like a user; the .invalid domain can
# never be a real mailbox.
DEFAULT_EMAIL = "smoke-test@ciroh-docuhub.invalid"
# API Gateway cuts requests off at ~30s; answers should land well under that.
SLOW_SECONDS = 20


def _frontend_url() -> str:
    sys.path.insert(0, str(REPO_ROOT / "backend"))
    from aws.stack_outputs import get_stack_outputs

    return get_stack_outputs()["FrontendUrl"]


def _request(url: str, payload: dict) -> urllib.request.Request:
    data = json.dumps(payload).encode()
    return urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "ciroh-smoke-test",
            # Required by CloudFront's signed access to the streaming Lambda.
            "x-amz-content-sha256": hashlib.sha256(data).hexdigest(),
        },
        method="POST",
    )


def _stream(url: str, payload: dict, timeout: int = 120) -> tuple[int, list[dict], float, float | None]:
    """POST to the streaming endpoint; returns (status, events, total_s, first_text_s)."""
    started = time.time()
    first_text = None
    events: list[dict] = []
    try:
        with urllib.request.urlopen(_request(url, payload), timeout=timeout) as resp:
            for raw in resp:
                line = raw.decode().strip()
                if not line:
                    continue
                event = json.loads(line)
                events.append(event)
                if event.get("type") == "delta" and first_text is None:
                    first_text = time.time() - started
            status = resp.status
    except urllib.error.HTTPError as e:
        status = e.code
    return status, events, time.time() - started, first_text


def _post(url: str, payload: dict, timeout: int = 60) -> tuple[int, dict | str, float]:
    req = _request(url, payload)
    started = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode()
            status = resp.status
    except urllib.error.HTTPError as e:
        body, status = e.read().decode(errors="replace"), e.code
    elapsed = time.time() - started
    try:
        return status, json.loads(body), elapsed
    except json.JSONDecodeError:
        return status, body[:300], elapsed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--url", help="Site URL (default: CirohStack's FrontendUrl output)")
    parser.add_argument("--question", action="append", help="Question to ask (repeatable)")
    parser.add_argument("--email", default=DEFAULT_EMAIL, help=f"Email to ask as (default: {DEFAULT_EMAIL})")
    args = parser.parse_args()

    base = (args.url or _frontend_url()).rstrip("/")
    print(f"Testing {base}\n")

    failures = 0

    # Same call the chat panel makes when opened: wakes Aurora if it paused.
    status, _body, _ = _post(f"{base}/telemetry", {"session_id": "smoke-test", "event": "chat_open"})
    print(f"[{'OK' if status == 200 else 'FAIL'}] /telemetry -> HTTP {status}")
    failures += status != 200
    if status == 200:
        print("      waiting 20s for the database to wake up...")
        time.sleep(20)

    status, _body, _ = _post(f"{base}/ask", {"text": DEFAULT_QUESTIONS[0]})
    ok = status == 422
    failures += not ok
    print(f"\n[{'OK' if ok else 'FAIL'}] a question without an email is refused (HTTP {status}, expected 422)")

    question = (args.question or DEFAULT_QUESTIONS)[0]
    status, events, elapsed, first_text = _stream(f"{base}/ask/stream", {"text": question, "email": args.email})
    done = next((e for e in events if e.get("type") == "done"), None)
    deltas = sum(e.get("type") == "delta" for e in events)
    ok = status == 200 and done is not None and deltas > 1 and done.get("route") not in ("rejected", "unavailable")
    failures += not ok
    print(f"\n[{'OK' if ok else 'FAIL'}] streaming: {question}")
    first = f"{first_text:.1f}s" if first_text is not None else "never"
    print(f"      HTTP {status}, first words after {first}, done after {elapsed:.1f}s, {deltas} pieces")
    if done:
        print(f"      route: {done.get('route')}, quota: {done.get('quota')}")
        print(f"      follow-ups: {done.get('follow_ups')}")

    for question in args.question or DEFAULT_QUESTIONS:
        status, body, elapsed = _post(f"{base}/ask", {"text": question, "email": args.email})
        ok = status == 200 and isinstance(body, dict) and body.get("route") not in (None, "rejected")
        failures += not ok
        print(f"\n[{'OK' if ok else 'FAIL'}] {question}")
        print(f"      HTTP {status} in {elapsed:.1f}s{'  (slow!)' if elapsed > SLOW_SECONDS else ''}")
        if isinstance(body, dict):
            print(f"      route: {body.get('route')}")
            print(f"      answer: {(body.get('answer') or '')[:300]}")
            for title, link in list(zip(body.get("sources", []), body.get("links", [])))[:3]:
                print(f"      source: {title}  {link}")
        else:
            print(f"      body: {body}")

    status, body, elapsed = _post(f"{base}/ask", {"text": OFF_TOPIC_QUESTION, "email": args.email})
    refused = status == 200 and isinstance(body, dict) and body.get("route") == "rejected"
    print(f"\n[{'OK' if refused else 'WARN'}] off-topic question is refused")
    print(f"      HTTP {status} in {elapsed:.1f}s, route: {body.get('route') if isinstance(body, dict) else body}")

    print("\nAll checks passed." if not failures else f"\n{failures} check(s) failed - see docs/AWS_DEPLOYMENT.md, Troubleshooting.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
