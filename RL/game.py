import pygame
from footsoldier import *

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

class AIController:
    def __init__(self):
        pass

    def GetAction(self, state):
        return 'left'

player = Footsoldier(position=(100, 100))

controller = KeyboardController()

def center_camera_on_player(player_position):
    camera_x = player_position[0] - GAME_WIDTH // 2
    camera_y = player_position[1] - GAME_HEIGHT // 2
    return camera_x, camera_y

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                player.attack()

    action = controller.GetAction()

    if action == 'attack':
        player.attack()
    elif action != 'idle':
        player.move(action)

    camera_x, camera_y = center_camera_on_player(player.position)

    screen.fill(BACKGROUND_COLOR)

    player.draw(screen, camera_x, camera_y)

    pygame.display.flip()

    clock.tick(FPS)

pygame.quit()
