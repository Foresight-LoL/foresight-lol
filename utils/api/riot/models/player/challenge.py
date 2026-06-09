from dataclasses import dataclass
from datetime import datetime, UTC
from typing import List, Self, Optional, Dict

import polars as pl

from utils.api.riot.models.api_model_interface import APIModelInterface


@dataclass
class ChallengeTotalPointsDTO(APIModelInterface):
    level: str
    current: int
    max: int
    percentile: float

    @classmethod
    def get_keys(cls) -> List[str]:
        return []

    @classmethod
    def to_dataframe(cls, records: List[Self]) -> pl.DataFrame:
        return pl.DataFrame(records)

    @classmethod
    def from_json(cls, json_data: Dict) -> ChallengeTotalPointsDTO:
        if "totalPoints" in json_data:
            fixed_json_data = json_data["totalPoints"]
        else:
            fixed_json_data = json_data

        return ChallengeTotalPointsDTO(
            level=fixed_json_data["level"],
            current=fixed_json_data["current"],
            max=fixed_json_data["max"],
            percentile=fixed_json_data["percentile"]
        )


@dataclass
class Challenge(APIModelInterface):
    puuid: str
    challenge_id: int
    percentile: float
    players_in_level: Optional[int]
    achieved_time: Optional[datetime]
    value: float
    level: str
    position: Optional[int]

    @classmethod
    def get_keys(cls) -> List[str]:
        return ["puuid", "challenge_id"]

    @classmethod
    def to_dataframe(cls, records: List[Self]) -> pl.DataFrame:
        return pl.DataFrame(records)

    @classmethod
    def from_json(cls, puuid: str, json_data: List | Dict) -> List[Self]:
        challenges_list = json_data if isinstance(json_data, list) else json_data["challenges"]

        challenges_arr = []
        for challenge_entry in challenges_list:
            achieved_time_unix = challenge_entry.get("achievedTime")

            challenges_arr.append(
                Challenge(
                    puuid=puuid,
                    challenge_id=challenge_entry["challengeId"],
                    percentile=challenge_entry["percentile"],
                    players_in_level=challenge_entry.get("playersInLevel"),
                    achieved_time=datetime.fromtimestamp(achieved_time_unix // 1000, UTC) if achieved_time_unix else None,
                    value=challenge_entry["value"],
                    level=challenge_entry["level"],
                    position=challenge_entry.get("position")
                )
            )

        return challenges_arr
