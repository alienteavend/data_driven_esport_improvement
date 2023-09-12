from collections import defaultdict
from typing import Optional

import requests


class RiotApiHelper:
    summoner_url: str = 'https://eun1.api.riotgames.com/lol/summoner/v4/summoners/by-name/%s'
    match_list_url = f'https://europe.api.riotgames.com/lol/match/v5/matches/by-puuid/%s/ids'
    match_url = 'https://europe.api.riotgames.com/lol/match/v5/matches/%s'
    match_timeline_url = 'https://europe.api.riotgames.com/lol/match/v5/matches/%s/timeline'

    def __init__(self, riot_api_key: str):
        self.riot_api_key = riot_api_key
        self.headers = {
            'X-Riot-Token': riot_api_key
        }
        self.cache = defaultdict(lambda: defaultdict(lambda: {'puuid': ''}))

    def get_puuid_for_summoner_name(self, summoner_name: str):
        if summoner_name not in self.cache:
            self.get_summoner_data_by_name(summoner_name)

        return self.cache[summoner_name]['puuid']

    def get_summoner_data_by_name(self, summoner_name: str):
        data = self.__handle_request(self.summoner_url % summoner_name)
        self.cache[summoner_name]['puuid'] = data['puuid']
        return data

    def get_match_list(self, summoner_name: Optional[str] = None, summoner_puuid: Optional[str] = None):
        if not summoner_name and not summoner_puuid:
            raise Exception("At least one of summoner_name OR summoner_puuid must be set")

        puuid = summoner_puuid
        if not summoner_puuid and summoner_name and summoner_name not in self.cache:
            self.get_summoner_data_by_name(summoner_name)
            puuid = self.cache[summoner_name]['puuid']

        data = self.__handle_request(self.match_list_url % puuid)
        return data

    def get_match_by_id(self, match_id: str):
        data = self.__handle_request(self.match_url % match_id)
        return data

    def get_match_timeline_by_id(self, match_id: str):
        data = self.__handle_request(self.match_timeline_url % match_id)
        return data

    def __handle_request(self, url: str) -> Optional[dict]:
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print('Error getting summoner data:', e)
            return None
