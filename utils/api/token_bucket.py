import asyncio
import time
from typing import Optional


class TokenBucket:
    def __init__(
            self,
            capacity: int,
            window_sec: int,
            start_tokens: Optional[int] = None
    ):
        self.capacity = capacity
        self.window_sec = window_sec
        self.refill_rate = self.capacity / self.window_sec

        self._tokens = float(capacity) if start_tokens is None else min(start_tokens, capacity)
        self._updated = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self):
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._updated

            self._tokens = min(self.capacity, self._tokens + elapsed * self.refill_rate)
            self._updated = now

            if self._tokens >= 1:
                wait = 0.0
                self._tokens -= 1

            else:
                deficit = 1 - self._tokens
                wait = deficit / self.refill_rate

        if wait > 0:
            await asyncio.sleep(wait)
            await self.acquire()
