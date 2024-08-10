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

player = Footsoldier(position=(100, 100))

controller = KeyboardController()

def center_camera_on_player(player_position):
    camera_x = player_position.x - GAME_WIDTH // 2
    camera_y = player_position.y - GAME_HEIGHT // 2
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

    screen.fill(BACKGROUND_COLOR)

    player.draw(screen, camera_x, camera_y)

    for monster in monsters:
        if monster.alive:
            monster.handle_event(event, player)
            monster.draw(screen, camera_x, camera_y)

    pygame.display.flip()

    clock.tick(FPS)

pygame.quit()
