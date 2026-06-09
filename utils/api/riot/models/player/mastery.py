from dataclasses import dataclass
from datetime import datetime, UTC
from typing import List, Self, Optional, Dict

import polars as pl

from utils.api.riot.models.api_model_interface import APIModelInterface


@dataclass
class Mastery(APIModelInterface):
    puuid: str
    champion_id: int
    champion_points_until_next_level: int
    chest_granted: Optional[bool]
    last_play_time: datetime
    champion_level: int
    champion_points: int
    champion_points_since_last_level: int
    mark_required_for_next_level: int
    champion_season_milestone: int
    tokens_earned: int
    milestone_grades: List[str]

    @classmethod
    def get_keys(cls) -> List[str]:
        return ["puuid", "champion_id"]

    @classmethod
    def to_dataframe(cls, records: List[Self]) -> pl.DataFrame:
        return pl.DataFrame(records)

    @classmethod
    def from_json(cls, json_data: List[Dict]) -> List[Self]:
        masteries_arr = []
        for masteries_entry in json_data:
            masteries_arr.append(
                Mastery(
                    puuid=masteries_entry["puuid"],
                    champion_id=masteries_entry["championId"],
                    champion_points_until_next_level=masteries_entry["championPointsUntilNextLevel"],
                    chest_granted=masteries_entry.get("chestGranted"),
                    last_play_time=datetime.fromtimestamp(masteries_entry["lastPlayTime"] // 1000, UTC),
                    champion_level=masteries_entry["championLevel"],
                    champion_points=masteries_entry["championPoints"],
                    champion_points_since_last_level=masteries_entry["championPointsSinceLastLevel"],
                    mark_required_for_next_level=masteries_entry["markRequiredForNextLevel"],
                    champion_season_milestone=masteries_entry["championSeasonMilestone"],
                    tokens_earned=masteries_entry["tokensEarned"],
                    milestone_grades=masteries_entry.get("milestoneGrades", [])
                )
            )

        return masteries_arr
