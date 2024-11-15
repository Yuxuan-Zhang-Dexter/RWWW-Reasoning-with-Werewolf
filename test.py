from game import GameSession
import json
import os

with open("./config/gpt-4o-mini-game-config.json", "r") as file:  # Replace "config.json" with your file path
    config = json.load(file)

def set_secret():

    # Define the file name and the environment variable name
    file_name = "secret.txt"
    env_var_name = "OPENAI_API_KEY"

    # Check if the file exists
    if os.path.isfile(file_name):
        # Open the file and read the first line
        with open(file_name, 'r') as file:
            first_line = file.readline().strip()
            # Set the first line as an environment variable
            os.environ[env_var_name] = first_line
 
set_secret()

game = GameSession(config)
game.display_player_roles()
game.initialize_agent_response()

game.play_rounds()