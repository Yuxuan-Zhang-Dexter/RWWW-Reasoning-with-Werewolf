from .base_role import Role
class Werewolf(Role):
    def __init__(self, player):
        super().__init__(
            name="Werewolf",
            description="The Werewolf’s goal is to kill all Villagers and the Prophet without revealing their identity.Mimic the Prophet to mislead Villagers if necessary",
            actions={
                "discussion": "Cast doubt and redirect suspicions onto other players during discussions. Mimic prophet to mislead villagers if necessary as one optional strategy",
                "vote": "Vote strategically to avoid suspicion and eliminate players subtly.",
                "night": "Choose one player to eliminate during the Night phase."
            },
             win_condition="Werewolf eliminates enough Villagers and the Prophet to prevent opposition.",
            player=player
        )