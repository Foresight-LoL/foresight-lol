from dataclasses import dataclass
from datetime import datetime, UTC
from typing import List, Self, Dict

import polars as pl

from utils.api.riot.models.api_model_interface import APIModelInterface


@dataclass
class RankSnapshot(APIModelInterface):
    puuid: str
    queue_type: str
    snapshot_time: datetime
    tier: str
    rank: str
    league_points: int
    wins: int
    losses: int
    hot_streak: bool
    veteran: bool
    fresh_blood: bool
    inactive: bool

    @classmethod
    def get_keys(cls) -> List[str]:
        return ["puuid", "queue_type", "snapshot_time"]

    @classmethod
    def to_dataframe(cls, records: List[Self]) -> pl.DataFrame:
        return pl.DataFrame(records)

    @classmethod
    def from_json(cls, puuid: str, json_data: List[Dict]) -> List[Self]:
        rank_snapshots_arr = []
        for rank_snapshot_json in json_data:
            rank_snapshots_arr.append(
                RankSnapshot(
                    puuid=puuid,
                    queue_type=rank_snapshot_json["queueType"],
                    snapshot_time=datetime.now(UTC),
                    tier=rank_snapshot_json["tier"],
                    rank=rank_snapshot_json["rank"],
                    league_points=rank_snapshot_json["leaguePoints"],
                    wins=rank_snapshot_json["wins"],
                    losses=rank_snapshot_json["losses"],
                    hot_streak=rank_snapshot_json["hotStreak"],
                    veteran=rank_snapshot_json["veteran"],
                    fresh_blood=rank_snapshot_json["freshBlood"],
                    inactive=rank_snapshot_json["inactive"]
                )
            )

        return rank_snapshots_arr
