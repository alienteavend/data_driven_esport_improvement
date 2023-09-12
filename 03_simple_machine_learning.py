import os

from dotenv import load_dotenv
import numpy as np

from sklearn.ensemble import IsolationForest
import pandas as pd
from src.riot_api import RiotApiHelper
from src.summoner_data_handler import SummonerDataHandler
import matplotlib.pyplot as plt


def analyze_cs(match_data_timeline: dict, player_index: int):
    participant_frames: dict = match_data_timeline["info"]["frames"]
    minions_killed_by_player = [x["participantFrames"][str(player_index)]["minionsKilled"] for x in participant_frames]
    gold_gained_by_player = [x["participantFrames"][str(player_index)]["totalGold"] for x in participant_frames]
    kills_by_player = []
    assists_by_player = []
    deaths_by_player = []
    damage_done_by_player = []
    damage_received_by_player = []
    sum_kills = 0
    sum_assists = 0
    sum_deaths = 0
    sum_damage_done = 0
    sum_damage_received = 0
    for frame in participant_frames:
        current_frame_kills = 0
        current_frame_assists = 0
        current_frame_deaths = 0
        current_damage_done = 0
        current_damage_received = 0
        for event in frame["events"]:
            if event["type"] == 'CHAMPION_KILL':
                if event["victimId"] == player_index:
                    current_frame_deaths += 1
                if event["killerId"] == player_index:
                    current_frame_kills += 1
                if "assistingParticipantIds" in event and player_index in event["assistingParticipantIds"]:
                    current_frame_assists += 1
                if 'victimDamageDealt' in event and (
                        event["killerId"] == player_index or "assistingParticipantIds" in event and player_index in
                        event["assistingParticipantIds"]):
                    for damage_event in event['victimDamageDealt']:
                        if damage_event['participantId'] != player_index:
                            continue
                        all_damage = damage_event['magicDamage'] + damage_event['physicalDamage'] + damage_event[
                            'trueDamage']
                        current_damage_done += all_damage
                if 'victimDamageReceived' in event and (
                        event["victimId"] == player_index):
                    for damage_event in event['victimDamageReceived']:
                        all_damage_received = damage_event['magicDamage'] + damage_event['physicalDamage'] + \
                                              damage_event[
                                                  'trueDamage']
                        current_damage_received += all_damage_received
        sum_kills += current_frame_kills
        kills_by_player.append(sum_kills)
        sum_assists += current_frame_assists
        assists_by_player.append(sum_assists)
        sum_deaths += current_frame_deaths
        deaths_by_player.append(sum_deaths)
        sum_damage_done += current_damage_done
        damage_done_by_player.append(sum_damage_done)
        sum_damage_received += current_damage_received
        damage_received_by_player.append(sum_damage_received)

    return np.array(minions_killed_by_player), np.array(gold_gained_by_player), np.array(kills_by_player), np.array(
        assists_by_player), np.array(deaths_by_player), np.array(damage_done_by_player), np.array(
        damage_received_by_player)


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

        cs, gold, kills, assists, deaths, damage_done, damage_received = analyze_cs(
            current_match_data["timeline"],
            player_id)

        minutes = np.arange(0, game_duration , 1)  # Assuming intervals of 1 minute

        # Combine the arrays into a single feature matrix
        feature_matrix = np.column_stack((np.diff(cs), np.diff(gold), np.diff(kills), np.diff(assists), np.diff(deaths),
                                          np.diff(damage_done), np.diff(damage_received)))
        # Create an Isolation Forest model
        model = IsolationForest(n_estimators=100, max_samples='auto',
                                contamination=0.05)  # Adjust the contamination parameter as needed

        # Fit the model on your data
        model.fit(feature_matrix)

        # Predict anomalies (1 for inliers, -1 for outliers)
        anomaly_scores = model.predict(feature_matrix)

        # Create a DataFrame to store the anomaly scores and the original data
        anomalies_df = pd.DataFrame({'Anomaly Score': anomaly_scores, 'CS': np.diff(cs),
                                     'Total gold': np.diff(gold), 'Kills': np.diff(kills), 'Assists': np.diff(assists),
                                     'Deaths': np.diff(deaths), 'Damage done': np.diff(damage_done),
                                     'Damage received': np.diff(damage_received),
                                     'Minute': minutes})

        # Filter out the anomalies
        anomalies = anomalies_df[anomalies_df['Anomaly Score'] == -1]

        # Find minutes where anomalies are present in all data
        anomalies_all_data = anomalies.groupby('Minute').size() == 7  # 7 metrics have anomalies

        # Get the minutes with anomalies in all data
        minutes_with_anomalies_all_data = anomalies_all_data[anomalies_all_data].index.tolist()

        # Create subplots
        fig, axes = plt.subplots(4, 2, figsize=(14, 12))

        # Plot CS with anomalies
        axes[0, 0].plot(minutes, np.diff(cs), label='CS', color='blue')
        axes[0, 0].plot(anomalies['Minute'], anomalies['CS'], 'ro', label='Anomalies')
        axes[0, 0].set_title('CS Over Time')

        # Plot Gold with anomalies
        axes[0, 1].plot(minutes, np.diff(gold), label='Gold', color='green')
        axes[0, 1].plot(anomalies['Minute'], anomalies['Total gold'], 'ro', label='Anomalies')
        axes[0, 1].set_title('Gold Over Time')

        # Plot Kills with anomalies
        axes[1, 0].plot(minutes, np.diff(kills), label='Kills', color='purple')
        axes[1, 0].plot(anomalies['Minute'], anomalies['Kills'], 'ro', label='Anomalies')
        axes[1, 0].set_title('Kills Over Time')

        # Plot Assists with anomalies
        axes[1, 1].plot(minutes, np.diff(assists), label='Assists', color='orange')
        axes[1, 1].plot(anomalies['Minute'], anomalies['Assists'], 'ro', label='Anomalies')
        axes[1, 1].set_title('Assists Over Time')

        # Plot Deaths with anomalies
        axes[2, 0].plot(minutes, np.diff(deaths), label='Deaths', color='red')
        axes[2, 0].plot(anomalies['Minute'], anomalies['Deaths'], 'ro', label='Anomalies')
        axes[2, 0].set_title('Deaths Over Time')

        # Plot Damage Done with anomalies
        axes[2, 1].plot(minutes, np.diff(damage_done), label='Damage Done', color='cyan')
        axes[2, 1].plot(anomalies['Minute'], anomalies['Damage done'], 'ro', label='Anomalies')
        axes[2, 1].set_title('Damage Done Over Time')

        # Plot Damage Received with anomalies
        axes[3, 0].plot(minutes, np.diff(damage_received), label='Damage Received', color='magenta')
        axes[3, 0].plot(anomalies['Minute'], anomalies['Damage received'], 'ro', label='Anomalies')
        axes[3, 0].set_title('Damage Received Over Time')

        # Remove empty subplot
        fig.delaxes(axes[3, 1])

        # Set common labels
        for ax in axes.flat:
            ax.set_xlabel('Minute')
            ax.set_ylabel('Value')
            ax.legend()

        # Adjust spacing between subplots
        plt.tight_layout()

        # Show the combined visualization
        plt.show()

if __name__ == '__main__':
    main()
