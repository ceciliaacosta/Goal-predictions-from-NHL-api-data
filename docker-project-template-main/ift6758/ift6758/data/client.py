import math
import requests
from pandas import json_normalize
from functions import *

class LiveGameClient:
    # ... (le reste du code)
    def __init__(self):
        self.base_url = "https://api-web.nhle.com/v1/gamecenter/"
        self.processed_events = set()  # Track processed events using a set

    def get_live_game_events(self, game_id):
        """
        Get live game events for the specified game_id.
        Args:
            game_id (str): The ID of the game.
        Returns:
            list: List of unprocessed events.
        """
        url = f"{self.base_url}{game_id}/play-by-play"
        response = requests.get(url)

        if response.status_code == 200:
            live_game_data = response.json()
            nested_data = live_game_data.get('plays', {})    
            # Normalize the nested data into a DataFrame
            df = json_normalize(nested_data)
            # Extract specific columns
            selected_columns =["eventId", "details.yCoord", "details.xCoord", "situationCode", "details.eventOwnerTeamId","typeDescKey","eventOwnerTeamId","period"]
            df = df[selected_columns]
            return df
        else:
            raise Exception(f"Failed to fetch live game events. Status code: {response.status_code}")

    def filter_processed_events(self, events):
        """
        Filter out events that have already been processed.
        Args:
            events (list): List of events.

        Returns:
            list: List of unprocessed events.
        """
        return [event for event in events if event['eventId'] not in self.processed_events]
    

    
    def process_live_game(self, game_id):
        """
        Process live game events.
        Args:
            game_id (str): The ID of the game.
        """
        df = self.get_live_game_events(game_id)
        unprocessed_events = self.filter_processed_events(df['eventId'])
        df["is_empty_net"] = self.is_empty_net(df['situationCode'], df['eventOwnerTeamId'])
        # Calculate the Euclidean distance and angle for each shot and goal
        target_goals = df.groupby([['period',"eventOwnerTeamId", 'team.name']]).apply(determine_target_goal).reset_index(name='target_goal')
        # Merge the target goal information with the main data
        df = df.merge(target_goals, on=['period',"eventOwnerTeamId", 'team.name'])
        df["distance_to_target_goal"] = df.apply(
                lambda row: calculate_distance(row["details.xCoord"], row["details.yCoord"], (89, 0) if row["target_goal"] == 1 else (-89, 0)), 
                axis=1
            )
        df["angle_to_target_goal"] = df.apply(
                lambda row: calculate_angle(row["details.xCoord"], row["details.yCoord"], (89, 0) if row["target_goal"] == 1 else (-89, 0)), 
                axis=1
        )
        df["IsGoal"] = df["typeDescKey"].apply(lambda x: 1 if x == "GOAL" else 0)

        # Update the set of processed events
        self.processed_events.add(df['event_id'])




    def is_empty_net(self, situation_code, event_owner_team_id):
        """
        Check if it's an empty net situation.

        Args:
            situation_code (int): The situation code.
            event_owner_team_id (int): The event owner team ID.

        Returns:
            bool: True if it's an empty net, False otherwise.
        """
        # Extract relevant digits from the situation code
        away_goalie_present = situation_code // 1000 % 10 == 1
        home_goalie_present = situation_code % 10 == 1

        # Check if it's an empty net situation
        return (event_owner_team_id == 2 and away_goalie_present and not home_goalie_present) or \
               (event_owner_team_id == 1 and home_goalie_present and not away_goalie_present)

# Example usage:
live_game_client = LiveGameClient()
live_game_client.process_live_game("2022030411")
