"""Smoke-test the running Careerly API (and optionally the UI) against the real dev database.

Creates two throwaway users (smoketest-<role>-<stamp>@example.com), exercises auth, the
application tracker (including cross-user access) and input validation, then deletes the
users - every table cascades from users, so nothing is left behind. No Claude calls are made.

Usage (repo root, servers already running via start.sh):
    ./venv/Scripts/python .claude/skills/run-cv-platform/smoke.py          # API only
    ./venv/Scripts/python .claude/skills/run-cv-platform/smoke.py --ui     # + browser tracker flow
    ./venv/Scripts/python .claude/skills/run-cv-platform/smoke.py --ui dashboard profile
        # + log in and screenshot those pages instead of the tracker flow
        # (no leading slash: Git Bash rewrites "/dashboard" into a Windows path)
"""
import logging
import subprocess
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from database.db_client import get_connection  # noqa: E402

# db_client calls logging.basicConfig(INFO), which makes httpx log every request.
logging.getLogger("httpx").setLevel(logging.WARNING)
# Keep our lines in order with the node driver's output when piped.
sys.stdout.reconfigure(line_buffering=True)

API = "http://localhost:8000"
PASSWORD = "password123"
stamp = int(time.time())
emails = {role: f"smoketest-{role}-{stamp}@example.com" for role in ("owner", "other")}
client = httpx.Client(base_url=API, timeout=30)
failures = []


def check(label, response, expected):
    ok = response.status_code == expected
    print(f"{'PASS' if ok else 'FAIL'}  {label:48} {response.status_code} (want {expected})")
    if not ok:
        failures.append(f"{label}: {response.status_code} {response.text[:200]}")
    return response


def cleanup():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE email = ANY(%s);", (list(emails.values()),))
    print(f"cleanup: deleted {cur.rowcount} smoketest user(s)")
    conn.commit()
    cur.close()
    conn.close()


def run_api_checks():
    check("signup rejects invalid email 'a@b'", client.post("/auth/signup", json={"email": "a@b", "password": PASSWORD}), 422)

    headers = {}
    for role, email in emails.items():
        r = check(f"signup {role}", client.post("/auth/signup", json={"email": email, "password": PASSWORD, "display_name": "Smoke"}), 200)
        headers[role] = {"Authorization": f"Bearer {r.json()['access_token']}"}
        check(f"create profile {role}", client.post("/profile", json={"target_role": "Engineer", "label": "smoke"}, headers=headers[role]), 200)

    owner, other = headers["owner"], headers["other"]
    check("login owner", client.post("/auth/login", json={"email": emails["owner"], "password": PASSWORD}), 200)
    check("login wrong password", client.post("/auth/login", json={"email": emails["owner"], "password": "nope12345"}), 401)

    r = check("owner adds application", client.post(
        "/tools/applications", json={"company": "Acme", "role": "Engineer", "date_applied": "2026-10-01"}, headers=owner), 200)
    app_id = r.json()["id"]
    url = f"/tools/applications/{app_id}"

    check("no token: update application", client.put(url, json={"status": "Rejected"}), 401)
    check("no token: delete application", client.delete(url), 401)
    check("other user: update owner's application", client.put(url, json={"status": "Rejected"}, headers=other), 404)
    check("other user: delete owner's application", client.delete(url, headers=other), 404)
    if client.get("/tools/applications", headers=other).json() != []:
        failures.append("other user can see owner's applications")

    check("owner updates status", client.put(url, json={"status": "Interview"}, headers=owner), 200)
    statuses = [a["status"] for a in client.get("/tools/applications", headers=owner).json()]
    if statuses != ["Interview"]:
        failures.append(f"expected status ['Interview'], got {statuses}")
    check("owner deletes application", client.delete(url, headers=owner), 200)

    check("cover letter rejects blank JD", client.post("/tools/cover-letter", json={"job_description": "  "}, headers=owner), 422)
    check("tailored CV rejects blank JD", client.post("/tools/tailored-cv", data={"job_description": " \n "}, headers=owner), 400)


def run_ui_driver():
    driver = Path(__file__).with_name("drive_ui.mjs")
    pages = [arg for arg in sys.argv[1:] if not arg.startswith("--")]
    result = subprocess.run(["node", str(driver), emails["owner"], PASSWORD, *pages])
    if result.returncode != 0:
        failures.append("UI driver failed (see output above)")


if __name__ == "__main__":
    try:
        client.get("/health").raise_for_status()
    except httpx.HTTPError as e:
        sys.exit(f"API not reachable at {API} ({e}). Run start.sh first.")
    try:
        run_api_checks()
        if "--ui" in sys.argv:
            run_ui_driver()
    finally:
        cleanup()
    print("\nALL PASSED" if not failures else "\nFAILURES:\n  " + "\n  ".join(failures))
    sys.exit(1 if failures else 0)
