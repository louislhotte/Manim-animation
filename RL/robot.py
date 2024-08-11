import random
import copy
import pygame
from footsoldier import Footsoldier
from monsters import Monster
import time
import cv2 
import multiprocessing

# Screen and world dimensions
WORLD_WIDTH = 1200
WORLD_HEIGHT = 800
SIMULATION_TIME = 60 
GAME_WIDTH = 1200
GAME_HEIGHT = 800
screen = pygame.display.set_mode((GAME_WIDTH, GAME_HEIGHT))
tile_image = pygame.image.load('RL/tile.png').convert()

# Constants for genetic algorithm
POPULATION_SIZE = 20
GENOME_LENGTH = 10000  # Number of actions in a sequence
MUTATION_RATE = 0.1
NUM_GENERATIONS = 50

# Possible actions for the bot
ACTIONS = ['left', 'right', 'up', 'down', 'attack']
# Pre-render the full background on a larger surface
background_surface = pygame.Surface((WORLD_WIDTH, WORLD_HEIGHT))

def draw_full_background(surface, tile_image, WORLD_HEIGHT=WORLD_HEIGHT, WORLD_WIDTH=WORLD_WIDTH):
    tile_width = tile_image.get_width()
    tile_height = tile_image.get_height()
    
    for y in range(0, WORLD_HEIGHT, tile_height):
        for x in range(0, WORLD_WIDTH, tile_width):
            surface.blit(tile_image, (x, y))

def center_camera_on_player(player_position):
    camera_x = player_position[0] - GAME_WIDTH // 2
    camera_y = player_position[1] - GAME_HEIGHT // 2

    # Clamp camera to world bounds
    camera_x = max(0, min(camera_x, WORLD_WIDTH - GAME_WIDTH))
    camera_y = max(0, min(camera_y, WORLD_HEIGHT - GAME_HEIGHT))

    return camera_x, camera_y

class Robot:
    def __init__(self, robot_id):
        self.robot_id = robot_id
        self.genome = [random.choice(ACTIONS) for _ in range(GENOME_LENGTH)]
        self.fitness = 0
        self.player = Footsoldier((100, 100), screen)  
        self.monsters = self.spawn_monsters(seed=34)  
        self.generation = 1

    def evaluate_fitness(self, seed):
        random.seed(seed)
        start_time = time.time()
        
        for action in self.genome:
            if time.time() - start_time > SIMULATION_TIME:
                break

            if not self.player.alive:
                break

            if action == 'attack':
                hit = self.player.attack(monsters=self.monsters)
                if hit:
                    self.fitness += 1
            else:
                self.player.move(action)

        # Add any leftover gold as fitness
        self.fitness += self.player.gold

    def simulate_frame(self, screen):
        if self.player is None:
            raise ValueError(f"Player not initialized for robot {self.robot_id}")
        
        camera_x, camera_y = center_camera_on_player(self.player.position)
        screen.blit(background_surface, (0, 0), (camera_x, camera_y, GAME_WIDTH, GAME_HEIGHT))
        self.player.draw(camera_x, camera_y)

        if self.player.alive:
            for monster in self.monsters:
                if monster.alive:
                    monster.handle_event(None, self.player)
                    monster.draw(screen, camera_x, camera_y)

        self.display_info(screen, self.generation)

    def display_info(self, screen, generation):
        font = pygame.font.Font(None, 36)
        text = font.render(f"Robot ID: {self.robot_id}  Generation: {generation + 1}", True, (255, 255, 255))
        screen.blit(text, (10, 10))

    def spawn_monsters(self, seed):
        # Generate monsters with a consistent random seed
        random.seed(seed)
        return [Monster(position=(random.randint(0, WORLD_WIDTH), random.randint(0, WORLD_HEIGHT)),
                        monster_type='strong' if i % 5 == 0 else 'weak') for i in range(15)]