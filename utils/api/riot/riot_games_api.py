import asyncio
import logging
import time
from typing import Optional

import aiohttp

from utils.api.riot.models.base.region import Region
from utils.api.riot.models.base.riot_api_response import RiotAPIResponse
from utils.api.token_bucket import TokenBucket


class AsyncRiotAPIClient:
    def __init__(
            self,
            api_key: str,
            default_region: Region,
            max_retries: int = 5,
            max_concurrent: int = 10,
            initial_capacity: Optional[int] = 20
    ):
        if max_concurrent < 1 or max_retries < 1:
            raise ValueError(f"max_concurrent and max_retries must be > 0")

        self.logger = logging.getLogger(__name__)

        self.api_key = api_key
        self.max_retries = max_retries
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._rate_limit_lock = asyncio.Lock()
        self._session: aiohttp.ClientSession = None

        self.default_region = default_region
        self._retry_after_ts = 0.0

        self._api_capacity_buckets = [
            TokenBucket(20, 1, start_tokens=initial_capacity),
            TokenBucket(100, 120, start_tokens=initial_capacity),
        ]

    async def __aenter__(self):
        self._session = aiohttp.ClientSession(
            headers={"X-Riot-Token": self.api_key}
        )

        self.logger.info(f"async riot api client opened")
        return self

    async def connect(self):
        await self.__aenter__()

    async def __aexit__(self, *exc):
        if self._session is not None:
            await self._session.close()

        self.logger.info(f"async riot api client closed")

    async def close(self):
        await self.__aexit__()

    async def _acquire_slot(self):
        for bucket in self._api_capacity_buckets:
            await bucket.acquire()

        now = time.monotonic()
        if now < self._retry_after_ts:
            await asyncio.sleep(self._retry_after_ts - now)

    async def request(
            self,
            path: str,
            region: Optional[Region] = None,
            **kwargs
    ) -> RiotAPIResponse:
        region = region if region is not None else self.default_region
        if path.startswith("/"):
            path = path.removeprefix("/")

        if path.startswith("riot/account") or path.startswith("lol/match"):
            url = f"{region.get_higher_level_base_url()}/{path}"
        else:
            url = f"{region.get_base_url()}/{path}"

        for attempt in range(self.max_retries):
            last_attempt = attempt >= self.max_retries - 1
            await self._acquire_slot()

            async with self._semaphore:
                async with self._session.request("GET", url, **kwargs) as response:
                    if response.status == 429:
                        retry_after = int(response.headers.get("Retry-After", 61))

                        async with self._rate_limit_lock:
                            already_waiting = time.monotonic() < self._retry_after_ts
                            self._retry_after_ts = max(self._retry_after_ts, time.monotonic() + retry_after)

                        if not already_waiting:
                            self.logger.warning(f"got rate limited, will retry in {retry_after} seconds, until then requests are held")

                        if last_attempt:
                            self.logger.error(f"max retries exceeded, will return")
                            return await RiotAPIResponse.error_response(response)  # max retries reached

                        continue

                    if response.status in (500, 502, 503, 504):
                        if last_attempt:
                            return await RiotAPIResponse.error_response(response)

                        backoff_time = min(2 ** attempt, 10)
                        self.logger.warning(f"server error {response.status}, retrying this request in {backoff_time}s")
                        await asyncio.sleep(backoff_time)
                        continue

                    if response.status != 200:  # we only retry on 429 and server errors
                        return await RiotAPIResponse.error_response(response)

                    return await RiotAPIResponse.from_response(response)

        error = Exception("the code shouldn't have reached here, will return")
        self.logger.error(error)
        raise error
