import pygame
from footsoldier import Footsoldier
import time

class Monster:
    def __init__(self, position, monster_type='weak', size=50):
        self.position = pygame.Rect(position[0], position[1], size, size)
        self.monster_type = monster_type
        
        # Set attributes based on the type of monster
        if monster_type == 'strong':
            self.health = 200
            self.max_health = 200
            self.attack_power = 20
            self.attack_range = 100  # Attack range for strong monsters
            self.speed = 2
            self.EXP = 10
            self.gold = 10
            self.detection_range = 150
            self.color = (255, 0, 0)  # Red for strong monster

        else:  # 'weak' monster
            self.health = 50
            self.max_health = 50
            self.attack_power = 5
            self.attack_range = 80  # Attack range for weak monsters
            self.speed = 1
            self.EXP = 10
            self.gold = 25
            self.detection_range = 100
            self.color = (0, 255, 0)  # Green for weak monster

        self.alive = True
        self.direction = 'right'
        self.last_attack_time = 0  # Track the time of the last attack

    def move_towards(self, target_position):
        """Move the monster towards the player's character."""
        self.current_action = 'run'
        if self.position.x < target_position[0]:
            self.position.x += self.speed
            self.direction = 'right'
        elif self.position.x > target_position[0]:
            self.position.x -= self.speed
            self.direction = 'left'
        if self.position.y < target_position[1]:
            self.position.y += self.speed
        elif self.position.y > target_position[1]:
            self.position.y -= self.speed

    def attack(self, player):
        """Perform an attack on the player if within a 10-pixel range and after a delay."""
        current_time = time.time()
        
        # If more than 1 second has passed since the last attack, perform the attack
        if current_time - self.last_attack_time >= 1:
            # Calculate the attack range based on the direction and include a 10-pixel range
            if self.direction == 'right':
                attack_range = pygame.Rect(self.position.right, self.position.centery - 10, 10, 20)
            elif self.direction == 'left':
                attack_range = pygame.Rect(self.position.left - 10, self.position.centery - 10, 10, 20)
            elif self.direction == 'up':
                attack_range = pygame.Rect(self.position.centerx - 10, self.position.top - 10, 20, 10)
            elif self.direction == 'down':
                attack_range = pygame.Rect(self.position.centerx - 10, self.position.bottom, 20, 10)

            # Check if the player's position intersects with the attack range
            if attack_range.colliderect(player.rect):
                player.take_damage(self.attack_power)
                print(f"Player hit by monster! Player health: {player.health}")
            # Set the last attack time to now
            self.last_attack_time = current_time

    def die(self, player):
        """Handles the logic for when the monster dies and rewards the player."""
        print(f"{self.monster_type.capitalize()} monster has died. Gained {self.EXP} EXP and {self.gold} Gold.")
        player.gold += self.gold
        player.exp += self.EXP
        self.current_action = 'idle'  

    def take_damage(self, amount, player):
        """Reduces health by a specified amount and checks if the monster is still alive."""
        if self.alive:
            self.health -= amount
            if self.health <= 0:
                self.alive = False
                self.health = 0
                self.die(player)  

    def draw(self, screen, camera_x, camera_y):
        """Draw the monster as a simple cube and its detection range on the screen."""
        if self.alive:
            adjusted_position = (self.position.x - camera_x, self.position.y - camera_y)
            
            # Draw the monster as a cube
            pygame.draw.rect(screen, self.color, pygame.Rect(adjusted_position[0], adjusted_position[1], self.position.width, self.position.height))
            
            # Draw health bar above the monster
            self.draw_health_bar(screen, camera_x, camera_y)
            
            # Draw the detection range as a red circle
            self.draw_detection_range(screen, camera_x, camera_y)

    def draw_health_bar(self, screen, camera_x, camera_y):
        """Draw the health bar above the monster, showing the percentage of health left."""
        if self.alive:
            bar_width = self.position.width
            bar_height = 7
            health_percentage = self.health / self.max_health
            health_bar_width = int(bar_width * health_percentage)

            # Adjust the position of the health bar based on the camera offset
            health_bar_position = (self.position.x - camera_x, self.position.y - camera_y - 15)

            # Colors
            background_color = (255, 0, 0)  # Red for the missing health portion
            health_color = (173, 216, 230)  # Light blue for the current health
            outline_color = (0, 0, 0)  # Black outline

            # Draw background (full health bar)
            pygame.draw.rect(screen, background_color, (health_bar_position[0], health_bar_position[1], bar_width, bar_height))

            # Draw current health bar
            pygame.draw.rect(screen, health_color, (health_bar_position[0], health_bar_position[1], health_bar_width, bar_height))

            # Draw outline around the health bar
            pygame.draw.rect(screen, outline_color, (health_bar_position[0], health_bar_position[1], bar_width, bar_height), 2)

            # Draw the health percentage text
            font = pygame.font.SysFont(None, 14, bold=True)
            hp_text = font.render(f'{int(health_percentage * 100)}%', True, (255, 255, 255))
            hp_text_position = (health_bar_position[0] + (bar_width // 2) - (hp_text.get_width() // 2), health_bar_position[1] - 15)
            screen.blit(hp_text, hp_text_position)

    def draw_detection_range(self, screen, camera_x, camera_y):
        """Draw the detection range as a red circle."""
        if self.alive:
            center_position = (self.position.centerx - camera_x, self.position.centery - camera_y)
            pygame.draw.circle(screen, (255, 0, 0), center_position, self.detection_range, 2)

    def handle_event(self, event, player):
        """Check if the player is within detection range and handle attacking."""
        if self.alive:
            # Ensure we're accessing the player's position correctly
            player_center = player.position.center
            monster_center = self.position.center
            distance_to_player = pygame.math.Vector2(monster_center).distance_to(player_center)

            if distance_to_player <= self.detection_range:
                self.move_towards(player_center)
                if distance_to_player <= self.attack_range:  # Attack if close enough
                    self.attack(player)