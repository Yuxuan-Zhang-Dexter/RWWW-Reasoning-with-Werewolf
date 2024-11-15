from game import GameSession
import json
with open("./config/gpt-4o-mini-game-config.json", "r") as file:  # Replace "config.json" with your file path
    config = json.load(file)
 

game = GameSession(config)
game.display_player_roles()
game.initialize_agent_response()

game.play_rounds()