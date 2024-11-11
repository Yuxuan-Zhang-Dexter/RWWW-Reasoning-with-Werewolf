from players import Villager, Werewolf, Prophet
import json
import random
from openai import OpenAI
from collections import Counter
import re

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
            players[f"player{i + 1}"] = self.initialize_role(role, f'player{i + 1}')
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
        for player, role in self.players.items():
            system_message += [{"role": "system", "content": role.description}]
            role.update_chat_history(system_message)


    def play_round(self):
        while True:
            if self.phase == "Day":
                print(f"Round {self.track_round}: Day Phase - Discussion and Voting")
                self.handle_day_phase()
                self.phase = "Night"
            elif self.phase == "Night":
                print(f"Round {self.track_round}: Night Phase - Werewolf acts, Prophet reveals")
                self.handle_night_phase()
                self.phase = "Day"
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
            generated_prompt = [{'role': 'user', 'content':  f'In the {self.track_round} round, previous players have already a discussion: {discussion_history} ' + self.generate_prompt(player, role, 'discussion')}]
            response = self.get_response_from_openai(role.chat_history + generated_prompt)
            print(f"{player}: {response}")
            # update role chat history and discussion chat history
            generated_prompt += [{'role': 'system', 'content': response}]
            role.update_chat_history(generated_prompt)
            discussion_history +=  f" {player}: {response} "
        
        # Voting and eliminating section
        self.conduct_voting()
    
    def conduct_voting(self):
        while True:  # Continue voting until a player is successfully eliminated
            # Each player votes for the player they suspect
            for player in self.alive_players:
                role = self.players[player]
                suspect = self.get_vote_from_openai(player, role)
                self.votes[player] = suspect
                print(f"{player} votes for {suspect}")

            # Tally votes and determine if there's a tie
            if not self.tally_votes_and_eliminate():
                print("A tie occurred, initiating re-vote...")
            else:
                break

        
    def get_vote_from_openai(self, player, role):
        alive_players_list = list(self.alive_players - {player})  # Players can vote for any other alive player except themselves
        vote_prompt = [{'role': 'user', 'content': f"{player}, please provide only the name of the player you suspect is the Werewolf. Your options are: {', '.join(alive_players_list)}. No explanations, please."}]
        response = self.get_response_from_openai(role.chat_history + vote_prompt)
        vote = response.strip().lower()
        print(vote)
        # if vote not in self.alive_players or vote == player:
        #     print(f"Invalid vote by {player} for {vote}. Re-voting...")
        #     return self.get_vote_from_openai(player, role)
        return vote
    
    def tally_votes_and_eliminate(self):
        vote_count = Counter(self.votes.values())
        most_voted_players = [player for player, count in vote_count.items() if count == max(vote_count.values())]
        most_votes = max(vote_count.values())

        if len(most_voted_players) == 1:
            # If there's only one player with the highest votes, they are eliminated
            most_voted_player = most_voted_players[0]
            match = re.search(r'player\d+', most_voted_player)
            if match:
                most_voted_player = match.group()
            print(f"{most_voted_player} is eliminated with {most_votes} votes.")
            self.alive_players.remove(most_voted_player)
            self.check_game_end_conditions()
            return True  # Elimination successful
        else:
            # If there is a tie, return False to indicate re-voting is needed
            return False
  
    
    def handle_night_phase(self):
        # Werewolf chooses a player to eliminate
        werewolf = [player for player in self.alive_players if self.players[player].name == "Werewolf"][0]
        target = self.get_werewolf_target(werewolf)
        print(f"Werewolf {werewolf} eliminates {target}.")
        if target in self.alive_players:
            self.alive_players.remove(target)

        if len([player for player in self.alive_players if self.players[player].name == "Prophet"]) > 0:
            prophet = [player for player in self.alive_players if self.players[player].name == "Prophet"][0]
            self.prophet_reveal(prophet)

        # Check for game end conditions
        self.check_game_end_conditions()
    
    def get_werewolf_target(self, werewolf):
        # Generate a prompt asking the Werewolf to choose a target to eliminate
        target_prompt = [{'role': 'user', 'content': f"{werewolf}, please only output the name of the player you want to eliminate, and please do not provide any explanation."}]
        response = self.get_response_from_openai(self.players[werewolf].chat_history + target_prompt)
        target = response.strip().lower()
        print("The werewolf removes: ", target)
        return target

    def prophet_reveal(self, prophet):
        # Generate a prompt asking the Prophet to reveal one player's identity
        reveal_prompt = [{'role': 'user', 'content': f"{prophet}, please only output the name of the player you want to reveal identity, and please do not provide any explanation."}]
        response = self.get_response_from_openai(self.players[prophet].chat_history + reveal_prompt)
        target = response.strip().lower()
        if target in self.alive_players:
            revealed_role = self.players[target].name
            print(f"Prophet {prophet} reveals that {target} is a {revealed_role}.")
            # Prophet can use this information in subsequent discussions
            self.players[prophet].update_chat_history([{'role': 'system', 'content': f"{target} is a {revealed_role}"}])
    
    def check_game_end_conditions(self):
        werewolf_alive = any(self.players[player].name == "Werewolf" for player in self.alive_players)
        villagers_alive = any(self.players[player].name == "Villager" or self.players[player].name == "Prophet" for player in self.alive_players)

        if not werewolf_alive:
            print("Villagers win! The Werewolf has been eliminated.")
            exit()
        elif not villagers_alive:
            print("Werewolf wins! All Villagers and the Prophet have been eliminated.")
            exit()
        elif len(self.alive_players) == 2:
            # If only two players remain, one Werewolf and one Villager, declare the Werewolf as the winner
            alive_roles = [self.players[player].name for player in self.alive_players]
            if "Werewolf" in alive_roles and ("Villager" in alive_roles or "Prophet" in alive_roles):
                print("Werewolf wins! Only one Villager remains against the Werewolf.")
                exit()


            
            
            
            
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