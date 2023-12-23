import requests
import numpy as np
import pandas as pd
from tqdm import tqdm
import math

def safe_get(dct, keys, default=np.NaN):
    """
    Safely get nested keys from a dictionary, return default if any key is not found.
    :param dct: dictionary to extract data from
    :param keys: dictionary keys to retrieve data
    :param default: return if any key is not found
    :return:
    """
    # Reference https://stackoverflow.com/questions/25833613/safe-method-to-get-value-of-nested-dictionary
    for key in keys:
        try:
            dct = dct[key]
        except (KeyError, TypeError):
            return default
    return dct





def fetch_game_data(game_id):
    """
    Fetch game data for a specific game_id.
    :param game_id: The game id to fetch data for
    :return: JSON data of the game or None if request fails
    """
    response = requests.get(f"https://api-web.nhle.com/v1/gamecenter/{game_id}/play-by-play")
    if response.status_code == 200:
        return response.json()
    else:
        print(f'Failed to get data for game {game_id}')
        return None


def clean_row(row):
    plays = []
    all_play_list = row["plays"]

    for play in all_play_list:
        if play["typeDescKey"] in [
            "blocked-shot",
            "shot-on-goal",
            "missed-shot",
            "goal",
        ]:
            # Teams information
            home_team_name = row["homeTeam"]["name"]["default"]
            home_team_id = row["homeTeam"]["id"]
            away_team_name = row["awayTeam"]["name"]["default"]
            away_team_id = row["awayTeam"]["id"]

            #Score information
            home_team_goals = row["homeTeam"]["score"]
            away_team_goals = row["awayTeam"]["score"]

            # Processing of Situation Code
            situation_Code = safe_get(play, ["situationCode"])
            away_team_gk = situation_Code[0]
            away_team_players = situation_Code[1]
            home_team_players = situation_Code[2]
            home_team_gk = situation_Code[3]

            # Checking if the net is empty or not
            event_Owner_id = safe_get(play, ["details", "eventOwnerTeamId"])
            if event_Owner_id == home_team_id:
                if home_team_gk == "1":
                    empty_net = 0
                else:
                    empty_net = 1
            else:
                if away_team_gk == "1":
                    empty_net = 0
                else:
                    empty_net = 1

            play_data = {
                "gameID": row["id"],
                "period": safe_get(play, ["period"]),
                "period_type": safe_get(play, ["periodDescriptor", "periodType"]),
                "period_time": safe_get(play, ["timeInPeriod"]),
                "home_team_name": home_team_name,
                "home_team_id": home_team_id,
                "away_team_name": away_team_name,
                "away_team_id": away_team_id,
                "shot_type": safe_get(play, ["details", "shotType"]),
                "event_type": safe_get(play, ["typeDescKey"]),
                "home_team_defending_side": safe_get(play, ["homeTeamDefendingSide"]),
                "x_coordinate": safe_get(play, ["details", "xCoord"]),
                "y_coordinate": safe_get(play, ["details", "yCoord"]),
                "event_owner_team_id": safe_get(play, ["details", "eventOwnerTeamId"]),
                "away_team_players": away_team_players,
                "home_team_players": home_team_players,
                "empty_net": empty_net,
                "home_score": home_team_goals,
                "away_score": away_team_goals,
            }
            plays.append(play_data)

    return plays


def determine_target_goal(df):
    team_shots = df["x_coordinate"].mean()
    if team_shots > 0:
        return (89, 0)  # But ciblé est à la droite
    else:
        return (-89, 0)  # But ciblé est à la gauche

def calculate_distance(x, y, target_goal):
    dx = target_goal[0] - x
    dy = target_goal[1] - y
    return math.sqrt(dx**2 + dy**2)

def calculate_angle(x, y, target_goal):
    if target_goal == (89, 0):
        target_x = 89
    else:
        target_x = -89

    dx = target_x - x
    dy = 0 - y
    if dy == 0:
        angle = 90
    else:
        angle = math.degrees(math.asin(dx / math.sqrt(dx**2 + dy**2)))
    angle -= 360 if angle > 90 else 0
    angle = abs(angle)
    return angle

def add_new_features(df: pd.DataFrame):
    target_goal = determine_target_goal(df)
    df["distance_to_target_goal"] = df.apply(
        lambda x: calculate_distance(x["x_coordinate"], x["y_coordinate"], target_goal),
        axis=1
    )
    df["distance_to_target_goal"] = df["distance_to_target_goal"].apply(lambda x: round(x, 1))

    df["angle_to_target_goal"] = df.apply(
        lambda x: calculate_angle(x["x_coordinate"], x["y_coordinate"], target_goal), axis=1
    )
    df["angle_to_target_goal"] = df["angle_to_target_goal"].apply(lambda x: round(x, 1))

    df["is_goal"] = df["event_type"].apply(lambda x: 1 if x == "goal" else 0)

    return df



def get_data(game_id):
    response = fetch_game_data(game_id)
    rows = [response]
    df = pd.DataFrame(rows)
    extracted_data = df.apply(clean_row, axis=1)
    all_plays_list = [play for sublist in extracted_data for play in sublist]
    all_plays_df = pd.DataFrame(all_plays_list)
    all_plays_df = add_new_features(all_plays_df)

    return all_plays_df


def print_data(game_data):

    rows = [
        game_data,
    ]

    df = pd.DataFrame(rows)

    extracted_data = df.apply(clean_row, axis=1)

    all_plays_list = [play for sublist in extracted_data for play in sublist]
    all_plays_df = pd.DataFrame(all_plays_list)

    all_plays_df = add_new_features(all_plays_df)

    return all_plays_df


