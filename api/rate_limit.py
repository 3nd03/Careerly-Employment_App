"""In-memory per-IP rate limiting.

Keyed by (route path, client IP) with a sliding window kept in a process-local
dict. Resets on restart and isn't shared across worker processes, which is
fine for this prototype's single-process deployment; a multi-instance
deployment would need a shared store (e.g. Redis) instead.
"""
import time
from collections import defaultdict

from fastapi import HTTPException, Request, status

_hits: dict[str, list[float]] = defaultdict(list)


def rate_limit(max_requests: int, window_seconds: int):
    def dependency(request: Request) -> None:
        client_ip = request.client.host if request.client else "unknown"
        key = f"{request.url.path}:{client_ip}"
        now = time.time()
        hits = _hits[key]
        while hits and hits[0] <= now - window_seconds:
            hits.pop(0)
        if len(hits) >= max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later.",
            )
        hits.append(now)

    return dependency


def reset() -> None:
    """Clears all tracked hits. Used by tests to isolate the limiter between cases."""
    _hits.clear()
