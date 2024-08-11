import pygame
from footsoldier import *
from monsters import Monster
import random
import time
import copy
import cv2
import numpy as np

pygame.init()

WORLD_WIDTH = 1200
WORLD_HEIGHT = 800
GAME_WIDTH = 1200
GAME_HEIGHT = 800
FPS = 20
BACKGROUND_COLOR = (50, 50, 50)
SIMULATION_TIME = 30
POPULATION_SIZE = 20
NUM_GENERATIONS = 50
GENERATIONS_TO_CAPTURE = [1, 3, 5, 10, 20, 50]  # Specific generations to capture video

screen = pygame.display.set_mode((GAME_WIDTH, GAME_HEIGHT))
pygame.display.set_caption("Footsoldier Melee Simulation")
clock = pygame.time.Clock()
# Load the tile image
tile_image = pygame.image.load('RL/tile.png').convert()


background_surface = pygame.Surface((WORLD_WIDTH, WORLD_HEIGHT))

def draw_full_background(surface, tile_image):
    tile_width = tile_image.get_width()
    tile_height = tile_image.get_height()
    
    for y in range(0, WORLD_HEIGHT, tile_height):
        for x in range(0, WORLD_WIDTH, tile_width):
            surface.blit(tile_image, (x, y))

# Generate the full background
draw_full_background(background_surface, tile_image)

class Robot:
    def __init__(self, robot_id):
        self.robot_id = robot_id
        self.genome = [random.choice(['left', 'right', 'up', 'down', 'attack']) for _ in range(1000)]  # Placeholder genome
        self.fitness = 0
        self.player = Footsoldier((100, 100), screen)  
        self.monsters = self.spawn_monsters(seed=robot_id)  # Each robot has its own monster set

    def spawn_monsters(self, seed):
        random.seed(seed)
        return [Monster(position=(random.randint(0, WORLD_WIDTH), random.randint(0, WORLD_HEIGHT)),
                        monster_type='strong' if i % 5 == 0 else 'weak') for i in range(30)]

    def evaluate_fitness(self):
        # Fitness is based on the amount of gold collected and monsters defeated
        self.fitness += self.player.gold
        for monster in self.monsters:
            if not monster.alive:
                self.fitness += 10  # Example reward for defeating a monster

    def simulate(self, capture_video=False, out=None):
        start_time = time.time()
        running = True

        for action in self.genome:
            if time.time() - start_time > SIMULATION_TIME or not self.player.alive:
                break

            if action == 'attack':
                self.player.attack(monsters=self.monsters)
            else:
                self.player.move(action)

            camera_x, camera_y = center_camera_on_player(self.player.position)

            screen.blit(background_surface, (0, 0), (camera_x, camera_y, GAME_WIDTH, GAME_HEIGHT))
            self.player.draw(camera_x, camera_y)

            for monster in self.monsters:
                if monster.alive:
                    monster.handle_event(None, self.player)
                    monster.draw(screen, camera_x, camera_y)

            pygame.display.flip()

            if capture_video:
                frame = pygame.surfarray.array3d(screen)
                frame = np.rot90(frame)
                frame = np.flipud(frame)
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                out.write(frame)

            clock.tick(FPS)

        self.evaluate_fitness()

def center_camera_on_player(player_position):
    camera_x = player_position.x - GAME_WIDTH // 2
    camera_y = player_position.y - GAME_HEIGHT // 2

    # Clamp camera to world bounds
    camera_x = max(0, min(camera_x, WORLD_WIDTH - GAME_WIDTH))
    camera_y = max(0, min(camera_y, WORLD_HEIGHT - GAME_HEIGHT))

    return camera_x, camera_y

def genetic_algorithm():
    # Set up video capture for all selected generations
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter('robot_animation.avi', fourcc, FPS, (GAME_WIDTH, GAME_HEIGHT))

    # Initialize population
    population = [Robot(robot_id=i) for i in range(POPULATION_SIZE)]

    for generation in range(NUM_GENERATIONS):
        print(f"Generation {generation + 1}")
        capture_video = (generation + 1) in GENERATIONS_TO_CAPTURE
        if capture_video:
            random_robot = random.choice(population)  # Select a random robot to capture its run

        for robot in population:
            if capture_video and robot == random_robot:
                robot.simulate(capture_video=True, out=out)
            else:
                robot.simulate()
            print(f"Robot {robot.robot_id} Fitness: {robot.fitness}")

        population.sort(key=lambda r: r.fitness, reverse=True)
        best_fitness = population[0].fitness
        print(f"Best fitness in generation {generation + 1}: {best_fitness}")
        next_generation = []
        next_generation.extend(copy.deepcopy(population[:POPULATION_SIZE // 5]))

        # Breed new individuals from the top performers
        while len(next_generation) < POPULATION_SIZE:
            parent1, parent2 = random.sample(population[:POPULATION_SIZE // 5], 2)
            child_genome = crossover(parent1.genome, parent2.genome)
            child_genome = mutate(child_genome)
            next_generation.append(Robot(robot_id=len(next_generation)))
            next_generation[-1].genome = child_genome

        # Replace old population with the new one
        population = next_generation

    # Release the video writer object after all generations are done
    out.release()

def crossover(genome1, genome2):
    crossover_point = random.randint(0, len(genome1) - 1)
    return genome1[:crossover_point] + genome2[crossover_point:]

def mutate(genome):
    MUTATION_RATE = 0.1
    for i in range(len(genome)):
        if random.random() < MUTATION_RATE:
            genome[i] = random.choice(['left', 'right', 'up', 'down', 'attack'])
    return genome

if __name__ == '__main__':
    genetic_algorithm()
    pygame.quit()
    cv2.destroyAllWindows()
