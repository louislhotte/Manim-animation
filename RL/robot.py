import random
import copy
import pygame
from footsoldier import Footsoldier
from monsters import Monster
import time
from game import GAME_HEIGHT, GAME_WIDTH, tile_image

# Screen and world dimensions
WORLD_WIDTH = 2000
WORLD_HEIGHT = 2000
SIMULATION_TIME = 120 

# Constants for genetic algorithm
POPULATION_SIZE = 20
GENOME_LENGTH = 100  # Number of actions in a sequence
MUTATION_RATE = 0.1
NUM_GENERATIONS = 50

# Possible actions for the bot
ACTIONS = ['left', 'right', 'up', 'down', 'attack', 'idle']

# Pre-render the full background on a larger surface
background_surface = pygame.Surface((WORLD_WIDTH, WORLD_HEIGHT))

def draw_full_background(surface, tile_image):
    tile_width = tile_image.get_width()
    tile_height = tile_image.get_height()
    
    for y in range(0, WORLD_HEIGHT, tile_height):
        for x in range(0, WORLD_WIDTH, tile_width):
            surface.blit(tile_image, (x, y))

# Generate the full background
draw_full_background(background_surface, tile_image)

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

    def evaluate_fitness(self, screen, seed):
        # Reset game state for each evaluation with the same seed
        random.seed(seed)
        player = Footsoldier((100, 100), screen)
        monsters = self.spawn_monsters(seed)

        for action in self.genome:
            if action == 'attack':
                player.attack(monsters=monsters)
            else:
                player.move(action)
            self.simulate_frame(screen, player, monsters)
                
        self.fitness = player.gold

    def simulate_frame(self, screen, player, monsters):
        # Simulate a single frame (basic environment interaction)
        camera_x, camera_y = center_camera_on_player(player.position)
        screen.blit(background_surface, (0, 0), (camera_x, camera_y, GAME_WIDTH, GAME_HEIGHT))
        player.draw(camera_x, camera_y)

        for monster in monsters:
            if monster.alive:
                monster.handle_event(None, player)
                monster.draw(screen, camera_x, camera_y)

        # Display the robot ID and generation number
        self.display_info(screen)

        pygame.display.flip()

    def display_info(self, screen):
        font = pygame.font.Font(None, 36)
        text = font.render(f"Robot ID: {self.robot_id}  Generation: {generation + 1}", True, (255, 255, 255))
        screen.blit(text, (10, 10))

    def spawn_monsters(self, seed):
        # Generate monsters with a consistent random seed
        random.seed(seed)
        return [Monster(position=(random.randint(0, WORLD_WIDTH), random.randint(0, WORLD_HEIGHT)),
                        monster_type='strong' if i % 2 == 0 else 'weak') for i in range(30)]


def run_evolution(screen):
    population = [Robot(robot_id=i) for i in range(POPULATION_SIZE)]
    
    for generation in range(NUM_GENERATIONS):
        print(f"Generation {generation + 1}")

        # Evaluate fitness
        for robot in population:
            robot.evaluate_fitness(screen, initial_seed)

        # Sort robots by fitness (higher is better)
        population.sort(key=lambda robot: robot.fitness, reverse=True)
        print(f"Best fitness: {population[0].fitness}")

        # Create the next generation
        next_population = population[:2]  # Keep the top 2 robots
        while len(next_population) < POPULATION_SIZE:
            parent1, parent2 = random.sample(population[:10], 2)
            child_genome = mutate(crossover(parent1.genome, parent2.genome))
            child = Robot(robot_id=len(next_population))
            child.genome = child_genome
            next_population.append(child)

        population = next_population

    print("Final genome of the best robot:", population[0].genome)

def run_evolution_parallel(screen):
    # Set a consistent random seed for the entire evolutionary process
    initial_seed = 42  # This seed controls the environment consistency
    
    global generation
    population = [Robot(robot_id=i) for i in range(POPULATION_SIZE)]
    
    for generation in range(NUM_GENERATIONS):
        print(f"Generation {generation + 1}")
        
        # Evaluate each robot's fitness using the same seed for consistency
        for robot in population:
            robot.evaluate_fitness(screen, initial_seed)
        
        # Sort robots by fitness (higher is better)
        population.sort(key=lambda robot: robot.fitness, reverse=True)
        print(f"Best fitness: {population[0].fitness}")

        # Display the best robot of the generation
        best_robot = population[0]
        best_player = Footsoldier((100, 100), screen)
        best_monsters = best_robot.spawn_monsters(initial_seed)

        for action in best_robot.genome:
            if action == 'attack':
                best_player.attack(monsters=best_monsters)
            else:
                best_player.move(action)
            
            # Simulate a single frame for the best robot
            best_robot.simulate_frame(screen, best_player, best_monsters)
            time.sleep(0.05)  # Add a small delay to observe the actions clearly
        
        # Create the next generation
        next_population = population[:2]  # Keep the top 2 robots
        while len(next_population) < POPULATION_SIZE:
            parent1, parent2 = random.sample(population[:10], 2)
            child_genome = mutate(crossover(parent1.genome, parent2.genome))
            child = Robot(robot_id=len(next_population))
            child.genome = child_genome
            next_population.append(child)

        population = next_population

    print("Final genome of the best robot:", population[0].genome)



def mutate(genome):
    new_genome = copy.deepcopy(genome)
    for i in range(len(new_genome)):
        if random.random() < MUTATION_RATE:
            new_genome[i] = random.choice(ACTIONS)
    return new_genome

def crossover(parent1, parent2):
    crossover_point = random.randint(0, GENOME_LENGTH - 1)
    return parent1[:crossover_point] + parent2[crossover_point:]


if __name__ == "__main__":
    pygame.init()

    screen = pygame.display.set_mode((GAME_WIDTH, GAME_HEIGHT))
    pygame.display.set_caption("Footsoldier Melee Simulation - AI")
    
    run_evolution_parallel(screen)

    pygame.quit()
