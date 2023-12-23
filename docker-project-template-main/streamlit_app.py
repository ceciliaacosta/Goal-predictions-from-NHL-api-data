import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image
import requests
from ift6758.data.client import GameClient
from api_data import print_data
from datetime import datetime
from ift6758.client.serving_client import *

gc = GameClient()
sclient = ServingClient(ip="serving", port="5050")

col1, col2 = st.columns(2)

with col1:
    st.write(" ")

with col2:
    st.write(" ")

# Title of the App
st.title("Hockey Visualisation")

with st.sidebar:
    # TODO: Add input for the sidebar
    st.sidebar.title("Selection Modele")

    workspace = st.text_input("Workspace", "francis75")
    side_model = st.sidebar.selectbox(
        "Modele", ("Distance", "Distance + Angle")
    )
    version = st.text_input("Version", value="1.0.0")

    get_model = st.button("Telecharger Modele")

    if side_model == "Distance + Angle":
        model = "regression3"
    elif side_model == "Distance":
        model = "regression1"

    if get_model:
        response = sclient.download_registry_model(
            model=model, workspace="francis75",version="1.0.0"
        )

        response = response["status"]

        st.markdown(
            f"{response}",
            unsafe_allow_html=True,
        )


user_input = st.text_input("Entrer ID")

button = st.button("Ping game")


if button:
    gd = gc.fetch_live_game_data(user_input)

    if gd == "vide":
        st.markdown(
            "Ce GameId n'existe pas",
            unsafe_allow_html=True,
        )
    else:
        away_team = gd["awayTeam"]["name"]["default"]
        home_team = gd["homeTeam"]["name"]["default"]

        year = int(user_input[0:4])
        gametype = user_input[4:6]
        if gametype == "01":
            g_type = "Regular season ##\n"
        elif gametype == "02":
            g_type = "All-Star ##\n"
        elif gametype == "03":
            g_type = "Playoffs ##\n"


        teams = f"{home_team} vs {away_team}"

        st.subheader(f"{teams}")

    data = print_data(gd)

    st.write(" ")
    st.write(" ")

    # st.slider("Event", len(data))

    st.markdown(
        f"{home_team} xG (actual)&emsp;&emsp;&emsp;&emsp;&emsp; {away_team} xG (actual)",
        unsafe_allow_html=True,
    )

    away_score = gd["awayTeam"]["score"]
    home_score = gd["homeTeam"]["score"]

    home_team_score = 0
    away_team_score = 0

    for index, row in data.iterrows():
        if row["is_goal"] == 1:
            if row["event_owner_team_id"] == row["home_team_id"]:
                home_team_score += 1
            else:
                away_team_score += 1
        data.at[index, "home_team_goals"] = home_team_score
        data.at[index, "away_team_goals"] = away_team_score

        if row["period"] in [1, 2, 3]:
            time_in_period = datetime.strptime("20:00", "%M:%S")
            time_played_in_period = datetime.strptime(row["period_time"], "%M:%S")

            time_left = time_in_period - time_played_in_period
            minutes, seconds = divmod(time_left.seconds, 60)
            formatted_time_left = f"{minutes:02d}:{seconds:02d}"

            data.at[index, "time_left_in_period"] = formatted_time_left
        else:
            time_in_period = datetime.strptime("05:00", "%M:%S")
            time_played_in_period = datetime.strptime(row["period_time"], "%M:%S")

            time_left = time_in_period - time_played_in_period
            minutes, seconds = divmod(time_left.seconds, 60)
            formatted_time_left = f"{minutes:02d}:{seconds:02d}"

            data.at[index, "time_left_in_period"] = formatted_time_left

    features = [
        "shot_type",
        "x_coordinate",
        "y_coordinate",
        "away_team_players",
        "home_team_players",
        "empty_net",
        "distance_to_target_goal",
        "angle_to_target_goal",
        "home_team_goals",
        "away_team_goals",
        "time_left_in_period",
        "prediction",
    ]
    columns= []

    df_shot = data[data["event_type"] == "shot-on-goal"]
    df_shot = df_shot.reset_index(drop=True)

    if side_model == "Distance + Angle":
        columns = ["distance_to_target_goal", "angle_to_target_goal"]
    elif side_model == "Distance":
        columns = ["distance_to_target_goal"]

    data = df_shot[columns].values
    df = pd.DataFrame(data, columns=columns)
    predictions = sclient.predict(df)

    df_shot = pd.concat([df_shot, predictions], axis=1)

    home_team_cum_prob = 0
    away_team_cum_prob = 0

    for index, row in df_shot.iterrows():
        if row["home_team_id"] == row["event_owner_team_id"]:
            home_team_cum_prob += row["prediction"]
        else:
            away_team_cum_prob += row["prediction"]

    difference_home = round(home_score - home_team_cum_prob, 2)
    difference_away = round(away_score - away_team_cum_prob, 2)

    if difference_away < 0:
        fleche_away = "↓"
    else:
        fleche_away = "↑"

    if difference_home < 0:
        fleche_home = "↓"
    else:
        fleche_home = "↑"
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"{round(home_team_cum_prob, 2)} ({home_score})", unsafe_allow_html=True)
        st.markdown(f"{fleche_home} {difference_home}", unsafe_allow_html=True)

    with col2:
        st.markdown(f"{round(away_team_cum_prob, 2)} ({away_score})", unsafe_allow_html=True)
        st.markdown(f"{fleche_away} {difference_away}", unsafe_allow_html=True)

    # st.markdown(
    #     f"{round(home_team_cum_prob, 2)} ({home_score})&emsp;&emsp;&emsp;&emsp;&emsp; {round(away_team_cum_prob, 2)} ({away_score})",
    #     unsafe_allow_html=True,
    # )

    # st.markdown(
    #     f"{fleche_home} {difference_home}&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp; {fleche_away} {difference_away}",
    #     unsafe_allow_html=True,
    # )

    st.write(df_shot[features])
