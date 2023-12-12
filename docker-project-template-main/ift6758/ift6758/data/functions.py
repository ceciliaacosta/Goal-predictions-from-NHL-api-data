import pandas as pd 
import math

def determine_target_goal(data,coordinateX):
    team_shots = data[coordinateX].mean()
    # Determine the target goal based on the average coordinates.x
    if team_shots > 0:
        return 1  # Team primarily shoots in positive coordinates.x
    else:
        return 2  # Team primarily shoots in negative coordinates.x
    

# Create a function to calculate Euclidean distance
def calculate_distance(x, y, target_goal):
        dx = target_goal[0] - x
        dy = target_goal[1] - y
        return math.sqrt(dx**2 + dy**2)

# Create a function to calculate the angle in degrees relative to the goal
def calculate_angle(x, y, target_goal):
        if target_goal == (89, 0):
            target_x = 89
        else:
            target_x = -89
        
        dx = target_x - x
        dy = 0 - y  
        if dy == 0:
            # For the case where the point is on the vertical line (dy is zero)
            angle = 90  # Set to 90 degrees
        else:
            angle = math.degrees(math.asin(dx / math.sqrt(dx**2 + dy**2)))
        # Ensure the angle is in the range [0, 360]
        angle -= 360 if angle > 90 else 0
        angle = abs(angle)  # Ensure the angle is positive
        return angle