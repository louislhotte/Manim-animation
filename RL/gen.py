import random
import copy
import pygame
from footsoldier import Footsoldier
from monsters import Monster
import time
import cv2 
import multiprocessing
from robot import Robot, draw_full_background

pygame.init()

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
# Generate the full background
draw_full_background(background_surface, tile_image, WORLD_HEIGHT, WORLD_WIDTH)

def mutate(genome):
    new_genome = copy.deepcopy(genome)
    for i in range(len(new_genome)):
        if random.random() < MUTATION_RATE:
            new_genome[i] = random.choice(ACTIONS)
    return new_genome

def crossover(parent1, parent2):
    crossover_point = random.randint(0, GENOME_LENGTH - 1)
    return parent1[:crossover_point] + parent2[crossover_point:]

def evaluate_robot_parallel(robot_genome, seed, generation):
    random.seed(seed)
    robot = Robot(robot_id=0)
    robot.genome = robot_genome
    robot.evaluate_fitness(screen, seed) 
    return robot.fitness

def run_evolution_parallel_display(screen):
    initial_seed = 34  
    global generation
    population = [Robot(robot_id=i) for i in range(POPULATION_SIZE)]
    video_filename = "robot_simulation_parallel.mp4"
    fps = 20
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video_out = cv2.VideoWriter(video_filename, fourcc, fps, (GAME_WIDTH, GAME_HEIGHT))

    for generation in range(NUM_GENERATIONS):
        for i, robot in enumerate(population):
            robot.generation = generation

        print(f"Generation {generation + 1}")
        with multiprocessing.Pool() as pool:
            fitness_results = pool.starmap(
                evaluate_robot_parallel,
                [(robot.genome, initial_seed, generation) for robot in population]
            )

        for i, robot in enumerate(population):
            robot.fitness = fitness_results[i]
        
        # Sort robots by fitness (higher is better)
        population.sort(key=lambda r: r.fitness, reverse=True)
        robot_to_display = population[0]
        for action_index, action in enumerate(robot_to_display.genome):
            screen.blit(background_surface, (0, 0))

            if robot_to_display.player is None:
                raise ValueError(f"Player not initialized for robot {robot_to_display.robot_id}")
            if not robot_to_display.player.alive:
                break

            if action == 'attack':
                hit = robot_to_display.player.attack(monsters=robot_to_display.monsters)
                if hit:
                    robot_to_display.fitness += 1
            else:
                robot_to_display.player.move(action)

            robot_to_display.simulate_frame(screen, generation)
            pygame.display.flip()

            # Capture the frame for the video
            frame = pygame.surfarray.array3d(screen)
            frame = cv2.transpose(frame)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            video_out.write(frame)

            time.sleep(0.05)
        print(f"Best fitness: {population[0].fitness}")
        print("===")


        next_population = population[:5]

        while len(next_population) < POPULATION_SIZE:
            parent1, parent2 = random.sample(population[:10], 2)
            child_genome = mutate(crossover(parent1.genome, parent2.genome))
            child = Robot(robot_id=len(next_population))
            child.genome = child_genome
            next_population.append(child)

        population = next_population

    print("Final genome of the best robot:", population[0].genome)
    video_out.release()

if __name__ == "__main__":
    pygame.init()

    screen = pygame.display.set_mode((GAME_WIDTH, GAME_HEIGHT))
    pygame.display.set_caption("Footsoldier Melee Simulation - AI")

    run_evolution_parallel_display(screen)

    pygame.quit()