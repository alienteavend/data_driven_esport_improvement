import os

from dotenv import load_dotenv
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt

from src.riot_api import RiotApiHelper
from src.summoner_data_handler import SummonerDataHandler


def analyze_cs(match_data_timeline: dict, player_index: int):
    participant_frames: dict = match_data_timeline["info"]["frames"]
    minions_killed_by_player = [x["participantFrames"][str(player_index)]["minionsKilled"] for x in participant_frames]
    # Calculate Z-Score for CS per minute
    cs_per_minute_array = np.array(minions_killed_by_player)
    z_scores = stats.zscore(cs_per_minute_array)
    anomalies = np.where(np.abs(z_scores) < 0.2)
    if len(anomalies[0]) > 0:
        recommendation = "Anomalies detected in CS per minute. Review your gameplay for potential mistakes."
    else:
        recommendation = "No significant anomalies detected in CS per minute. Keep practicing!"

    return cs_per_minute_array, anomalies, recommendation


def main():
    load_dotenv()
    api_key = os.getenv("API_KEY")
    summoner_name = os.getenv("SUMMONER_NAME")

    riot_api_helper = RiotApiHelper(api_key)
    data_handler = SummonerDataHandler(riot_api_helper)

    for current_match_data in data_handler.iterator_on_data(summoner_name):
        player_index = data_handler.find_player_index_in_data(current_match_data["timeline"], summoner_name)
        player_id = player_index + 1
        game_duration = current_match_data["match"]["info"]["gameDuration"] / 60
        cs_per_minute_array, anomalies, recommendation = analyze_cs(current_match_data["timeline"], player_id)

        # Plot CS data along with anomalies
        timestamps = np.arange(0, game_duration + 1, 1)  # Assuming intervals of 1 minute
        zero = 0 * timestamps
        range_9_10 = (9 * timestamps, 10 * timestamps)
        range_7_9 = (7 * timestamps, 9 * timestamps)
        max_cs_per_minute = 12.6 * timestamps

        print(f'------------------------')
        print(recommendation)
        print(f'Anomaly minutes: {list(anomalies)}')

        plt.plot(timestamps, cs_per_minute_array, marker='x', label='CS per minute')
        plt.scatter(anomalies[0], cs_per_minute_array[anomalies[0]], color='red', marker='o', label='Anomalies')
        # Plot horizontal lines for different CS per minute ranges
        plt.plot(timestamps, max_cs_per_minute, color='gray', linestyle='--', label='Max CS per minute (12.6)')

        plt.fill_between(timestamps, zero, range_9_10[0], color='red', alpha=0.3,
                         label='CS per minute (7-) BAD')
        plt.fill_between(timestamps, range_7_9[0], range_7_9[1], color='yellow', alpha=0.3,
                         label='CS per minute (7-9) OKAY')
        plt.fill_between(timestamps, range_9_10[0], range_9_10[1], color='blue', alpha=0.3,
                         label='CS per minute (9-10) GOOD')
        plt.fill_between(timestamps, range_9_10[1], max_cs_per_minute, color='green', alpha=0.3,
                         label='CS per minute (10+) EXCELLENT')

        plt.xlabel('Time (minutes)')
        plt.ylabel('CS per minute')
        plt.title('CS per Minute and Anomalies Timeline')
        plt.legend()
        plt.grid(True)
        plt.show()


if __name__ == '__main__':
    main()
