"""Unit tests for the sliding-window rate limiter."""

import time

from app.rate_limiter import RateLimiter


def test_allows_up_to_limit(monkeypatch):
    limiter = RateLimiter(max_per_minute=3)
    assert limiter.allow() is True
    assert limiter.allow() is True
    assert limiter.allow() is True
    assert limiter.allow() is False  # 4th call in the window is blocked


def test_window_slides_forward(monkeypatch):
    limiter = RateLimiter(max_per_minute=2)
    now = {"t": 1000.0}
    monkeypatch.setattr(time, "time", lambda: now["t"])

    assert limiter.allow() is True
    assert limiter.allow() is True
    assert limiter.allow() is False

    now["t"] += 61  # slide past the 60 s window
    assert limiter.allow() is True
    assert limiter.allow() is True
    assert limiter.allow() is False


def test_reset_clears_window(monkeypatch):
    limiter = RateLimiter(max_per_minute=1)
    assert limiter.allow() is True
    assert limiter.allow() is False
    limiter.reset()
    assert limiter.allow() is True
