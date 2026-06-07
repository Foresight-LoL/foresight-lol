import asyncio
import time
from dataclasses import dataclass
from typing import Optional

import aiohttp
import logging

from utils.api.region import Region


@dataclass
class RiotAPIResponse:
    headers: dict
    data: dict | list
    url: str
    real_url: str
    content_length: int
    status: int
    charset: Optional[str]

    @property
    def ok(self) -> bool:
        return 200 <= self.status < 300

    @classmethod
    async def from_response(cls, response: aiohttp.ClientResponse) -> "RiotAPIResponse":
        return cls(
            headers=dict(response.headers),
            data=await response.json(),
            url=str(response.url),
            real_url=str(response.real_url),
            content_length=response.content_length or 0,
            status=response.status,
            charset=response.charset
        )

    @classmethod
    async def error_response(cls, response: aiohttp.ClientResponse) -> "RiotAPIResponse":
        try:
            data = await response.json()
        except Exception:
            data = {"message": await response.text()}

        return cls(
            headers=dict(response.headers),
            data=data,
            url=str(response.url),
            real_url=str(response.real_url),
            content_length=response.content_length or 0,
            status=response.status,
            charset=response.charset
        )


class AsyncRiotAPIClient:
    def __init__(
            self,
            api_key: str,
            region: Region,
            max_retries: int = 3,
            max_concurrent: int = 10
    ):
        if max_concurrent < 1 or max_retries < 1:
            raise ValueError(f"max_concurrent and max_retries must be > 0")

        self.logger = logging.getLogger(__name__)

        self.api_key = api_key
        self.max_retries = max_retries
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._rate_limit_lock = asyncio.Lock()
        self._session: aiohttp.ClientSession = None

        self.region = region
        self.higher_level_region = region.get_higher_level_region()
        self.base_url = f"https://{self.region}.api.riotgames.com"
        self.higher_level_url = f"https://{self.higher_level_region}.api.riotgames.com"

        self._retry_after_ts = 0.0

    async def __aenter__(self):
        self._session = aiohttp.ClientSession(
            headers={"X-Riot-Token": self.api_key}
        )

        self.logger.info(f"async riot api opened on region {self.region}")
        return self

    async def __aexit__(self, *exc):
        if self._session is not None:
            await self._session.close()

        self.logger.info(f"async riot api closed on region {self.region}")

    async def _request(
            self,
            path: str,
            **kwargs
    ) -> RiotAPIResponse:
        if path.startswith("/"):
            path = path.removeprefix("/")

        if path.startswith("riot/account") or path.startswith("lol/match"):
            url = f"{self.higher_level_url}/{path}"
        else:
            url = f"{self.base_url}/{path}"

        for attempt in range(self.max_retries):
            now = time.monotonic()
            if now < self._retry_after_ts:
                await asyncio.sleep(self._retry_after_ts - now)

            async with self._semaphore:
                async with self._session.request("GET", url, **kwargs) as response:
                    if response.status in [429, 500, 502, 503, 504]:
                        retry_after = int(response.headers.get("Retry-After", 61))  # TODO: change this when we get the new api key

                        if response.status == 429:
                            self.logger.warning(f"got rate limited, will retry in {retry_after} seconds, until then requests are held")
                        else:
                            self.logger.warning(f"the api server is experiencing some problems, will retry in {retry_after} seconds, until then requests are held")

                        async with self._rate_limit_lock:
                            self._retry_after_ts = max(self._retry_after_ts, time.monotonic() + retry_after)

                        if attempt >= self.max_retries - 1:
                            self.logger.error(f"max retries exceeded, will return")
                            return await RiotAPIResponse.error_response(response)  # max retries reached

                        continue

                    if response.status != 200:  # we only retry on 429
                        return await RiotAPIResponse.error_response(response)

                    return await RiotAPIResponse.from_response(response)

        return await RiotAPIResponse.error_response(response)
