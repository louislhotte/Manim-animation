import pygame

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
        self.animation_speed = 20  # Number of ticks before the next frame
        self.tick_count = 0

        self.health = 100
        self.attack_power = 10
        self.speed = 5
        self.alive = True

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
        self.current_action = 'attack'
        self.current_frame = 0 

        # Define the attack range based on the footsoldier's direction
        attack_range = 30  # Example attack range distance in pixels

        if self.direction == 'right':
            attack_rect = pygame.Rect(self.position.right, self.position.y, attack_range, self.position.height)
        elif self.direction == 'left':
            attack_rect = pygame.Rect(self.position.left - attack_range, self.position.y, attack_range, self.position.height)
        elif self.direction == 'up':
            attack_rect = pygame.Rect(self.position.x, self.position.top - attack_range, self.position.width, attack_range)
        elif self.direction == 'down':
            attack_rect = pygame.Rect(self.position.x, self.position.bottom, self.position.width, attack_range)

        # Check for collisions with monsters within the attack range
        for monster in monsters:
            if attack_rect.colliderect(monster.position) and monster.alive:
                monster.take_damage(self.attack_power)
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
            screen.blit(game_over_text, (camera_x + 200, camera_y + 200))  # Adjust position as needed

        self.draw_health_bar(screen, camera_x, camera_y)

    def draw_health_bar(self, screen, camera_x, camera_y):
        if self.alive:
            bar_width = 50
            bar_height = 10
            health_bar_width = int(bar_width * (self.health / 100))

            # Adjust the position of the health bar based on the camera offset
            health_bar_position = (self.position.x - camera_x, self.position.y - camera_y - 10)

            # Colors
            background_color = (200, 0, 0)  # Red for background
            health_color = (0, 200, 0)  # Green for current health
            outline_color = (255, 255, 255)  # White outline

            # Draw the background (full bar)
            pygame.draw.rect(screen, background_color, 
                            (health_bar_position[0], health_bar_position[1], bar_width, bar_height))

            # Draw the health bar (current health)
            pygame.draw.rect(screen, health_color, 
                            (health_bar_position[0], health_bar_position[1], health_bar_width, bar_height))

            # Draw outline around the health bar
            pygame.draw.rect(screen, outline_color, 
                            (health_bar_position[0], health_bar_position[1], bar_width, bar_height), 
                            2)

            # Display the current HP over total HP
            font = pygame.font.Font(None, 14)  # Slightly smaller font for simplicity
            hp_text = f"{self.health} / 100"
            text_surface = font.render(hp_text, True, (255, 255, 255))  # White text for clarity
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
