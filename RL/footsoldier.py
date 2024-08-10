import pygame
import time

class Footsoldier:
    def __init__(self, position, team_color=None, sprite_folder="C:\\Users\\Louis\\OneDrive\\The Eggcellent\\Coding Projects\\2024\\Manim\\RL\\knight\\"):
        self.position = pygame.Rect(position[0], position[1], 50, 50)
        self.team_color = team_color

        # Load and crop sprites with fixed dimensions
        self.idle_sprites = self.load_sprites(f'{sprite_folder}Idle.png', frame_width=50, num_frames=4)
        self.run_sprites = self.load_sprites(f'{sprite_folder}Run.png', frame_width=50, num_frames=7)
        self.attack_sprites = self.load_sprites(f'{sprite_folder}Attack 1.png', frame_width=50, num_frames=5)

        # Initialize animation state
        self.current_action = 'idle'
        self.current_frame = 0
        self.animation_speed = 2 
        self.tick_count = 0
        self.last_attack_time = 0 
        self.attack_cooldown = 1.0 
        self.attack_range = 30
        self.health = 100
        self.attack_power = 10
        self.speed = 5
        self.alive = True
        self.gold = 0
        self.exp = 0
        self.level = 1

        # Direction state
        self.direction = 'right'

    def load_sprites(self, filepath, frame_width, num_frames):
        """Load a sprite sheet, resize proportionally, and divide it into individual frames."""
        sprite_sheet = pygame.image.load(filepath).convert_alpha()
        
        # Calculate the width of the entire sprite sheet based on the width of a single frame
        sheet_width = frame_width * num_frames
        
        # Calculate the proportional height based on the aspect ratio of the original sprite sheet
        original_width = sprite_sheet.get_width()
        original_height = sprite_sheet.get_height()
        aspect_ratio = original_height / original_width
        sheet_height = int(sheet_width * aspect_ratio)
        
        # Resize the sprite sheet to the correct width while maintaining the aspect ratio
        resized_sprite_sheet = pygame.transform.scale(sprite_sheet, (sheet_width, sheet_height))
        
        frames = []
        for i in range(num_frames):
            # Crop each frame
            frame = resized_sprite_sheet.subsurface(pygame.Rect(i * frame_width, 0, frame_width, sheet_height))
            frames.append(frame)
        return frames

    def move(self, direction):
        self.current_action = 'run'
        if direction == 'left':
            self.position.x -= self.speed
            self.direction = 'left'
        elif direction == 'right':
            self.position.x += self.speed
            self.direction = 'right'
        elif direction == 'up':
            self.position.y -= self.speed
        elif direction == 'down':
            self.position.y += self.speed

    def attack(self, monsters):
        """Perform an attack, checking if any monster is in range in front of the footsoldier."""
        current_time = time.time()
        if current_time - self.last_attack_time < self.attack_cooldown:
            return

        # Update the last attack time
        self.last_attack_time = current_time

        self.current_action = 'attack'
        self.current_frame = 0 

        if self.direction == 'right':
            attack_rect = pygame.Rect(self.position.right, self.position.y, self.attack_range, self.position.height)
        elif self.direction == 'left':
            attack_rect = pygame.Rect(self.position.left - self.attack_range, self.position.y, self.attack_range, self.position.height)
        elif self.direction == 'up':
            attack_rect = pygame.Rect(self.position.x, self.position.top - self.attack_range, self.position.width, self.attack_range)
        elif self.direction == 'down':
            attack_rect = pygame.Rect(self.position.x, self.position.bottom, self.position.width, self.attack_range)

        for monster in monsters:
            if attack_rect.colliderect(monster.position) and monster.alive:
                monster.take_damage(self.attack_power, self)
                print(f"Monster hit! Monster health: {monster.health}")

    def take_damage(self, amount):
        """Reduces health by a specified amount and checks if the footsoldier is still alive."""
        if self.alive:
            self.health -= amount
            if self.health <= 0:
                self.health = 0  # Ensure health doesn't go negative
                self.alive = False
                self.die()
        print("AOUCH")

    def die(self):
        """Handles the logic for when the footsoldier dies."""
        print("Footsoldier has died.")
        self.current_action = 'idle'  # Could change to a 'dead' state if there's a death animation

    def update_animation(self):
        # Determine which frames to use based on the current action
        if self.current_action == 'run':
            frames = self.run_sprites
        elif self.current_action == 'attack':
            frames = self.attack_sprites
        else:
            frames = self.idle_sprites

        self.tick_count += 1
        if self.tick_count >= self.animation_speed:
            self.tick_count = 0
            self.current_frame += 1
            if self.current_frame >= len(frames):
                if self.current_action == 'attack':  # If attacking, reset to idle after attack
                    self.current_action = 'idle'
                self.current_frame = 0

        # Handle sprite flipping if moving left
        current_frame = frames[self.current_frame]
        if self.direction == 'left':
            current_frame = pygame.transform.flip(current_frame, True, False)
        
        return current_frame

    def draw(self, screen, camera_x, camera_y):
        if self.alive:
            current_sprite = self.update_animation()
            adjusted_position = (self.position.x - camera_x, self.position.y - camera_y)
            screen.blit(current_sprite, adjusted_position)
        else:
            # Display "GAME OVER" if the footsoldier is dead
            font = pygame.font.SysFont(None, 48, bold=True)
            game_over_text = font.render("GAME OVER", True, (255, 0, 0))
            screen.blit(game_over_text, (camera_x + 200, camera_y + 200))

        self.draw_health_bar(screen, camera_x, camera_y)
        self.draw_status_bar(screen)

    def draw_health_bar(self, screen, camera_x, camera_y):
        if self.alive:
            bar_width = 50
            bar_height = 10
            health_bar_width = int(bar_width * (self.health / 100))
            health_bar_position = (self.position.x - camera_x, self.position.y - camera_y - 10)

            # Colors
            background_color = (200, 0, 0)  # Red for background
            health_color = (0, 200, 0)  # Green for current health
            outline_color = (255, 255, 255)  # White outline

            # Draw the background (full bar)
            pygame.draw.rect(screen, background_color, 
                            (health_bar_position[0], health_bar_position[1], bar_width, bar_height))

            # current health bar
            pygame.draw.rect(screen, health_color, 
                            (health_bar_position[0], health_bar_position[1], health_bar_width, bar_height))

            # Health bar outline
            pygame.draw.rect(screen, outline_color, 
                            (health_bar_position[0], health_bar_position[1], bar_width, bar_height), 
                            2)

            font = pygame.font.Font(None, 14)  
            hp_text = f"{self.health} / 100"
            text_surface = font.render(hp_text, True, (255, 255, 255))  
            text_rect = text_surface.get_rect(center=(health_bar_position[0] + bar_width // 2, health_bar_position[1] - 12))
            
            # Draw the text
            screen.blit(text_surface, text_rect)

    def handle_event(self, event):
        """Handles input events, such as attacking on left click."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                mouse_pos = pygame.mouse.get_pos()
                if self.position.collidepoint(mouse_pos):
                    self.attack()


    def draw_status_bar(self, screen):
        """Draw the EXP and GOLD on the top-right corner of the screen surrounded by a white rectangle."""
        font = pygame.font.SysFont(None, 16, bold=True)
        exp_text = f"EXP: {self.exp}"
        gold_text = f"GOLD: {self.gold}"

        exp_surface = font.render(exp_text, True, (0, 0, 0))  
        gold_surface = font.render(gold_text, True, (0, 0, 0))  

        padding = 10
        rect_width = max(exp_surface.get_width(), gold_surface.get_width()) + padding * 2
        rect_height = exp_surface.get_height() + gold_surface.get_height() + padding * 3

        screen_width = screen.get_width()
        rect_x = screen_width - rect_width - 20  
        rect_y = 20  
        pygame.draw.rect(screen, (255, 255, 255), (rect_x, rect_y, rect_width, rect_height))
        pygame.draw.rect(screen, (0, 0, 0), (rect_x, rect_y, rect_width, rect_height), 2)  # Black outline
        screen.blit(exp_surface, (rect_x + padding, rect_y + padding))
        screen.blit(gold_surface, (rect_x + padding, rect_y + exp_surface.get_height() + padding * 2))

