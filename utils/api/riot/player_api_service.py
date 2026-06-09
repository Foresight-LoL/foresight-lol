import asyncio
from typing import Optional, List, Tuple

from utils.api.riot.models.player.challenge import Challenge
from utils.api.riot.models.player.mastery import Mastery
from utils.api.riot.models.player.player import PlayerBase
from utils.api.riot.models.player.player_snapshot import PlayerSnapshot
from utils.api.riot.models.rank.rank_snapshot import RankSnapshot
from utils.api.riot.models.base.region import Region
from utils.api.riot.models.base.riot_api_response import RiotAPIResponse
from utils.api.riot.riot_games_api import AsyncRiotAPIClient


class PlayerApiService:
    def __init__(self, api_client: AsyncRiotAPIClient, default_region: Region):
        self.api_client = api_client
        self.default_region = default_region

    @classmethod
    def _malformed_error_response(cls, path: str, data: str):
        return RuntimeError(f"error or malformed response on upstream api with path {path} | details:\n {data}")

    async def request_by_puuid(self, puuid: str, region: Optional[Region] = None) -> PlayerBase:
        region = region or self.default_region
        request_path = f"/riot/account/v1/accounts/by-puuid/{puuid}"

        player_response = await self.api_client.request(path=request_path, region=region)
        if not (isinstance(player_response.data, dict) and player_response.ok):
            raise self._malformed_error_response(request_path, player_response.data.__str__())

        player_response_json = player_response.data
        return PlayerBase.from_json(player_response_json, region=region)

    async def request_by_game_name(self, game_name: str, tag_line: str, region: Optional[Region] = None) -> PlayerBase:
        region = region or self.default_region
        request_path = f"/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"

        player_response = await self.api_client.request(path=request_path, region=region)
        if not (isinstance(player_response.data, dict) and player_response.ok):
            raise self._malformed_error_response(request_path, player_response.data.__str__())

        player_response_json = player_response.data
        return PlayerBase.from_json(player_response_json, region=region)

    async def _get_player_challenges_helper(self, puuid: str, region: Optional[Region] = None) -> Tuple[List[Challenge], RiotAPIResponse]:
        region = region or self.default_region
        request_path = f"/lol/challenges/v1/player-data/{puuid}"

        challenges_response = await self.api_client.request(path=request_path, region=region)
        if not (isinstance(challenges_response.data, dict) and challenges_response.ok):
            raise self._malformed_error_response(request_path, challenges_response.data.__str__())

        return Challenge.from_json(puuid, challenges_response.data), challenges_response

    async def get_player_challenges(self, puuid: str, region: Optional[Region] = None) -> List[Challenge]:
        return (await self._get_player_challenges_helper(puuid, region))[0]

    async def _get_player_snapshot_helper(self, puuid: str, region: Optional[Region] = None) -> Tuple[PlayerSnapshot, List[Challenge]]:
        region = region or self.default_region
        request_path = f"/lol/summoner/v4/summoners/by-puuid/{puuid}"

        summoner_response, (challenges, challenges_response) = await asyncio.gather(
            self.api_client.request(request_path, region=region),
            self._get_player_challenges_helper(puuid, region)
        )

        if not (isinstance(summoner_response.data, dict) and summoner_response.ok and isinstance(challenges_response.data, dict) and challenges_response.ok):
            raise self._malformed_error_response(request_path, summoner_response.data.__str__())

        player_snapshot = PlayerSnapshot.from_json(puuid=puuid, summoner_json=summoner_response.data, challenges_json=challenges_response.data)

        return player_snapshot, challenges

    async def get_player_snapshot(self, puuid: str, region: Optional[Region] = None) -> PlayerSnapshot:
        return (await self._get_player_snapshot_helper(puuid, region))[0]

    async def get_player_masteries(self, puuid: str, region: Optional[Region] = None) -> List[Mastery]:
        region = region or self.default_region
        request_path = f"/lol/champion-mastery/v4/champion-masteries/by-puuid/{puuid}"

        masteries_response = await self.api_client.request(request_path, region=region)
        if not (isinstance(masteries_response.data, list) and masteries_response.ok):
            raise self._malformed_error_response(request_path, masteries_response.data.__str__())

        return Mastery.from_json(masteries_response.data)

    async def get_player_rank_snapshots(self, puuid: str, region: Optional[Region] = None) -> List[RankSnapshot]:
        region = region or self.default_region
        request_path = f"/lol/league/v4/entries/by-puuid/{puuid}"

        rank_snapshots_response = await self.api_client.request(request_path, region=region)
        if not (isinstance(rank_snapshots_response.data, list) and rank_snapshots_response.ok):
            raise self._malformed_error_response(request_path, rank_snapshots_response.data.__str__())

        return RankSnapshot.from_json(puuid, rank_snapshots_response.data)
