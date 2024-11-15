from .base_role import Role
class Prophet(Role):
    def __init__(self, player):
        super().__init__(
            name="Prophet",
            description="The Prophet tries to discover the Werewolf by secretly revealing one player's identity each night and subtly guiding the Village toward the Werewolf.",
            actions={
                "discussion": "Participate in discussions, subtly guiding Villagers towards the Werewolf without revealing yourself.",
                "vote": "Vote based on gathered insights, aiming to eliminate the Werewolf.",
                "night": "Choose one player to reveal their true identity each Night phase."
            },
            win_condition="Werewolf is eliminated before they eliminate all Villagers and the Prophet.",
            player=player
        )

