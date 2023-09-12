import json
import os
from collections import defaultdict

from src.riot_api import RiotApiHelper


class SummonerDataHandler:
    def __init__(self, riot_api_helper: RiotApiHelper):
        self.riot_api_helper = riot_api_helper
        self.cache = defaultdict(lambda: defaultdict(lambda: {'match': {}, 'timeline': {}}))
        self.summoner_cache = defaultdict(lambda: defaultdict(lambda: {}))

    def save_match_data_for_summoner(self, save_dir: str, summoner_name: str, num_matches: int = 5,
                                     force: bool = False):
        # We are getting CLASSIC games only!

        os.makedirs(save_dir, exist_ok=True)
        summoner_data = self.riot_api_helper.get_summoner_data_by_name(summoner_name)
        with open(os.path.join(save_dir, f'{summoner_name}.json'), 'w', encoding='utf-8') as file:
            json.dump(summoner_data, file, ensure_ascii=False, indent=4)
            self.summoner_cache[summoner_name] = summoner_data
        puuid = summoner_data['puuid']

        match_list = self.riot_api_helper.get_match_list(summoner_puuid=puuid)
        downloaded_matches = 0
        for match_id in match_list:
            if downloaded_matches == num_matches:
                break

            match_data = self.riot_api_helper.get_match_by_id(match_id)
            if match_data['info']['gameMode'] != 'CLASSIC':
                continue
            match_data_filename = os.path.join(save_dir, f'match_{match_id}.json')
            if force or not os.path.exists(match_data_filename):
                with open(match_data_filename, 'w', encoding='utf-8') as file:
                    json.dump(match_data, file, ensure_ascii=False, indent=4)

            match_timeline_data = self.riot_api_helper.get_match_timeline_by_id(match_id)
            match_timeline_data_filename = os.path.join(save_dir, f'match_{match_id}_timeline.json')
            if force or not os.path.exists(match_timeline_data_filename):
                with open(match_timeline_data_filename, 'w', encoding='utf-8') as file:
                    json.dump(match_timeline_data, file, ensure_ascii=False, indent=4)

            self.cache[summoner_name][match_id] = {
                'match': match_data,
                'timeline': match_timeline_data
            }
            downloaded_matches += 1

    def iterator_on_match_data(self, summoner_name: str):
        if not os.path.exists(summoner_name):
            self.save_match_data_for_summoner(summoner_name, summoner_name)
        elif os.path.exists(summoner_name) and summoner_name not in self.cache:
            self.__load_match_data_from_directory(summoner_name)
        for match_id, data in self.cache[summoner_name].items():
            yield data['match']

    def iterator_on_match_timeline_data(self, summoner_name: str):
        if not os.path.exists(summoner_name):
            self.save_match_data_for_summoner(summoner_name, summoner_name)
        elif os.path.exists(summoner_name) and summoner_name not in self.cache:
            self.__load_match_data_from_directory(summoner_name)

        for match_id, data in self.cache[summoner_name].items():
            yield data['timeline']

    def iterator_on_data(self, summoner_name: str):
        if not os.path.exists(summoner_name):
            self.save_match_data_for_summoner(summoner_name, summoner_name)
        elif os.path.exists(summoner_name) and summoner_name not in self.cache:
            self.__load_match_data_from_directory(summoner_name)

        for match_id, data in self.cache[summoner_name].items():
            yield data

    def find_player_index_in_data(self, match_data: dict, summoner_name: str):
        if summoner_name in self.summoner_cache:
            puuid = self.summoner_cache[summoner_name]['puuid']
        elif summoner_name not in self.summoner_cache and os.path.exists(summoner_name):
            data = self.__load_player_data_from_directory(summoner_name)
            puuid = data['puuid']
        else:
            puuid = self.riot_api_helper.get_puuid_for_summoner_name(summoner_name)
        return match_data['metadata']['participants'].index(puuid)

    def __load_player_data_from_directory(self, summoner_name: str):
        with open(os.path.join(summoner_name, f'{summoner_name}.json'), 'r', encoding='utf-8') as file:
            data = json.load(file)
            self.summoner_cache[summoner_name] = data
        return data

    def __load_match_data_from_directory(self, summoner_name: str):
        # Check if it's a directory
        if os.path.isdir(summoner_name):
            # Initialize match and timeline dictionaries
            match_data = {}
            timeline_data = {}

            # Iterate over files in the subdirectory
            for filename in os.listdir(summoner_name):
                if filename == f'{summoner_name}.json':
                    continue
                match_id = filename.replace("match_", "").replace("_timeline", "").replace(".json", "")
                file_path = os.path.join(summoner_name, filename)

                # Check if it's a JSON file not ending with "_timeline"
                if filename.endswith(".json") and not filename.endswith("_timeline.json"):
                    try:
                        # Load the JSON content into match_data
                        with open(file_path, 'r', encoding='utf-8') as file:
                            match_data[match_id] = json.load(file)
                    except Exception as e:
                        print(f"Error loading match data from {file_path}: {e}")

                # Check if it's a JSON file ending with "_timeline.json"
                elif filename.endswith("_timeline.json"):
                    try:
                        # Load the JSON content into timeline_data
                        with open(file_path, 'r', encoding='utf-8') as file:
                            timeline_data[match_id] = json.load(file)
                    except Exception as e:
                        print(f"Error loading timeline data from {file_path}: {e}")

            for filename in match_data.keys():
                self.cache[summoner_name][filename] = {
                    "match": match_data[filename],
                    "timeline": timeline_data[filename]
                }
