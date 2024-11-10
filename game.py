from players import Villager, Werewolf, Prophet
import json
import random
from openai import OpenAI

class GameSession:
    def __init__(self, config):
        self.model = config['model']
        self.config = config
        # self.roles = self.initialize_roles(config["game_settings"]["roles"])
        self.players = self.assign_roles_to_players(config["game_settings"]["player_count"])
        self.phase = "Day"
        self.votes = {}
        self.alive_players = set(self.players.keys())
        self.system_prompt = config['game_settings']['system_prompt']
        self.track_round = 1

    def initialize_role(self, role_name, player):
        if role_name == "Villager":
            return Villager(player)
        elif role_name == "Werewolf":
            return Werewolf(player)
        elif role_name == "Prophet":
            return Prophet(player)

    def assign_roles_to_players(self, player_count):
        players = {}
        role_names = ["Villager"] * 3 + ["Werewolf"] + ["Prophet"]
        random.shuffle(role_names)
        for i in range(player_count):
            role = role_names.pop()
            players[f"Player_{i + 1}"] = self.initialize_role(role, f'Player_{i + 1}')
        return players

    def display_player_roles(self):
        for player, role in self.players.items():
            print(f"{player} is assigned the role: {role.name}")

    def initialize_agent_response(self):
        client = OpenAI()
        system_message = [
                {"role": "system", "content": self.system_prompt[0]}
            ]
        completion = client.chat.completions.create(
            model = self.model,
            messages = system_message,
            max_tokens=50,
            temperature=0.7
        )
        print(f"Verify Initialization: {completion.choices[0].message.content}")
        # updates each role's chat history with game rule
        for player, role in self.players.items():
            system_message += [{"role": "system", "content": role.description}]
            role.update_chat_history(system_message)


    def play_round(self):
        if self.phase == "Day":
            print("Day Phase: Discussion and Voting")
            self.handle_day_phase()
            self.phase = "Night"
        # elif self.phase == "Night":
        #     print("Night Phase: Werewolf acts, Prophet reveals")
        #     self.handle_night_phase()
        #     self.phase = "Day"
        self.track_round += 1
        
    def generate_prompt(self, player, role, action_type):
        if action_type == "discussion":
            return (
            f"You are playing the role of a {role.name} as {player} in a game of Werewolf. Your objective is to fulfill your role's "
            f"unique goals without revealing your true identity. It is the discussion phase, and your task is to discuss "
            f"who might be the suspicious Werewolf based on the interactions and statements of other players.\n\n"
            f"Role-specific guidance:\n"
            f"- As a {role.name}, {role.actions['discussion']} Use subtlety and strategy to stay in character and "
            f"avoid giving away too much information.\n"
            f"- Aim to guide the discussion while keeping your role hidden, and focus on achieving your win condition: {role.win_condition}.\n\n"
            f"Engage in the discussion phase with careful observations and strategic statements. Stay in character and "
            f"use your role's traits to fulfill your objective!"
            f"Please based on discussion mentioned above. and Please be concise and say a few sentences, one or two sentences"
        )
        # elif action_type == "night" and role.name == "Werewolf":
        #     return f"You are the Werewolf. It’s the Night phase. Choose one player to eliminate from the game."
        # elif action_type == "reveal" and role.name == "Prophet":
        #     return f"You are the Prophet. It’s the Night phase. Choose one player to reveal their role."

    
    def get_response_from_openai(self, messages):
        client = OpenAI()
        response = client.chat.completions.create(
            model = self.model,
            messages = messages,
            max_tokens=100,
            temperature=0.7
        )

        return response.choices[0].message.content
    
    def handle_day_phase(self):
        self.votes = {player: None for player in self.alive_players}
        # Discussion Session
        discussion_history = ''
        for player in sorted(self.alive_players):
            role = self.players[player]
            # get prompt
            generated_prompt = ''
            if not discussion_history: # if first to discuss
                generated_prompt = [{'role': 'user', 'content':  f'It is your turn to discuss. In round {self.track_round}, you are the first to discuss. ' + self.generate_prompt(player, role, 'discussion')}]    
            else:
                generated_prompt = [{'role': 'user', 'content':  f'It is your turn to discuss. In round {self.track_round}, previous players have already a discussion: {discussion_history} ' + self.generate_prompt(player, role, 'discussion')}]
            response = self.get_response_from_openai(role.chat_history + generated_prompt)
            print(f"{player}: {response}")
            # update role chat history and discussion chat history
            generated_prompt += [{'role': 'system', 'content': response}]
            discussion_history +=  f" {player}: {response} "
            role.update_chat_history([{'role': 'system', 'content': f'In Round {self.track_round}, you said: ' + response}])
        for player in sorted(self.alive_players):
            role = self.players[player]
            role.update_chat_history([{'role': 'system', 'content': f'In Round {self.track_round}, this is what everyone said. {discussion_history}'}])
        


            
            
            
            
        # # Vote
        # vote = self.get_response_from_openai(player, "day")
        # self.votes[player] = vote
        # print(f"{player} votes to eliminate {vote}.")
        # self.resolve_votes()

    # def handle_night_phase(self):
    #     werewolf = self.get_role_player("Werewolf")
    #     prophet = self.get_role_player("Prophet")
    #     if werewolf and prophet:
    #         # Werewolf action
    #         target = self.get_response_from_openai(werewolf, "night")
    #         print(f"Werewolf chooses to kill {target}.")
    #         self.alive_players.remove(target)
    #         # Prophet action
    #         reveal_target = self.get_response_from_openai(prophet, "reveal")
    #         print(f"Prophet discovers {reveal_target}'s role is {self.players[reveal_target].name}.")

    # def resolve_votes(self):
    #     vote_counts = {}
    #     for voter, target in self.votes.items():
    #         vote_counts[target] = vote_counts.get(target, 0) + 1
    #     if vote_counts:
    #         eliminated = max(vote_counts, key=vote_counts.get)
    #         print(f"{eliminated} is eliminated.")
    #         self.alive_players.remove(eliminated)

    # def get_role_player(self, role_name):
    #     for player, role in self.players.items():
    #         if role.name == role_name and player in self.alive_players:
    #             return player
    #     return None

    # def check_win_conditions(self):
    #     werewolf_alive = any(role.name == "Werewolf" for role in self.players.values() if role in self.alive_players)
    #     villagers_and_prophet_alive = any(role.name in ["Villager", "Prophet"] for role in self.players.values() if role in self.alive_players)

    #     if not werewolf_alive:
    #         print("Villagers and Prophet win!")
    #         return True
    #     elif not villagers_and_prophet_alive:
    #         print("Werewolf wins!")
    #         return True
    #     return False

    # def get_response_from_openai(self, player, action_type):
    #     role = self.players[player]
    #     prompt = self.generate_prompt(player, role, action_type)
    #     response = openai.ChatCompletion.create(
    #         model=self.config["model"],
    #         messages=[{"role": "system", "content": prompt}],
    #         max_tokens=50,
    #         temperature=0.7
    #     )
    #     return response.choices[0].message["content"]

    # def generate_prompt(self, player, role, action_type):
    #     if action_type == "day":
    #         return f"You are {role.name}. It’s the Day phase, and you must vote to eliminate a suspicious player. Who do you suspect?"
    #     elif action_type == "night" and role.name == "Werewolf":
    #         return f"You are the Werewolf. It’s the Night phase. Choose one player to eliminate from the game."
    #     elif action_type == "reveal" and role.name == "Prophet":
    #         return f"You are the Prophet. It’s the Night phase. Choose one player to reveal their role."