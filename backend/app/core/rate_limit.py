"""core/rate_limit.py — In-memory sliding window rate limiter (C-03).

Design decisions (C-03 design.md D-04):
- Sliding window algorithm using a deque of timestamps per key.
- Key for login: f"{ip}:{email_lower}" — blocks both per-IP and per-email attacks.
- In-memory only: does NOT survive worker restart and does NOT scale horizontally.
  A TODO documents the Redis upgrade path for multi-worker production deployments.
- Thread-safe for async (single-threaded event loop) — no locks needed.

TODO (post-MVP): replace the in-memory dict with Redis + EXPIRE for multi-worker safety.
"""

import time
from collections import defaultdict, deque
from typing import Deque

from app.core.exceptions import AppError


class TooManyRequestsError(AppError):
    """Raised when a rate limit is exceeded."""

    http_status = 429

    def __init__(self, message: str = "Too many requests — try again later") -> None:
        super().__init__(message, code="rate_limit_exceeded")


class RateLimiter:
    """Sliding window rate limiter backed by an in-memory deque per key.

    Usage:
        limiter = RateLimiter()
        limiter.check("127.0.0.1:user@example.com", limit=5, window_seconds=60)
        # Raises TooManyRequestsError if >= limit events in the last window_seconds.

    Public methods:
        check(key, limit, window_seconds)   — record an event; raises if over limit
        reset(key)                          — clear counters for a key (after success)
    """

    def __init__(self) -> None:
        # key -> deque of monotonic timestamps (float, seconds)
        self._windows: dict[str, Deque[float]] = defaultdict(deque)

    def check(self, key: str, limit: int, window_seconds: int) -> None:
        """Record an event and raise TooManyRequestsError if the limit is exceeded.

        The check happens BEFORE recording the current event — so the first `limit`
        calls per window succeed, and the (limit+1)-th raises.

        Args:
            key:            Rate limit key (e.g. "ip:email").
            limit:          Maximum allowed events per window (inclusive).
            window_seconds: Sliding window size in seconds.

        Raises:
            TooManyRequestsError: If the caller has already made `limit` events
                                  within the last `window_seconds`.
        """
        now = time.monotonic()
        cutoff = now - window_seconds
        window = self._windows[key]

        # Evict events outside the window
        while window and window[0] <= cutoff:
            window.popleft()

        if len(window) >= limit:
            raise TooManyRequestsError()

        window.append(now)

    def reset(self, key: str) -> None:
        """Clear the event history for a key.

        Call this on a successful login to reset the (IP, email) counter.

        Args:
            key: Rate limit key to clear.
        """
        self._windows.pop(key, None)


# Module-level singleton — shared across all requests in the same worker process.
rate_limiter = RateLimiter()
