import pygame
from footsoldier import *
from monsters import Monster
import random
import time
import copy
import cv2
import numpy as np

pygame.init()

GAME_WIDTH = 1200
GAME_HEIGHT = 800
FPS = 20
BACKGROUND_COLOR = (50, 50, 50)
SIMULATION_TIME = 60
POPULATION_SIZE = 10
NUM_GENERATIONS = 50
GENERATIONS_TO_CAPTURE = [1, 3, 5, 10, 20, 50]  # Specific generations to capture video

screen = pygame.display.set_mode((GAME_WIDTH, GAME_HEIGHT))
pygame.display.set_caption("Footsoldier Melee Simulation")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)  # Font for displaying text

# Load the tile image
tile_image = pygame.image.load('RL/tile.png').convert()

# Pre-render the full background on a larger surface
WORLD_WIDTH = 1200
WORLD_HEIGHT = 800
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
        self.monsters = self.spawn_monsters(seed=34)  # Each robot has its own monster set

    def spawn_monsters(self, seed):
        random.seed(seed)
        return [Monster(position=(random.randint(0, WORLD_WIDTH), random.randint(0, WORLD_HEIGHT)),
                        monster_type='strong' if i % 5 == 0 else 'weak') for i in range(20)]

    def evaluate_fitness(self):
        # Fitness is based on the amount of gold collected and monsters defeated
        self.fitness += self.player.gold
        for monster in self.monsters:
            if not monster.alive:
                self.fitness += 10  # Example reward for defeating a monster

    def simulate(self, capture_video=False, out=None, generation=None):
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

            # Draw monsters
            for monster in self.monsters:
                if monster.alive:
                    monster.handle_event(None, self.player)
                    monster.draw(screen, camera_x, camera_y)

            # Display generation and robot ID
            text_surface = font.render(f"Generation: {generation + 1}  Robot ID: {self.robot_id}", True, (255, 255, 255))
            screen.blit(text_surface, (10, 10))

            pygame.display.flip()

            if capture_video:
                # Capture the frame
                frame = pygame.surfarray.array3d(screen)
                frame = np.rot90(frame)
                frame = np.flipud(frame)
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                out.write(frame)

            clock.tick(FPS)

        self.evaluate_fitness()

    def copy_without_surface(self):
        """Returns a deepcopy of the robot without copying the pygame.Surface objects."""
        new_robot = Robot(self.robot_id)
        new_robot.genome = copy.deepcopy(self.genome)
        new_robot.fitness = self.fitness
        # Reinitialize player and monsters without copying surfaces
        new_robot.player = Footsoldier(self.player.position, screen)
        new_robot.player.gold = self.player.gold
        new_robot.player.alive = self.player.alive

        new_robot.monsters = []
        for monster in self.monsters:
            new_monster = Monster(monster.position, monster.monster_type)
            new_monster.alive = monster.alive
            new_robot.monsters.append(new_monster)
        return new_robot

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
                robot.simulate(capture_video=True, out=out, generation=generation)
            else:
                robot.simulate(generation=generation)
            print(f"Robot {robot.robot_id} Fitness: {robot.fitness}")

        population.sort(key=lambda r: r.fitness, reverse=True)
        best_fitness = population[0].fitness
        print(f"Best fitness in generation {generation + 1}: {best_fitness}")
        next_generation = []
        next_generation.extend(robot.copy_without_surface() for robot in population[:POPULATION_SIZE // 5])

        # Breed new individuals from the top performers
        while len(next_generation) < POPULATION_SIZE:
            parent1, parent2 = random.sample(next_generation[:POPULATION_SIZE // 5], 2)
            child_genome = crossover(parent1.genome, parent2.genome)
            child_genome = mutate(child_genome)
            new_robot = Robot(robot_id=len(next_generation))
            new_robot.genome = child_genome
            next_generation.append(new_robot)

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
