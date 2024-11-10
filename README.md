# RWWW - Reasoning with Werewolf

RWWW (Reasoning with Werewolf) is a Python-based simulation of the popular social deduction game *Werewolf*, where AI agents take on roles and interact within the game's logical framework. The project explores reasoning, deception, and strategic deduction in an AI-driven Werewolf game setting.

## Project Overview

The project currently supports:
- **Game Session Logic**: The main game logic is encapsulated in `game.py`, which sets up a game session with different roles, prompts, and interactions.
- **Daytime Discussion Phase**: Players engage in discussions to deduce each other’s roles.
- **Test Script**: `test.py` allows you to run a sample game session.

## Setup and Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/RWWW-Reasoning-with-Werewolf.git
   cd RWWW-Reasoning-with-Werewolf
   ```

2. **Install Dependencies**:
   Use the `requirements.txt` file to install the necessary packages:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set Up OpenAI API Key**: 
   Set the OpenAI API key in your environment. You can do this by adding it to your .bashrc, .zshrc, or equivalent configuration file:
   ```bash
   export OPENAI_API_KEY="your_openai_api_key_here"
   ```

## Running the Game

To start a game session and see the current implementation in action, run:
```bash
python test.py
```

The output will display players discussing who they suspect to be the Werewolf, based on the prompts generated in `game.py`.

## Project Progress

### Current Implementation

1. **Daytime Discussion Phase**:
   - Each player discusses and attempts to deduce who might be the Werewolf, based on role-specific prompts.
   
2. **Role-Based Actions**:
   - Players (AI agents) are assigned specific roles (Villager, Werewolf, Prophet), each with unique actions and win conditions.

3. **Prompt Generation**:
   - Initial prompts guide each role's behavior during discussions. This allows each AI agent to align its responses with its assigned role.

### Next Steps

1. **Implementing the Night Phase**:
   - Add Werewolf elimination logic and Prophet’s nightly revelation of one player’s identity.

2. **Game Logic Enhancements**:
   - Develop voting mechanics and victory conditions to complete the gameplay loop.
   - Enable player elimination based on the discussions and voting outcomes.

3. **Prompt Optimization**:
   - Improve prompt structures to enhance each role’s reasoning and alignment with game strategies.
   - Experiment with prompt variations for better AI-driven interaction.

## Contributing

Contributions to improve the game logic, prompts, or features are welcome! To contribute:

1. **Fork the Repository** and create a new branch for your changes.
2. Make your changes and ensure they align with the project goals.
3. **Submit a Pull Request** with a clear description of your updates.

## License

This project is licensed under the MIT License.
