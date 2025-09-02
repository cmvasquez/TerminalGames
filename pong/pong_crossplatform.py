#!/usr/bin/env python3
"""
Cross-Platform Terminal Pong Game
A Pong game that works on all platforms without requiring curses.

Controls:
- Single Player: W/S keys to move paddle up/down
- Two Player: Player 1 (W/S), Player 2 (A/D or J/K)
- M to switch between single/two player modes
- Q to quit the game
- Enter to confirm input

This version uses standard input/output and works on Windows, Mac, and Linux.
"""

import sys
import time
import random
import math
import threading
import os
from queue import Queue, Empty

# Try to import keyboard for better input handling
try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False

# Try to import colorama for colored output on Windows
try:
    import colorama
    colorama.init()
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False

class CrossPlatformPong:
    def __init__(self):
        # Terminal setup
        self.width = 80
        self.height = 24
        
        # Game settings
        self.target_score = 10
        self.ball_speed = 0.15
        self.single_player = True
        
        # AI settings
        self.ai_speed = 0.7
        self.ai_prediction = 0.3
        
        # Game state
        self.running = True
        self.paused = False
        self.game_over = False
        self.winner = None
        
        # Input handling
        self.input_queue = Queue()
        self.keys_pressed = set()
        
        # Initialize game objects
        self.reset_game()
        
        # Start input thread if keyboard is available
        if KEYBOARD_AVAILABLE:
            self.start_keyboard_input()
        else:
            print("Note: Install 'keyboard' package for better controls (pip install keyboard)")
            print("Using basic input mode - press Enter after each command")
    
    def start_keyboard_input(self):
        """Start keyboard input handling in a separate thread"""
        def input_handler():
            keyboard.on_press_key('w', lambda _: self.add_key('w'))
            keyboard.on_press_key('s', lambda _: self.add_key('s'))
            keyboard.on_press_key('up', lambda _: self.add_key('up'))
            keyboard.on_press_key('down', lambda _: self.add_key('down'))
            keyboard.on_press_key('a', lambda _: self.add_key('a'))
            keyboard.on_press_key('d', lambda _: self.add_key('d'))
            keyboard.on_press_key('j', lambda _: self.add_key('j'))
            keyboard.on_press_key('k', lambda _: self.add_key('k'))
            keyboard.on_press_key('m', lambda _: self.add_key('m'))
            keyboard.on_press_key('q', lambda _: self.add_key('q'))
            keyboard.on_press_key('space', lambda _: self.add_key('space'))
            keyboard.on_press_key('r', lambda _: self.add_key('r'))
            
            # Keep the thread alive
            while self.running:
                time.sleep(0.1)
        
        if KEYBOARD_AVAILABLE:
            input_thread = threading.Thread(target=input_handler, daemon=True)
            input_thread.start()
    
    def add_key(self, key):
        """Add a key press to the input queue"""
        self.input_queue.put(key)
    
    def reset_game(self):
        """Reset the game to initial state"""
        # Paddle settings
        self.paddle_height = 5
        
        # Player 1 (left paddle)
        self.p1_y = self.height // 2 - self.paddle_height // 2
        self.p1_x = 2
        self.p1_score = 0
        
        # Player 2 (right paddle)
        self.p2_y = self.height // 2 - self.paddle_height // 2
        self.p2_x = self.width - 3
        self.p2_score = 0
        
        # Ball settings
        self.reset_ball()
        
        # Game state
        self.game_over = False
        self.winner = None
    
    def reset_ball(self):
        """Reset ball position and velocity"""
        self.ball_x = float(self.width // 2)
        self.ball_y = float(self.height // 2)
        
        # Random starting direction
        angle = random.uniform(-math.pi/4, math.pi/4)
        if random.choice([True, False]):
            angle += math.pi
        
        speed = 1.0
        self.ball_dx = speed * math.cos(angle)
        self.ball_dy = speed * math.sin(angle)
    
    def move_paddle(self, player, direction):
        """Move paddle up or down"""
        if player == 1:
            new_y = self.p1_y + direction
            if 1 <= new_y <= self.height - self.paddle_height - 2:
                self.p1_y = new_y
        elif player == 2:
            new_y = self.p2_y + direction
            if 1 <= new_y <= self.height - self.paddle_height - 2:
                self.p2_y = new_y
    
    def update_ai_paddle(self):
        """Update AI paddle position"""
        if not self.single_player or self.paused or self.game_over:
            return
        
        # Predict ball position
        if self.ball_dx > 0:  # Ball moving towards AI
            time_to_paddle = (self.p2_x - self.ball_x) / abs(self.ball_dx)
            predicted_y = self.ball_y + (self.ball_dy * time_to_paddle * self.ai_prediction)
            
            if random.random() < 0.1:
                predicted_y += random.uniform(-2, 2)
        else:
            predicted_y = self.height // 2
        
        # Move AI paddle
        paddle_center = self.p2_y + self.paddle_height // 2
        if abs(predicted_y - paddle_center) > 0.5:
            direction = 1 if predicted_y > paddle_center else -1
            if random.random() < self.ai_speed:
                self.move_paddle(2, direction)
    
    def update_ball(self):
        """Update ball position and handle collisions"""
        # Update position
        self.ball_x += self.ball_dx
        self.ball_y += self.ball_dy
        
        # Wall collisions
        if self.ball_y <= 1 or self.ball_y >= self.height - 2:
            self.ball_dy = -self.ball_dy
            self.ball_y = max(2, min(self.ball_y, self.height - 3))
        
        # Paddle collisions
        ball_int_x = int(round(self.ball_x))
        ball_int_y = int(round(self.ball_y))
        
        # Left paddle
        if (ball_int_x <= self.p1_x + 1 and 
            self.p1_y <= ball_int_y <= self.p1_y + self.paddle_height - 1 and
            self.ball_dx < 0):
            self.ball_dx = abs(self.ball_dx)
            hit_pos = (ball_int_y - self.p1_y) / (self.paddle_height - 1)
            self.ball_dy += (hit_pos - 0.5) * 0.5
            
        # Right paddle
        elif (ball_int_x >= self.p2_x - 1 and 
              self.p2_y <= ball_int_y <= self.p2_y + self.paddle_height - 1 and
              self.ball_dx > 0):
            self.ball_dx = -abs(self.ball_dx)
            hit_pos = (ball_int_y - self.p2_y) / (self.paddle_height - 1)
            self.ball_dy += (hit_pos - 0.5) * 0.5
        
        # Scoring
        if self.ball_x < 0:
            self.p2_score += 1
            if self.p2_score >= self.target_score:
                self.game_over = True
                self.winner = "Computer" if self.single_player else "Player 2"
            else:
                self.reset_ball()
        elif self.ball_x > self.width:
            self.p1_score += 1
            if self.p1_score >= self.target_score:
                self.game_over = True
                self.winner = "You" if self.single_player else "Player 1"
            else:
                self.reset_ball()
    
    def handle_input(self):
        """Handle user input"""
        if KEYBOARD_AVAILABLE:
            # Handle keyboard input from queue
            while not self.input_queue.empty():
                try:
                    key = self.input_queue.get_nowait()
                    
                    if key == 'q':
                        return False
                    elif key == 'm':
                        self.single_player = not self.single_player
                        if not self.game_over:
                            self.reset_game()
                    elif key == 'r' and self.game_over:
                        self.reset_game()
                    elif key == 'space':
                        self.paused = not self.paused
                    elif not self.game_over:
                        # Player 1 controls
                        if key == 'w':
                            self.move_paddle(1, -1)
                        elif key == 's':
                            self.move_paddle(1, 1)
                        # Player 2 controls (only in two player mode)
                        elif not self.single_player:
                            if key in ['up', 'k']:
                                self.move_paddle(2, -1)
                            elif key in ['down', 'j']:
                                self.move_paddle(2, 1)
                except Empty:
                    break
        else:
            # Basic input mode - show prompt
            if not hasattr(self, '_input_shown'):
                print("\nControls: W/S (P1), Up/Down or J/K (P2), M (mode), Q (quit), R (restart)")
                print("Enter command and press Enter:")
                self._input_shown = True
        
        return True
    
    def clear_screen(self):
        """Clear the terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def draw_game(self):
        """Draw the entire game"""
        # Create game field
        field = [[' ' for _ in range(self.width)] for _ in range(self.height)]
        
        # Draw borders
        for x in range(self.width):
            field[0][x] = '─'
            field[self.height-1][x] = '─'
        
        # Draw center line
        center_x = self.width // 2
        for y in range(1, self.height-1, 2):
            field[y][center_x] = '│'
        
        # Draw paddles
        for i in range(self.paddle_height):
            if 0 <= self.p1_y + i < self.height:
                field[self.p1_y + i][self.p1_x] = '█'
            if 0 <= self.p2_y + i < self.height:
                field[self.p2_y + i][self.p2_x] = '█'
        
        # Draw ball
        if not self.paused:
            ball_x = int(round(self.ball_x))
            ball_y = int(round(self.ball_y))
            if 0 <= ball_x < self.width and 0 <= ball_y < self.height:
                field[ball_y][ball_x] = '●'
        
        # Convert to string and display
        self.clear_screen()
        
        # Game info
        mode = "Single Player" if self.single_player else "Two Player"
        print(f"PONG - {mode} Mode")
        print(f"Score: {self.p1_score} - {self.p2_score}")
        print()
        
        # Draw field
        for row in field:
            print(''.join(row))
        
        # Game status
        if self.game_over:
            print(f"\nGAME OVER! {self.winner} Wins!")
            print("Press R to restart, M to change mode, Q to quit")
        elif self.paused:
            print("\nPAUSED - Press SPACE to continue")
        else:
            if self.single_player:
                print("\nControls: W/S to move paddle")
            else:
                print("\nControls: P1(W/S), P2(↑/↓ or J/K)")
            print("M: Change Mode | SPACE: Pause | Q: Quit")
        
        if not KEYBOARD_AVAILABLE:
            print("\nFor better experience: pip install keyboard")
    
    def run(self):
        """Main game loop"""
        print("Starting Cross-Platform Pong...")
        print("Terminal size:", self.width, "x", self.height)
        time.sleep(1)
        
        while self.running:
            if not self.handle_input():
                break
            
            if not self.game_over and not self.paused:
                self.update_ball()
                self.update_ai_paddle()
            
            self.draw_game()
            time.sleep(self.ball_speed)
        
        print("\nThanks for playing!")

def main():
    """Main function"""
    try:
        game = CrossPlatformPong()
        game.run()
    except KeyboardInterrupt:
        print("\nGame interrupted by user")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
