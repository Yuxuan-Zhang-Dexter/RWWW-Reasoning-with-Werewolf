class Role:
    def __init__(self, name, description, actions, win_condition, player, target):
        self.name = name
        self.description = description
        self.actions = actions
        self.win_condition = win_condition
        self.chat_history = []
        self.player = player
        self.target = target
    
    def update_chat_history(self, prompt):
        self.chat_history += prompt