import pygame
from footsoldier import *
from monsters import Monster
import random

pygame.init()

GAME_WIDTH = 1200
GAME_HEIGHT = 800
FPS = 60
BACKGROUND_COLOR = (50, 50, 50)

screen = pygame.display.set_mode((GAME_WIDTH, GAME_HEIGHT))
pygame.display.set_caption("Footsoldier Melee Simulation")

clock = pygame.time.Clock()

# Load the tile image
tile_image = pygame.image.load('RL/tile.png').convert()

# Pre-render the full background on a larger surface
WORLD_WIDTH = 2000
WORLD_HEIGHT = 2000
background_surface = pygame.Surface((WORLD_WIDTH, WORLD_HEIGHT))

def draw_full_background(surface, tile_image):
    tile_width = tile_image.get_width()
    tile_height = tile_image.get_height()
    
    for y in range(0, WORLD_HEIGHT, tile_height):
        for x in range(0, WORLD_WIDTH, tile_width):
            surface.blit(tile_image, (x, y))

# Generate the full background
draw_full_background(background_surface, tile_image)

class KeyboardController:
    def GetAction(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            return 'left'
        elif keys[pygame.K_RIGHT]:
            return 'right'
        elif keys[pygame.K_UP]:
            return 'up'
        elif keys[pygame.K_DOWN]:
            return 'down'
        elif keys[pygame.K_SPACE]:
            return 'attack'
        return 'idle'

player = Footsoldier((100, 100), screen)

controller = KeyboardController()

def center_camera_on_player(player_position):
    camera_x = player_position.x - GAME_WIDTH // 2
    camera_y = player_position.y - GAME_HEIGHT // 2

    # Clamp camera to world bounds
    camera_x = max(0, min(camera_x, WORLD_WIDTH - GAME_WIDTH))
    camera_y = max(0, min(camera_y, WORLD_HEIGHT - GAME_HEIGHT))

    return camera_x, camera_y

random.seed(42) 
monsters = []
for i in range(30):
    x = random.randint(0, 2000) 
    y = random.randint(0, 2000)  
    monster_type = 'strong' if i % 4 == 0 else 'weak' 
    monsters.append(Monster(position=(x, y), monster_type=monster_type))

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                player.attack(monsters=monsters)

    action = controller.GetAction()

    if action == 'attack':
        player.attack()
    elif action != 'idle':
        player.move(action)

    camera_x, camera_y = center_camera_on_player(player.position)

    # Blit the part of the background corresponding to the camera position
    screen.blit(background_surface, (0, 0), (camera_x, camera_y, GAME_WIDTH, GAME_HEIGHT))

    player.draw(camera_x, camera_y)

    for monster in monsters:
        if monster.alive:
            monster.handle_event(event, player)
            monster.draw(screen, camera_x, camera_y)

    pygame.display.flip()

    clock.tick(FPS)

pygame.quit()
