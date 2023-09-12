import os
from dotenv import load_dotenv

from src.riot_api import RiotApiHelper
from src.summoner_data_handler import SummonerDataHandler


# Function to calculate CS per minute
def calculate_cs_per_minute(cs: int, game_duration: int):
    return cs / game_duration


# Function to analyze CS data and provide recommendations
def analyze_cs(match_data: dict, player_index: int):
    participant_data = match_data["info"]["participants"][player_index]

    total_cs = participant_data["totalMinionsKilled"]
    neutral_cs = participant_data["neutralMinionsKilled"]
    game_duration = match_data["info"]["gameDuration"] / 60

    cs_per_minute = calculate_cs_per_minute(total_cs + neutral_cs, game_duration)

    if cs_per_minute >= 7.0:
        recommendation = "Your CS per minute is good. Keep up the good work!"
    else:
        recommendation = "Your CS per minute could be improved. Focus on last-hitting minions more consistently."

    gold_per_cs = 21

    potential = {
        7: game_duration * 7 * gold_per_cs - game_duration * cs_per_minute * gold_per_cs,
        9: game_duration * 9 * gold_per_cs - game_duration * cs_per_minute * gold_per_cs,
        10: game_duration * 10 * gold_per_cs - game_duration * cs_per_minute * gold_per_cs,
    }

    return cs_per_minute, recommendation, potential


def main():
    load_dotenv()
    api_key = os.getenv("API_KEY")
    summoner_name = os.getenv("SUMMONER_NAME")

    riot_api_helper = RiotApiHelper(api_key)
    data_handler = SummonerDataHandler(riot_api_helper)

    for current_match_data in data_handler.iterator_on_match_data(summoner_name):
        player_index = data_handler.find_player_index_in_data(current_match_data, summoner_name)
        cs_per_minute, recommendation, potential = analyze_cs(current_match_data, player_index)
        print(f'------------------------')
        print(f'Creep score: {cs_per_minute}')
        print(recommendation)
        print("Potential gains with better CS/m (at the end of the game):")
        for key, value in potential.items():
            print(f'{key} cs/m: {value:.0f} diff')


if __name__ == '__main__':
    main()
