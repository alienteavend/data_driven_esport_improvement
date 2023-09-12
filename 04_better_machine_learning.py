import os

import numpy as np
from dotenv import load_dotenv
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

from src.riot_api import RiotApiHelper
from src.summoner_data_handler import SummonerDataHandler


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
                        event["killerId"] == player_index or ("assistingParticipantIds" in event and player_index in
                        event["assistingParticipantIds"])):
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
        print(current_match_data['match']['info']['gameId'])

        cs, gold, kills, assists, deaths, damage_done, damage_received = analyze_cs(
            current_match_data["timeline"],
            player_id)

        cs_diff, gold_diff, kills_diff, assists_diff, deaths_diff, damage_done_diff, damage_received_diff = np.diff(
            cs), np.diff(gold), np.diff(kills), np.diff(assists), np.diff(deaths), np.diff(
            damage_done), np.diff(damage_received)

        # Combine the arrays into a single feature matrix
        feature_matrix = np.column_stack((cs_diff, gold_diff, kills_diff, assists_diff, deaths_diff, damage_done_diff,
                                         damage_received_diff))

        # Define criteria for labeling weak points (you can customize these criteria)
        low_cs_threshold = 7
        high_deaths_threshold = 2

        # Create labels for weak and strong minutes based on criteria
        labels = ["weak" if (cs_diff[i] < low_cs_threshold) or (deaths_diff[i] > high_deaths_threshold) else "strong"
                  for i in
                  range(len(cs_diff))]

        # Split data into training and testing sets
        X_train, X_test, y_train, y_test = train_test_split(feature_matrix, labels, test_size=0.2, random_state=42)

        # Train a Random Forest classifier (you can use other classifiers as well)
        classifier = RandomForestClassifier(n_estimators=100, random_state=42)
        classifier.fit(X_train, y_train)

        # Predict weak points using the trained model
        predictions = classifier.predict(X_test)

        # Calculate accuracy on the test set (optional)
        accuracy = accuracy_score(y_test, predictions)
        print(f"Model Accuracy: {accuracy:.2f}")

        # Highlight weak minutes based on model predictions
        weak_minutes = [i for i, prediction in enumerate(predictions) if prediction == "weak" and i > 2]
        print(f"Weak Minutes Predicted by the Model: {weak_minutes}")

        game_duration = current_match_data['match']["info"]["gameDuration"] / 60

        average_cs = cs[-1] / game_duration
        average_gold = gold[-1] / game_duration
        average_kills = kills[-1] / game_duration
        average_assists = assists[-1] / game_duration
        average_deaths = deaths[-1] / game_duration
        average_damage_done = damage_done[-1] / game_duration
        average_damage_received = damage_received[-1] / game_duration

        # Pretty print results
        print("--------------------------------------------------------")
        print("--------------------------------------------------------")
        print("--------------------------------------------------------")
        print(f"# Game meta data")
        print(f"Length: {game_duration:.0f}")
        current_player_data = current_match_data['match']['info']['participants'][player_index]
        print(f"Character: {current_player_data['championName']}")
        print(f"Lane: {current_player_data['individualPosition']}")
        print(f"KDA: {current_player_data['challenges']['kda']}")

        print(f"# Per minute statistics")
        print(f"CS: {average_cs:.2f} per minute")
        print(f"Gold: {average_gold:.2f} per minute")
        print(f"Kills: {average_kills:.2f} per minute")
        print(f"Assists: {average_assists:.2f} per minute")
        print(f"Deaths: {average_deaths:.2f} per minute")
        print(f"Damage Done: {average_damage_done:.2f} per minute")
        print(f"Damage Received: {average_damage_received:.2f} per minute")

        # Iterate through weak minutes and print stats in a human-readable form
        print(f"# Weak Points in my game")
        for minute_idx in weak_minutes:
            print(f"## Minute {minute_idx}: Weak Point Stats")
            print("--------------------------------------------------------")

            print(f"- CS total: {cs[minute_idx]:.2f}")
            print(f"- CS Diff (compared to previous minute): {cs_diff[minute_idx]:.2f}")
            print(f"- Gold total: {gold[minute_idx]:.2f}")
            print(f"- Gold Diff (compared to previous minute): {gold_diff[minute_idx]:.2f}")
            print(f"- Kills total: {kills[minute_idx]:.2f}")
            print(f"- Kills Diff (compared to previous minute): {kills_diff[minute_idx]:.2f}")
            print(f"- Assists total: {assists[minute_idx]:.2f}")
            print(f"- Assists Diff (compared to previous minute): {assists_diff[minute_idx]:.2f}")
            print(f"- Deaths total: {deaths[minute_idx]:.2f}")
            print(f"- Deaths Diff (compared to previous minute): {deaths_diff[minute_idx]:.2f}")
            print(f"- Damage done total: {damage_done_diff[minute_idx]:.2f}")
            print(f"- Damage Done Diff (compared to previous minute): {damage_done_diff[minute_idx]:.2f}")
            print(f"- Damage received total: {damage_received_diff[minute_idx]:.2f}")
            print(f"- Damage Received Diff (compared to previous minute): {damage_received_diff[minute_idx]:.2f}")

            print("\n")


if __name__ == '__main__':
    main()
