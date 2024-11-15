from players import Villager, Werewolf, Prophet
import json
import random
from openai import OpenAI
from collections import Counter
import re
import uuid
import os
from datetime import datetime

class GameSession:
    def __init__(self, config):
        self.model = config['model']
        self.session_id = str(uuid.uuid4())
        self.config = config
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

    def end_game_save_history(self, winning_team):
        """Ends the game and saves both individual and global histories."""
        self.output_individual_chat_histories(winning_team)
        self.output_global_chat_history(winning_team)


    def play_round(self):
        print(f"Round {self.track_round}: Day Phase - Discussion and Voting")
        self.handle_day_phase()
        
        # Check win conditions after daytime
        winning_team, printinfo = self.check_game_end_conditions()
        if winning_team:
            self.end_game_save_history(winning_team)
            return

        # Night Phase
        self.phase = "Night"
        print(f"Round {self.track_round}: Night Phase - Werewolf acts, Prophet reveals")
        self.handle_night_phase()

        # Check win conditions after nighttime
        winning_team = self.check_game_end_conditions()
        if winning_team:
            self.end_game_save_history(winning_team)
            return

    
    def play_rounds(self):
        """Continuously plays rounds until a winning team is determined."""
        while True:
            self.play_round()
            winning_team, printinfo = self.check_game_end_conditions()
            if winning_team:
                print(printinfo)
                break
            self.track_round += 1
            # If play_round finds a winner and ends the game, exit the loop

    def generate_discussion_prompt(self, player, role, action_type):
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

    
    def get_response_from_openai(self, messages, temp = 0.7):
        client = OpenAI()
        response = client.chat.completions.create(
            model = self.model,
            messages = messages,
            max_tokens=100,
            temperature=temp
        )

        return response.choices[0].message.content
    
    def update_alive_player_history(self, prompt):
        for player in sorted(self.alive_players):
            role = self.players[player]
            role.update_chat_history(prompt)

    
    def handle_day_phase(self):
        self.votes = {player: None for player in self.alive_players}
        # Discussion Session
        discussion_history = ''
        for player in sorted(self.alive_players):
            role = self.players[player]
            # get prompt
            if discussion_history != '':
                generated_prompt = [{'role': 'user', 'content':  f'In the {self.track_round} round, previous players have already a discussion: {discussion_history} ' + self.generate_discussion_prompt(player, role, 'discussion')}]
            else:
                generated_prompt = [{'role': 'user', 'content':  self.generate_discussion_prompt(player, role, 'discussion')}]
            response = self.get_response_from_openai(role.chat_history + generated_prompt)
            print(f"{player}: {response}")
            # update role chat history and discussion chat history
            generated_prompt += [{'role': 'system', 'content': response}]
            discussion_history +=  f" {player}: {response} "
            role.update_chat_history(generated_prompt)
        
        discussion_history_summary = [{'role': 'user', 'content': f'In the {self.track_round} round, we summarize today discussion as pre-knowledge for the future discussion here: {discussion_history}'}]
        self.update_alive_player_history(discussion_history_summary)

        # Voting and eliminating section
        self.conduct_voting()
    
    def conduct_voting(self):
        if self.track_round == 1:
            print("The first daytime is peaceful. Everyone should love each other and don't be such agressive. Love and Peace!!!")
            first_round_prompt = [{'role': 'system', 'content': f"No one will vote in the first round."}]
            self.update_alive_player_history(first_round_prompt)
            return
        
        for player in self.alive_players:
            role = self.players[player]
            suspect = self.get_vote_from_openai(player, role)
            self.votes[player] = suspect
            print(f"{role.name} {player} votes for {suspect}")
            role.update_chat_history([{'role': 'system', 'content': f"{role.name} {player} votes for {suspect}"}])

        # Tally votes and determine if there's a tie
        if not self.tally_votes_and_eliminate():
            print("A voting tie occurred so no one was voted out.")
            vote_decision = [{'role': 'user', 'content': "A voting tie occurred so no one was voted out."}]
            self.update_alive_player_history(vote_decision)
 

        
    def get_vote_from_openai(self, player, role):
        alive_players_list = list(self.alive_players - {player})  # Players can vote for any other alive player except themselves
        vote_prompt = [{'role': 'user', 'content': f"{player}, please provide only the name of the player you suspect is the Werewolf. Your options are: {', '.join(alive_players_list)}. No explanations, please. Restrict reply to be player[number], like player1, player2, player3..."}]
        response = self.get_response_from_openai(role.chat_history + vote_prompt, temp = 0.1)
        vote = response.strip().lower()
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
            vote_decision = [{'role': 'user', 'content': f"{most_voted_player} is eliminated with {most_votes} votes."}]
            self.update_alive_player_history(vote_decision)
            self.alive_players.remove(most_voted_player)
            self.check_game_end_conditions()
            return True  # Elimination successful
        else:
            # If there is a tie, return False to indicate re-voting is needed
            return False
  
    
    def handle_night_phase(self):
        # Prophet reveal identity
        if len([player for player in self.alive_players if self.players[player].name == "Prophet"]) > 0:
            prophet = [player for player in self.alive_players if self.players[player].name == "Prophet"][0]
            self.prophet_reveal(prophet)

        # Werewolf chooses a player to eliminate
        werewolf = [player for player in self.alive_players if self.players[player].name == "Werewolf"][0]
        target = self.get_werewolf_target(werewolf)
        print(f"Werewolf {werewolf} eliminates {target}.")
        self.update_alive_player_history([{'role': 'user', 'content': f"Werewolf eliminates {target}."}])
        if target in self.alive_players:
            self.alive_players.remove(target)

        # Check for game end conditions
        self.check_game_end_conditions()
    
    def get_werewolf_target(self, werewolf):
        # Generate a prompt asking the Werewolf to choose a target to eliminate
        werewolf_role = self.players[werewolf]
        target_prompt = [{'role': 'user', 'content': f"{werewolf}, please only output one name from alive players {self.alive_players} you want to eliminate, and please do not provide any explanation. Restrict reply to player[number], like player1, player2, player3..."}]
        response = self.get_response_from_openai(werewolf_role.chat_history + target_prompt, temp = 0.1)
        target = response.strip().lower()

        # update werewolf chat history
        response_prompt = [{'role': 'system', 'content': target}]
        werewolf_role.update_chat_history(target_prompt + response_prompt)
        return target

    def prophet_reveal(self, prophet):
        # Generate a prompt asking the Prophet to reveal one player's identity
        prophet_role = self.players[prophet]
        reveal_prompt = [{'role': 'user', 'content': f"{prophet}, please only output one name from the alive player {self.alive_players} you want to reveal identity, and please do not provide any explanation. Restrict reply to player[number], like player1, player2, player3..."}]
        response = self.get_response_from_openai(prophet_role.chat_history + reveal_prompt, temp = 0.1)
        target = response.strip().lower()
        revealed_role = self.players[target].name
        result_prompt = f"Prophet {prophet} reveals that {target} is a {revealed_role}."
        print(result_prompt)
        # Prophet can use this information in subsequent discussions
        prophet_role.update_chat_history(reveal_prompt + [{'role':'system', 'content': result_prompt}])
    
    def check_game_end_conditions(self):
        """Checks if the game has ended and returns the winning team if so."""
        werewolf_alive = any(self.players[player].name == "Werewolf" for player in self.alive_players)
        villagers_alive = any(self.players[player].name == "Villager" or self.players[player].name == "Prophet" for player in self.alive_players)

        if not werewolf_alive:
            return "Villagers", "Villagers win!"
        elif not villagers_alive:
            return "Werewolves", "Werewolf wins!"
        elif len(self.alive_players) == 2:
            alive_roles = [self.players[player].name for player in self.alive_players]
            if "Werewolf" in alive_roles and ("Villager" in alive_roles or "Prophet" in alive_roles):
                return "Werewolves", "Werewolf wins! Only one Villager remains against the Werewolf."

        # Return None if the game has not ended
        return None, None
    
    def output_individual_chat_histories(self, winning_team, directory="output/individual_histories"):
        os.makedirs(directory, exist_ok=True)
        for player, role in self.players.items():
            history_file = os.path.join(directory, f"{player}_history.json")
            player_history = {
                "session_id": self.session_id,
                "timestamp": datetime.now().isoformat(),
                "model_name": self.model,
                "role": role.name,
                "total_rounds": self.track_round,
                "winning_team": winning_team,
                "chat_history": role.chat_history
            }
            full_history = {}
            if os.path.exists(history_file):
                with open(history_file, 'r') as f:
                    full_history = json.load(f)
            full_history[self.session_id] = player_history
            with open(history_file, 'w') as f:
                json.dump(full_history, f, indent=2)
          

    def output_global_chat_history(self, winning_team, directory="output/global_history"):
        """Outputs the global chat history with session metadata to a JSON file, removing duplicate entries."""
        os.makedirs(directory, exist_ok=True)
        global_history_file = os.path.join(directory, f"game_session_{self.session_id}.json")
        
        # Collect player roles
        player_roles = {player: role.name for player, role in self.players.items()}
        
        # Gather all chat histories from players, removing duplicates
        combined_chat_history = []
        seen_messages = set()  # Track unique messages
        
        for role in self.players.values():
            for entry in role.chat_history:
                # Convert each entry to a JSON string for uniqueness tracking
                message_content = json.dumps(entry, sort_keys=True)
                if message_content not in seen_messages:
                    combined_chat_history.append(entry)
                    seen_messages.add(message_content)  # Mark as seen

        # Organize data structure for global chat history
        global_history_data = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "model_name": self.model,
            "player_roles": player_roles,
            "total_rounds": self.track_round,
            "winning_team": winning_team,
            "chat_history": combined_chat_history  # Deduplicated combined chat history
        }

        # Write the global history to a JSON file
        with open(global_history_file, 'w') as f:
            json.dump(global_history_data, f, indent=2)

            
   