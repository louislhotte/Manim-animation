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
        self.animation_speed = 15  # Number of ticks before the next frame
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

    def attack(self):
        self.current_action = 'attack'
        self.current_frame = 0 

    def take_damage(self, amount):
        """Reduces health by a specified amount and checks if the footsoldier is still alive."""
        if self.alive:
            self.health -= amount
            if self.health <= 0:
                self.alive = False
                self.health = 0
                self.die()

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
            adjusted_position = (self.position[0] - camera_x, self.position[1] - camera_y)
            screen.blit(current_sprite, adjusted_position)
            self.draw_health_bar(screen, camera_x, camera_y)


    def draw_health_bar(self, screen, camera_x, camera_y):
        if self.alive:
            bar_width = 50
            bar_height = 7
            health_bar_width = int(bar_width * (self.health / 100))
            
            # Adjust the position of the health bar based on the camera offset
            health_bar_position = (self.position.x - camera_x, self.position.y - camera_y - 10)

            # Colors
            background_color = (255, 0, 0)  # Red background for missing health
            health_color = (0, 255, 0)  # Green for current health
            outline_color = (0, 0, 0)  # Black outline
            shadow_color = (50, 50, 50)  # Shadow color
            hp_text_color = (255, 0, 0)  # Red color for the HP text

            # Draw shadow
            shadow_offset = 2
            pygame.draw.rect(screen, shadow_color, (health_bar_position[0] + shadow_offset, health_bar_position[1] + shadow_offset, bar_width, bar_height), border_radius=3)

            # Draw background with rounded corners
            pygame.draw.rect(screen, background_color, (health_bar_position[0], health_bar_position[1], bar_width, bar_height), border_radius=3)

            # Draw health bar with rounded corners and gradient effect
            for i in range(health_bar_width):
                gradient_color = (
                    int(health_color[0] * (i / health_bar_width)),
                    int(health_color[1] * (i / health_bar_width)),
                    int(health_color[2] * (i / health_bar_width))
                )
                pygame.draw.line(screen, gradient_color, (health_bar_position[0] + i, health_bar_position[1]), (health_bar_position[0] + i, health_bar_position[1] + bar_height))

            # Draw outline around the health bar
            pygame.draw.rect(screen, outline_color, (health_bar_position[0], health_bar_position[1], bar_width, bar_height), 2, border_radius=3)

            # Draw current HP value above the health bar
            font = pygame.font.SysFont(None, 14, bold=True)
            hp_text = font.render(f'{self.health} HP', True, hp_text_color)
            hp_text_position = (health_bar_position[0] + (bar_width // 2) - (hp_text.get_width() // 2), health_bar_position[1] - 15)
            screen.blit(hp_text, hp_text_position)

    def handle_event(self, event):
        """Handles input events, such as attacking on left click."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                mouse_pos = pygame.mouse.get_pos()
                if self.position.collidepoint(mouse_pos):
                    self.attack()

