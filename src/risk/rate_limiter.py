from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator


class TokenBucket:
    """
    Simple async token bucket to stay under exchange rate limits.
    """

    def __init__(self, rate: int, interval: float = 1.0) -> None:
        self.rate = rate
        self.interval = interval
        self._tokens = rate
        self._lock = asyncio.Lock()
        self._last_refill = asyncio.get_event_loop().time()

    def _refill(self) -> None:
        now = asyncio.get_event_loop().time()
        elapsed = now - self._last_refill
        refill = int(elapsed / self.interval * self.rate)
        if refill > 0:
            self._tokens = min(self.rate, self._tokens + refill)
            self._last_refill = now

    @asynccontextmanager
    async def acquire(self, weight: int = 1) -> AsyncIterator[None]:
        async with self._lock:
            while True:
                self._refill()
                if self._tokens >= weight:
                    self._tokens -= weight
                    break
                await asyncio.sleep(self.interval / self.rate)
        try:
            yield
        finally:
            pass


