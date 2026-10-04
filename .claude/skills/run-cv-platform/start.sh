#!/usr/bin/env bash
# Start the FastAPI backend (:8000) and Vite frontend (:5173) in the background and wait until both serve.
# Run from the repo root. Logs go to .claude/skills/run-cv-platform/out/.
set -u
SKILL_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SKILL_DIR/../../.." && pwd)"
OUT="$SKILL_DIR/out"
mkdir -p "$OUT"

if curl -sf localhost:8000/health >/dev/null 2>&1 || curl -sf localhost:5173 >/dev/null 2>&1; then
  echo "Port 8000 or 5173 already in use - run stop.sh first." >&2
  exit 1
fi

(cd "$ROOT" && nohup ./venv/Scripts/python -m uvicorn api.main:app --port 8000 > "$OUT/api.log" 2>&1 &)
(cd "$ROOT/frontend" && nohup npm run dev -- --port 5173 --strictPort > "$OUT/web.log" 2>&1 &)

for _ in $(seq 1 60); do
  if curl -sf localhost:8000/health >/dev/null 2>&1 && curl -sf localhost:5173 >/dev/null 2>&1; then
    echo "API  http://localhost:8000  $(curl -s localhost:8000/health)"
    echo "Web  http://localhost:5173"
    exit 0
  fi
  sleep 1
done

echo "Servers did not come up within 60s. Last log lines:" >&2
tail -5 "$OUT/api.log" "$OUT/web.log" >&2
exit 1
