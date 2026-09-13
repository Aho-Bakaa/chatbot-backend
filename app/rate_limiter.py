"""Thread-safe sliding-window rate limiter.

NOTE (documented scaling limitation): this limiter is process-local and
in-memory. It resets on restart and does not coordinate across multiple
workers/instances; for multi-replica deployments it should be replaced with
a shared store (e.g. Redis) or moved to a gateway.
"""

import threading
import time


class RateLimiter:
    """Sliding-window limiter: at most `max_per_minute` calls in any 60 s window."""

    def __init__(self, max_per_minute: int):
        self.max = max_per_minute
        self._calls: list[float] = []
        self._lock = threading.Lock()

    def allow(self) -> bool:
        now = time.time()
        with self._lock:
            self._calls = [t for t in self._calls if now - t < 60]
            if len(self._calls) < self.max:
                self._calls.append(now)
                return True
            return False

    def reset(self) -> None:
        with self._lock:
            self._calls.clear()
