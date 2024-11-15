from .base_role import Role
class Villager(Role):
    def __init__(self, player):
        super().__init__(
            name="Villager",
            description="A Villager's goal is to find and eliminate the Werewolf by voting each round. Villagers may protect the Prophet when possible.",
            actions={
                "discussion": "Engage in discussions to identify suspicious behaviors and spot the Werewolf.",
                "vote": "Vote to eliminate players suspected of being the Werewolf."
            },
            win_condition="Werewolf is eliminated before they eliminate all Villagers and the Prophet.",
            player=player
        )
