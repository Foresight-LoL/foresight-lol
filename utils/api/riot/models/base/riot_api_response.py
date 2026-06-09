from dataclasses import dataclass
from typing import Optional, Self

import aiohttp


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
    async def from_response(cls, response: aiohttp.ClientResponse) -> Self:
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
    async def error_response(cls, response: aiohttp.ClientResponse) -> Self:
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
