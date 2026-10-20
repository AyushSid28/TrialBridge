import pytest

from src.services.rate_limiter import RateLimiter


@pytest.mark.asyncio
async def test_allows_requests_when_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("src.services.rate_limiter.settings.RATE_LIMIT_ENABLED", False)
    limiter = RateLimiter()

    allowed, retry_after = await limiter.is_allowed("10.0.0.1")

    assert allowed is True
    assert retry_after == 0


@pytest.mark.asyncio
async def test_blocks_after_limit_and_starts_cooldown(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("src.services.rate_limiter.settings.RATE_LIMIT_ENABLED", True)
    monkeypatch.setattr("src.services.rate_limiter.settings.RATE_LIMIT_REQUESTS", 2)
    monkeypatch.setattr("src.services.rate_limiter.settings.RATE_LIMIT_WINDOW_SECONDS", 60)
    monkeypatch.setattr("src.services.rate_limiter.settings.RATE_LIMIT_COOLDOWN_SECONDS", 30)

    limiter = RateLimiter()
    ip = "10.0.0.8"

    assert (await limiter.is_allowed(ip))[0] is True
    assert (await limiter.is_allowed(ip))[0] is True

    allowed, retry_after = await limiter.is_allowed(ip)
    assert allowed is False
    assert retry_after == 30

    stats = limiter.stats(ip)
    assert stats["in_cooldown"] is True
    assert stats["limit"] == 2
