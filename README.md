# Terminal Games

A collection of classic games that run directly in your terminal!

## Pong

A classic Pong game implementation that runs in the terminal using Python's curses library.

### Features
- **Single player mode** with AI opponent
- **Two-player mode** for local multiplayer
- **Three difficulty levels**: Easy, Medium, Hard with dramatically different ball speeds
- Real-time ball physics with paddle collision
- **Smooth, fluid paddle movement** with acceleration and deceleration
- Score tracking (first to 10 points wins)
- AI with adjustable difficulty that scales with game difficulty
- Pause functionality
- Game over screen with restart option

### Controls
- **Single Player Mode**: Hold W/S keys to move your paddle up/down continuously
- **Two Player Mode**: Player 1 (hold W/S), Player 2 (hold Up/Down arrows)
- **M**: Switch between single player and two player modes
- **D**: Cycle through difficulty levels (Easy → Medium → Hard → Easy)
- **Spacebar**: Pause/unpause the game
- **Q**: Quit the game
- **R**: Restart after game over

**Note**: Hold down movement keys for continuous movement - no need to repeatedly tap!

### Requirements
- Python 3.x
- Terminal with at least 60x20 character display
- Color terminal support (recommended)

### How to Run
```bash
python pong.py
```

### Game Rules
- **Single Player**: You control the left paddle, computer controls the right
- **Two Player**: Left player uses W/S, right player uses arrow keys
- **Difficulty Levels**:
  - **Easy**: Slower ball speed, easier AI opponent
  - **Medium**: Moderate ball speed, balanced AI (default)
  - **Hard**: Very fast ball speed, challenging AI opponent
- The ball bounces off the top and bottom walls
- Players must hit the ball with their paddles to keep it in play
- If the ball goes past a paddle, the other player scores a point
- First player to reach 10 points wins the game
- The ball's angle changes based on where it hits the paddle
- Press M anytime to switch between single and two player modes
- Press D anytime to cycle through difficulty levels

### Technical Details
- Built with Python's `curses` library for terminal-based UI
- **Physics-based smooth movement** with velocity, acceleration, and time-based updates
- Real-time input handling with continuous key press detection
- Physics simulation with collision detection
- AI opponent with predictive movement and adjustable difficulty
- Smart AI that predicts ball trajectory and reacts accordingly
- Three-tier difficulty system affecting ball speed and AI performance
- Dynamic difficulty switching during gameplay
- Mode switching between single and multiplayer during gameplay
- High refresh rate (1ms) for ultra-smooth gameplay
- Color support for enhanced visual experience


this shit sucks
