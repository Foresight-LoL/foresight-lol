from dataclasses import dataclass
from datetime import datetime, UTC
from typing import List, Self, Dict

import polars as pl

from utils.api.riot.models.api_model_interface import APIModelInterface
from utils.api.riot.models.base.region import Region


@dataclass
class PlayerBase(APIModelInterface):
    puuid: str
    game_name: str
    tag_line: str
    region: str
    synced_at: datetime

    @classmethod
    def get_keys(cls) -> List[str]:
        return ["puuid"]

    @classmethod
    def to_dataframe(cls, records: List[Self]) -> pl.DataFrame:
        return pl.DataFrame(records)

    @classmethod
    def from_json(cls, json_data: Dict | List, region: Region) -> PlayerBase:
        return PlayerBase(
            puuid=json_data["puuid"],
            game_name=json_data["gameName"],
            tag_line=json_data["tagLine"],
            region=region.value,
            synced_at=datetime.now(UTC)
        )
