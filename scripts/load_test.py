"""Concurrent-load test for the running Careerly API, against the real dev database.

Creates a handful of throwaway users (like .claude/skills/run-cv-platform/smoke.py), then
fires many concurrent requests at DB-backed endpoints for a fixed duration and reports
latency percentiles and error rate per endpoint. Deletes the throwaway users afterwards.

Deliberately NEVER calls a Claude-backed endpoint (anything under /tools or /profile/cv-prefill):
those are pay-per-token, and hammering them concurrently would spend real money for no reason
when the thing we actually want to test - whether the API and its unpooled DB connections
(see database/db_client.py get_connection) hold up under concurrent traffic - doesn't require it.
A SAFE_PATHS allowlist below enforces this even if someone adds targets later.

Usage (repo root, API already running via start.sh):
    ./venv/Scripts/python scripts/load_test.py
    ./venv/Scripts/python scripts/load_test.py --concurrency 50 --duration 20
    ./venv/Scripts/python scripts/load_test.py --host http://localhost:8000
"""
import argparse
import asyncio
import logging
import random
import statistics
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from database.db_client import get_connection  # noqa: E402

# db_client calls logging.basicConfig(INFO) on import, which would log every request below.
logging.getLogger("httpx").setLevel(logging.WARNING)

PASSWORD = "password123"
NUM_USERS = 5  # signup is rate-limited to 10 requests/5min per IP; stay well under that

# Only DB-backed endpoints. Never add a /tools/* or /profile/cv-prefill path here.
SAFE_PATHS = [
    ("GET", "/health"),
    ("GET", "/auth/me"),
    ("GET", "/profile"),
    ("GET", "/profile/all"),
    ("GET", "/profile/history"),
]
CLAUDE_PATH_MARKERS = ("/tools", "/cv-prefill")


def _assert_no_claude_paths():
    for _, path in SAFE_PATHS:
        if any(marker in path for marker in CLAUDE_PATH_MARKERS):
            sys.exit(f"Refusing to run: '{path}' looks like a Claude-backed endpoint.")


async def _setup_users(client: httpx.AsyncClient, n: int, emails: list[str]) -> list[dict]:
    """Appends each email to `emails` as soon as it's signed up, before creating its profile,
    so the caller's cleanup still finds and deletes it even if a later step raises."""
    stamp = int(time.time())
    tokens = []
    for i in range(n):
        email = f"loadtest-{stamp}-{i}@example.com"
        emails.append(email)
        r = await client.post(
            "/auth/signup",
            json={"email": email, "password": PASSWORD, "display_name": "Load Test", "consent": True},
        )
        r.raise_for_status()
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        (await client.post("/profile", json={"target_role": "Engineer", "label": "load test"}, headers=headers)).raise_for_status()
        tokens.append(headers)
    return tokens


def _cleanup_users(emails: list[str]) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE email = ANY(%s);", (emails,))
    print(f"\ncleanup: deleted {cur.rowcount} load-test user(s)")
    conn.commit()
    cur.close()
    conn.close()


async def _worker(client: httpx.AsyncClient, tokens: list[dict], deadline: float, results: list[tuple[str, float, int]]) -> None:
    while time.monotonic() < deadline:
        method, path = random.choice(SAFE_PATHS)
        headers = random.choice(tokens) if path != "/health" else {}
        start = time.monotonic()
        try:
            r = await client.request(method, path, headers=headers)
            status_code = r.status_code
        except httpx.HTTPError:
            status_code = -1
        elapsed_ms = (time.monotonic() - start) * 1000
        results.append((path, elapsed_ms, status_code))


def _percentile(values: list[float], pct: float) -> float:
    return statistics.quantiles(values, n=100)[int(pct) - 1] if len(values) > 1 else values[0]


def _report(results: list[tuple[str, float, int]], wall_seconds: float) -> bool:
    print(f"\n{len(results)} requests in {wall_seconds:.1f}s ({len(results) / wall_seconds:.1f} req/s)\n")
    header = f"{'endpoint':22} {'count':>6} {'errors':>7} {'p50 ms':>8} {'p95 ms':>8} {'max ms':>8}"
    print(header)
    print("-" * len(header))
    all_ok = True
    by_path: dict[str, list[tuple[float, int]]] = {}
    for path, elapsed_ms, status_code in results:
        by_path.setdefault(path, []).append((elapsed_ms, status_code))
    for path, rows in sorted(by_path.items()):
        latencies = [ms for ms, _ in rows]
        errors = sum(1 for _, code in rows if code < 200 or code >= 400)
        if errors:
            all_ok = False
        print(
            f"{path:22} {len(rows):>6} {errors:>7} "
            f"{_percentile(latencies, 50):>8.1f} {_percentile(latencies, 95):>8.1f} {max(latencies):>8.1f}"
        )
    return all_ok


async def main(host: str, concurrency: int, duration: float) -> bool:
    _assert_no_claude_paths()
    async with httpx.AsyncClient(base_url=host, timeout=30) as client:
        try:
            (await client.get("/health")).raise_for_status()
        except httpx.HTTPError as e:
            sys.exit(f"API not reachable at {host} ({e}). Run start.sh first.")

        emails: list[str] = []
        try:
            tokens = await _setup_users(client, NUM_USERS, emails)
            print(f"Load testing {host} with {concurrency} concurrent workers for {duration:.0f}s ...")
            results: list[tuple[str, float, int]] = []
            deadline = time.monotonic() + duration
            start = time.monotonic()
            await asyncio.gather(*(_worker(client, tokens, deadline, results) for _ in range(concurrency)))
            wall_seconds = time.monotonic() - start
        finally:
            if emails:
                _cleanup_users(emails)

    return _report(results, wall_seconds)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="http://localhost:8000")
    parser.add_argument("--concurrency", type=int, default=20)
    parser.add_argument("--duration", type=float, default=15.0)
    args = parser.parse_args()

    ok = asyncio.run(main(args.host, args.concurrency, args.duration))
    print("\nALL OK" if ok else "\nSOME REQUESTS FAILED (see errors column above)")
    sys.exit(0 if ok else 1)
