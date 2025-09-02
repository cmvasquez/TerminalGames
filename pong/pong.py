#!/usr/bin/env python3
"""
Terminal Pong Game
A classic Pong game that runs in the terminal using curses.

Controls:
- Single Player: W/S keys to move paddle up/down
- Two Player: Player 1 (W/S), Player 2 (Up/Down arrows)
- M to switch between single/two player modes
- D to cycle through difficulty levels (Easy/Medium/Hard)
- Q to quit the game

The game features:
- Single player mode with AI opponent
- Two player mode for local multiplayer
- Three difficulty levels with varying ball speeds
- A bouncing ball with physics
- Score tracking
- Game over when a player reaches 10 points
"""

import curses
import time
import random
import math
import threading
from collections import defaultdict

class PongGame:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.height, self.width = stdscr.getmaxyx()
        
        # Game settings
        self.target_score = 10
        self.single_player = True  # Start in single player mode
        
        # Difficulty settings
        self.difficulty_levels = ["Easy", "Medium", "Hard"]
        self.current_difficulty = 1  # Start with Medium (index 1)
        self.ball_speeds = [0.04, 0.02, 0.01]  # Much faster speeds for each difficulty
        self.ball_speed = self.ball_speeds[self.current_difficulty]
        
        # AI settings (adjust based on difficulty)
        self.ai_base_speed = 0.8
        self.ai_base_prediction = 0.3
        
        # Initialize game objects
        self.reset_game()
        
        # Set up initial difficulty settings
        self.update_difficulty_settings()
        
        # Set up curses for optimal input handling
        curses.curs_set(0)      # Hide cursor
        curses.noecho()         # Don't echo keys to screen
        curses.cbreak()         # React to keys immediately
        stdscr.nodelay(1)       # Non-blocking input
        stdscr.timeout(16)      # ~60 FPS refresh rate (16ms)
        stdscr.keypad(1)        # Enable special keys
        
        # Disable input buffering for better responsiveness
        if hasattr(curses, 'raw'):
            curses.raw()
        
        # Initialize colors if available
        if curses.has_colors():
            curses.start_color()
            curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
            curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
            curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)
            curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)
        
        # Key state tracking for continuous movement
        self.key_states = {
            'w': False, 's': False,
            'up': False, 'down': False
        }
        self.last_key_time = defaultdict(float)
        self.key_repeat_delay = 0.05  # 50ms between key repeats
        self.continuous_keys = set()  # Keys currently being held
    
    def reset_game(self):
        """Reset the game to initial state"""
        # Paddle settings
        self.paddle_height = 5
        self.paddle_width = 1
        
        # Player 1 (left paddle)
        self.p1_y = float(self.height // 2 - self.paddle_height // 2)
        self.p1_x = 2
        self.p1_score = 0
        self.p1_velocity = 0.0  # Current movement velocity
        
        # Player 2 (right paddle)
        self.p2_y = float(self.height // 2 - self.paddle_height // 2)
        self.p2_x = self.width - 3
        self.p2_score = 0
        self.p2_velocity = 0.0  # Current movement velocity
        
        # Paddle movement settings
        self.paddle_speed = 15.0  # Units per second
        self.paddle_acceleration = 50.0  # Acceleration when starting/stopping
        self.last_paddle_update = time.time()
        
        # Input state tracking
        self.p1_moving_up = False
        self.p1_moving_down = False
        self.p2_moving_up = False
        self.p2_moving_down = False
        
        # Ball settings
        self.reset_ball()
        
        # Game state
        self.game_over = False
        self.winner = None
        self.paused = False
        self.show_mode_change = False
        self.mode_change_time = 0
        self.show_difficulty_change = False
        self.difficulty_change_time = 0
    
    def reset_ball(self):
        """Reset ball position and velocity"""
        self.ball_x = self.width // 2
        self.ball_y = self.height // 2
        
        # Random starting direction
        angle = random.uniform(-math.pi/4, math.pi/4)  # -45 to 45 degrees
        if random.choice([True, False]):
            angle += math.pi  # Start going left instead of right
        
        # Increase base speed significantly and adjust by difficulty
        base_speed = 2.0  # Much faster base speed
        difficulty_speed_multipliers = [0.8, 1.0, 1.4]  # Easy, Medium, Hard
        speed = base_speed * difficulty_speed_multipliers[self.current_difficulty]
        
        self.ball_dx = speed * math.cos(angle)
        self.ball_dy = speed * math.sin(angle)
        
        self.last_ball_move = time.time()
    
    def update_difficulty_settings(self):
        """Update AI and game settings based on difficulty"""
        # Adjust AI difficulty based on game difficulty
        difficulty_multipliers = [0.6, 0.8, 1.0]  # Easy, Medium, Hard
        multiplier = difficulty_multipliers[self.current_difficulty]
        
        self.ai_speed = self.ai_base_speed * multiplier
        self.ai_prediction = self.ai_base_prediction * multiplier
        self.ball_speed = self.ball_speeds[self.current_difficulty]

    def cycle_difficulty(self):
        """Cycle through difficulty levels"""
        self.current_difficulty = (self.current_difficulty + 1) % len(self.difficulty_levels)
        self.update_difficulty_settings()
        self.show_difficulty_change = True
        self.difficulty_change_time = time.time()
        if not self.game_over:
            self.reset_game()

    def cycle_difficulty(self):
        """Cycle through difficulty levels"""
        self.current_difficulty = (self.current_difficulty + 1) % len(self.difficulty_levels)
        self.update_difficulty_settings()
        self.show_difficulty_change = True
        self.difficulty_change_time = time.time()
        if not self.game_over:
            self.reset_game()

    def update_paddle_movement(self):
        """Update paddle positions with smooth movement"""
        current_time = time.time()
        dt = current_time - self.last_paddle_update
        self.last_paddle_update = current_time
        
        # Cap delta time to prevent large jumps
        dt = min(dt, 0.1)
        
        # Update Player 1 paddle
        target_velocity_p1 = 0.0
        if self.p1_moving_up:
            target_velocity_p1 = -self.paddle_speed
        elif self.p1_moving_down:
            target_velocity_p1 = self.paddle_speed
        
        # Smooth acceleration/deceleration
        velocity_diff_p1 = target_velocity_p1 - self.p1_velocity
        if abs(velocity_diff_p1) > 0.1:
            acceleration_p1 = self.paddle_acceleration * (1 if velocity_diff_p1 > 0 else -1)
            self.p1_velocity += acceleration_p1 * dt
            # Clamp velocity to target
            if (velocity_diff_p1 > 0 and self.p1_velocity > target_velocity_p1) or \
               (velocity_diff_p1 < 0 and self.p1_velocity < target_velocity_p1):
                self.p1_velocity = target_velocity_p1
        else:
            self.p1_velocity = target_velocity_p1
        
        # Update position
        new_p1_y = self.p1_y + self.p1_velocity * dt
        if 1 <= new_p1_y <= self.height - self.paddle_height - 1:
            self.p1_y = new_p1_y
        else:
            self.p1_velocity = 0.0  # Stop at boundaries
        
        # Update Player 2 paddle (only if not AI controlled)
        if not self.single_player:
            target_velocity_p2 = 0.0
            if self.p2_moving_up:
                target_velocity_p2 = -self.paddle_speed
            elif self.p2_moving_down:
                target_velocity_p2 = self.paddle_speed
            
            # Smooth acceleration/deceleration
            velocity_diff_p2 = target_velocity_p2 - self.p2_velocity
            if abs(velocity_diff_p2) > 0.1:
                acceleration_p2 = self.paddle_acceleration * (1 if velocity_diff_p2 > 0 else -1)
                self.p2_velocity += acceleration_p2 * dt
                # Clamp velocity to target
                if (velocity_diff_p2 > 0 and self.p2_velocity > target_velocity_p2) or \
                   (velocity_diff_p2 < 0 and self.p2_velocity < target_velocity_p2):
                    self.p2_velocity = target_velocity_p2
            else:
                self.p2_velocity = target_velocity_p2
            
            # Update position
            new_p2_y = self.p2_y + self.p2_velocity * dt
            if 1 <= new_p2_y <= self.height - self.paddle_height - 1:
                self.p2_y = new_p2_y
            else:
                self.p2_velocity = 0.0  # Stop at boundaries

    def update_ai_paddle(self):
        """Update AI paddle position (Player 2 in single player mode)"""
        if not self.single_player or self.paused or self.game_over:
            return
        
        current_time = time.time()
        dt = current_time - self.last_paddle_update
        dt = min(dt, 0.1)  # Cap delta time
        
        # Calculate where the ball will be when it reaches the paddle
        if self.ball_dx > 0:  # Ball moving towards AI paddle
            # Predict ball position
            time_to_paddle = (self.p2_x - self.ball_x) / abs(self.ball_dx)
            predicted_y = self.ball_y + (self.ball_dy * time_to_paddle * self.ai_prediction)
            
            # Add some randomness to make AI beatable
            if random.random() < 0.1:  # 10% chance of random movement
                predicted_y += random.uniform(-2, 2)
        else:
            # Ball moving away, move towards center
            predicted_y = self.height // 2
        
        # Calculate desired paddle center position
        paddle_center = self.p2_y + self.paddle_height // 2
        target_center = predicted_y
        
        # Determine target velocity for AI
        distance_to_target = target_center - paddle_center
        target_velocity = 0.0
        
        if abs(distance_to_target) > 0.5:
            # AI moves at a speed proportional to distance and AI speed setting
            max_ai_speed = self.paddle_speed * self.ai_speed
            target_velocity = max_ai_speed * (1 if distance_to_target > 0 else -1)
            
            # Scale velocity based on distance for more natural movement
            velocity_scale = min(1.0, abs(distance_to_target) / 3.0)
            target_velocity *= velocity_scale
        
        # Smooth AI movement with acceleration
        velocity_diff = target_velocity - self.p2_velocity
        if abs(velocity_diff) > 0.1:
            ai_acceleration = self.paddle_acceleration * 0.8  # Slightly slower acceleration for AI
            acceleration = ai_acceleration * (1 if velocity_diff > 0 else -1)
            self.p2_velocity += acceleration * dt
            
            # Clamp velocity to target
            if (velocity_diff > 0 and self.p2_velocity > target_velocity) or \
               (velocity_diff < 0 and self.p2_velocity < target_velocity):
                self.p2_velocity = target_velocity
        else:
            self.p2_velocity = target_velocity
        
        # Update AI paddle position
        new_p2_y = self.p2_y + self.p2_velocity * dt
        if 1 <= new_p2_y <= self.height - self.paddle_height - 1:
            self.p2_y = new_p2_y
        else:
            self.p2_velocity = 0.0  # Stop at boundaries

    def update_ball(self):
        """Update ball position and handle collisions"""
        current_time = time.time()
        if current_time - self.last_ball_move < self.ball_speed:
            return
        
        self.last_ball_move = current_time
        
        # Update ball position
        self.ball_x += self.ball_dx
        self.ball_y += self.ball_dy
        
        # Ball collision with top and bottom walls
        if self.ball_y <= 1 or self.ball_y >= self.height - 2:
            self.ball_dy = -self.ball_dy
            self.ball_y = max(2, min(self.ball_y, self.height - 3))
        
        # Ball collision with paddles
        ball_int_x = int(round(self.ball_x))
        ball_int_y = int(round(self.ball_y))
        
        # Left paddle collision
        p1_int_y = int(round(self.p1_y))
        if (ball_int_x <= self.p1_x + self.paddle_width and 
            p1_int_y <= ball_int_y <= p1_int_y + self.paddle_height - 1 and
            self.ball_dx < 0):
            self.ball_dx = abs(self.ball_dx)  # Reverse X direction
            # Add some angle based on where it hit the paddle
            hit_pos = (ball_int_y - p1_int_y) / (self.paddle_height - 1)  # 0 to 1
            angle_modifier = (hit_pos - 0.5) * 0.5  # -0.25 to 0.25
            self.ball_dy += angle_modifier
            
        # Right paddle collision
        p2_int_y = int(round(self.p2_y))
        if (ball_int_x >= self.p2_x - 1 and 
            p2_int_y <= ball_int_y <= p2_int_y + self.paddle_height - 1 and
            self.ball_dx > 0):
            self.ball_dx = -abs(self.ball_dx)  # Reverse X direction
            # Add some angle based on where it hit the paddle
            hit_pos = (ball_int_y - p2_int_y) / (self.paddle_height - 1)  # 0 to 1
            angle_modifier = (hit_pos - 0.5) * 0.5  # -0.25 to 0.25
            self.ball_dy += angle_modifier
        
        # Scoring
        if self.ball_x < 0:
            self.p2_score += 1
            if self.p2_score >= self.target_score:
                self.game_over = True
                self.winner = "Player 2"
            else:
                self.reset_ball()
        elif self.ball_x > self.width:
            self.p1_score += 1
            if self.p1_score >= self.target_score:
                self.game_over = True
                self.winner = "Player 1"
            else:
                self.reset_ball()
    
    def draw_paddle(self, x, y):
        """Draw a paddle at the given position"""
        int_y = int(round(y))  # Convert float position to integer for drawing
        for i in range(self.paddle_height):
            paddle_y = int_y + i
            if 0 <= paddle_y < self.height:  # Bounds checking
                try:
                    self.stdscr.addstr(paddle_y, x, '█', curses.color_pair(1))
                except curses.error:
                    pass
    
    def draw_ball(self):
        """Draw the ball"""
        ball_int_x = int(round(self.ball_x))
        ball_int_y = int(round(self.ball_y))
        try:
            if 0 <= ball_int_x < self.width and 0 <= ball_int_y < self.height:
                self.stdscr.addstr(ball_int_y, ball_int_x, '●', curses.color_pair(2))
        except curses.error:
            pass
    
    def draw_center_line(self):
        """Draw the center line"""
        center_x = self.width // 2
        for y in range(1, self.height - 1, 2):
            try:
                self.stdscr.addstr(y, center_x, '│', curses.color_pair(1))
            except curses.error:
                pass
    
    def draw_borders(self):
        """Draw game borders"""
        # Top and bottom borders
        for x in range(self.width):
            try:
                self.stdscr.addstr(0, x, '─', curses.color_pair(1))
                self.stdscr.addstr(self.height - 1, x, '─', curses.color_pair(1))
            except curses.error:
                pass
    
    def draw_scores(self):
        """Draw the scores, game mode, and difficulty"""
        score_text = f"{self.p1_score}    {self.p2_score}"
        score_x = self.width // 2 - len(score_text) // 2
        try:
            self.stdscr.addstr(1, score_x, score_text, curses.color_pair(3))
        except curses.error:
            pass
        
        # Show game mode
        mode_text = "Single Player" if self.single_player else "Two Player"
        mode_x = self.width // 2 - len(mode_text) // 2
        try:
            self.stdscr.addstr(2, mode_x, mode_text, curses.color_pair(1))
        except curses.error:
            pass
        
        # Show difficulty
        difficulty_text = f"Difficulty: {self.difficulty_levels[self.current_difficulty]}"
        difficulty_x = self.width // 2 - len(difficulty_text) // 2
        try:
            self.stdscr.addstr(3, difficulty_x, difficulty_text, curses.color_pair(2))
        except curses.error:
            pass
        
        # Show temporary mode change notification
        if self.show_mode_change and time.time() - self.mode_change_time < 2:
            change_text = f"Switched to {mode_text} Mode!"
            change_x = self.width // 2 - len(change_text) // 2
            try:
                self.stdscr.addstr(4, change_x, change_text, curses.color_pair(2))
            except curses.error:
                pass
        else:
            self.show_mode_change = False
        
        # Show temporary difficulty change notification
        if self.show_difficulty_change and time.time() - self.difficulty_change_time < 2:
            diff_change_text = f"Difficulty: {self.difficulty_levels[self.current_difficulty]}!"
            diff_change_x = self.width // 2 - len(diff_change_text) // 2
            try:
                self.stdscr.addstr(5, diff_change_x, diff_change_text, curses.color_pair(3))
            except curses.error:
                pass
        else:
            self.show_difficulty_change = False
    
    def draw_instructions(self):
        """Draw game instructions"""
        if self.single_player:
            instructions = [
                "Player: W/S",
                "M: Two Player | D: Difficulty", 
                "Q: Quit | Space: Pause",
                f"First to {self.target_score} wins!"
            ]
        else:
            instructions = [
                "P1: W/S, P2: ↑/↓",
                "M: Single Player | D: Difficulty", 
                "Q: Quit | Space: Pause",
                f"First to {self.target_score} wins!"
            ]
        
        start_y = self.height - len(instructions) - 1
        for i, instruction in enumerate(instructions):
            try:
                self.stdscr.addstr(start_y + i, 1, instruction, curses.color_pair(1))
            except curses.error:
                pass
    
    def draw_game_over(self):
        """Draw game over screen"""
        if self.winner:
            if self.single_player:
                if "Player 1" in self.winner:
                    winner_text = "You Win!"
                else:
                    winner_text = "Computer Wins!"
            else:
                winner_text = f"{self.winner} Wins!"
            
            difficulty_name = self.difficulty_levels[self.current_difficulty]
            
            messages = [
                "GAME OVER!",
                winner_text,
                f"Final Score: {self.p1_score} - {self.p2_score}",
                f"Difficulty: {difficulty_name}",
                "",
                "Press R to restart",
                "Press M to change mode",
                "Press D to change difficulty",
                "Press Q to quit"
            ]
            
            start_y = self.height // 2 - len(messages) // 2
            for i, message in enumerate(messages):
                message_x = self.width // 2 - len(message) // 2
                try:
                    color = curses.color_pair(4) if i < 4 else curses.color_pair(3)
                    self.stdscr.addstr(start_y + i, message_x, message, color)
                except curses.error:
                    pass
    
    def handle_input(self):
        """Handle user input with proper continuous key press detection"""
        current_time = time.time()
        
        try:
            # Process all available key presses without blocking
            key_pressed = False
            while True:
                key = self.stdscr.getch()
                if key == -1:  # No more keys available
                    break
                
                key_pressed = True
                
                # Handle special action keys first
                if key == ord('q') or key == ord('Q'):
                    return False
                
                # Mode switching
                if key == ord('m') or key == ord('M'):
                    self.single_player = not self.single_player
                    self.show_mode_change = True
                    self.mode_change_time = time.time()
                    if not self.game_over:
                        self.reset_game()
                    continue
                
                # Difficulty switching
                if key == ord('d') or key == ord('D'):
                    self.cycle_difficulty()
                    continue
                
                if self.game_over:
                    if key == ord('r') or key == ord('R'):
                        self.reset_game()
                    continue
                
                # Pause/unpause
                if key == ord(' '):
                    self.paused = not self.paused
                    continue
                
                # Track movement keys for continuous input
                key_name = None
                if key == ord('w') or key == ord('W'):
                    key_name = 'w'
                    self.key_states['s'] = False  # Can't move both directions
                elif key == ord('s') or key == ord('S'):
                    key_name = 's'
                    self.key_states['w'] = False  # Can't move both directions
                elif key == curses.KEY_UP:
                    key_name = 'up'
                    self.key_states['down'] = False
                elif key == curses.KEY_DOWN:
                    key_name = 'down'
                    self.key_states['up'] = False
                
                if key_name:
                    self.key_states[key_name] = True
                    self.last_key_time[key_name] = current_time
                    self.continuous_keys.add(key_name)
            
            # Handle continuous key presses with timeout-based release detection
            key_timeout = 0.08  # 80ms timeout for key release detection
            
            for key_name in list(self.continuous_keys):
                # Check if key should be considered "released"
                if current_time - self.last_key_time[key_name] > key_timeout:
                    self.key_states[key_name] = False
                    self.continuous_keys.discard(key_name)
                else:
                    # Key is still being held, keep it active
                    self.key_states[key_name] = True
            
            # Update movement state based on current key states
            if not self.game_over and not self.paused:
                # Player 1 movement
                self.p1_moving_up = self.key_states['w']
                self.p1_moving_down = self.key_states['s']
                
                # Player 2 movement (only in two player mode)
                if not self.single_player:
                    self.p2_moving_up = self.key_states['up']
                    self.p2_moving_down = self.key_states['down']
                else:
                    self.p2_moving_up = False
                    self.p2_moving_down = False
            else:
                # Stop all movement when paused or game over
                self.p1_moving_up = False
                self.p1_moving_down = False
                self.p2_moving_up = False
                self.p2_moving_down = False
                
        except curses.error:
            pass
        
        return True
    
    def draw(self):
        """Draw the entire game"""
        self.stdscr.clear()
        
        # Draw game elements
        self.draw_borders()
        self.draw_center_line()
        self.draw_scores()
        
        if not self.game_over:
            self.draw_paddle(self.p1_x, self.p1_y)
            self.draw_paddle(self.p2_x, self.p2_y)
            if not self.paused:
                self.draw_ball()
            else:
                # Show pause message
                pause_msg = "PAUSED - Press SPACE to continue"
                pause_x = self.width // 2 - len(pause_msg) // 2
                try:
                    self.stdscr.addstr(self.height // 2, pause_x, pause_msg, curses.color_pair(3))
                except curses.error:
                    pass
        else:
            self.draw_game_over()
        
        if not self.game_over:
            self.draw_instructions()
        
        self.stdscr.refresh()
    
    def run(self):
        """Main game loop"""
        while True:
            if not self.handle_input():
                break
            
            if not self.game_over and not self.paused:
                self.update_ball()
                self.update_ai_paddle()  # Update AI in single player mode
            
            # Always update paddle movement for smooth motion
            if not self.game_over and not self.paused:
                self.update_paddle_movement()
            
            self.draw()


def main(stdscr):
    """Main function to set up and run the game"""
    # Check terminal size
    height, width = stdscr.getmaxyx()
    if height < 20 or width < 60:
        stdscr.clear()
        stdscr.addstr(0, 0, "Terminal too small! Need at least 60x20 characters.")
        stdscr.addstr(1, 0, f"Current size: {width}x{height}")
        stdscr.addstr(2, 0, "Press any key to exit...")
        stdscr.refresh()
        stdscr.getch()
        return
    
    # Create and run the game
    game = PongGame(stdscr)
    game.run()


if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        print("\nGame interrupted by user")
    except Exception as e:
        print(f"An error occurred: {e}")
        print("Make sure your terminal supports color and has adequate size (60x20 minimum)")
