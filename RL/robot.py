import random
import copy
import pygame
from footsoldier import Footsoldier
from monsters import Monster
import time

pygame.init()

# Screen and world dimensions
WORLD_WIDTH = 1200
WORLD_HEIGHT = 800
SIMULATION_TIME = 240 
GAME_WIDTH = 1200
GAME_HEIGHT = 800
screen = pygame.display.set_mode((GAME_WIDTH, GAME_HEIGHT))
tile_image = pygame.image.load('RL/tile.png').convert()

# Constants for genetic algorithm
POPULATION_SIZE = 10
GENOME_LENGTH = 200  # Number of actions in a sequence
MUTATION_RATE = 0.1
NUM_GENERATIONS = 20

# Possible actions for the bot
ACTIONS = ['left', 'right', 'up', 'down', 'attack']

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
        self.player = None  # Initialize as None
        self.monsters = []  # Initialize as an empty list

    def evaluate_fitness(self, screen, seed):
        start_time = time.time()
        
        # Initialize player and monsters for this robot
        random.seed(seed)
        self.player = Footsoldier((100, 100), screen)
        self.monsters = self.spawn_monsters(seed)
        
        for action in self.genome:
            # Check if simulation time has exceeded
            if time.time() - start_time > SIMULATION_TIME:
                break

            # Stop simulation if the player is dead
            if not self.player.alive:
                break

            if action == 'attack':
                self.player.attack(monsters=self.monsters)
            else:
                self.player.move(action)
            self.simulate_frame(screen)
        
        self.fitness = self.player.gold

    def simulate_frame(self, screen):
        if self.player is None:
            raise ValueError(f"Player not initialized for robot {self.robot_id}")
        
        # Simulate a single frame (basic environment interaction)
        camera_x, camera_y = center_camera_on_player(self.player.position)
        screen.blit(background_surface, (0, 0), (camera_x, camera_y, GAME_WIDTH, GAME_HEIGHT))
        self.player.draw(camera_x, camera_y)

        if self.player.alive:
            for monster in self.monsters:
                if monster.alive:
                    monster.handle_event(None, self.player)
                    monster.draw(screen, camera_x, camera_y)

        # Display the robot ID and generation number
        self.display_info(screen)

    def display_info(self, screen):
        font = pygame.font.Font(None, 36)
        text = font.render(f"Robot ID: {self.robot_id}  Generation: {generation + 1}", True, (255, 255, 255))
        screen.blit(text, (10, 10))

    def spawn_monsters(self, seed):
        # Generate monsters with a consistent random seed
        random.seed(seed)
        return [Monster(position=(random.randint(0, WORLD_WIDTH), random.randint(0, WORLD_HEIGHT)),
                        monster_type='strong' if i % 5 == 0 else 'weak') for i in range(15)]

def mutate(genome):
    new_genome = copy.deepcopy(genome)
    for i in range(len(new_genome)):
        if random.random() < MUTATION_RATE:
            new_genome[i] = random.choice(ACTIONS)
    return new_genome

def crossover(parent1, parent2):
    crossover_point = random.randint(0, GENOME_LENGTH - 1)
    return parent1[:crossover_point] + parent2[crossover_point:]

def run_evolution_single_display(screen):
    initial_seed = 69  # Consistent random seed for environment
    
    global generation
    population = [Robot(robot_id=i) for i in range(POPULATION_SIZE)]
    
    for generation in range(NUM_GENERATIONS):
        print(f"Generation {generation + 1}")
        for robot in population:
            robot.evaluate_fitness(screen, initial_seed)
        robot_to_display = random.choice(population)

        # Simulate the selected robot
        for action_index, action in enumerate(robot_to_display.genome):
            screen.blit(background_surface, (0, 0))
            
            if robot_to_display.player is None:
                raise ValueError(f"Player not initialized for robot {robot_to_display.robot_id}")
            
            # Stop processing actions if the player is dead
            if not robot_to_display.player.alive:
                break
            
            if action == 'attack':
                robot_to_display.player.attack(monsters=robot_to_display.monsters)
            else:
                robot_to_display.player.move(action)
            
            robot_to_display.simulate_frame(screen)
            pygame.display.flip()
            time.sleep(0.05)

        # Evaluate fitness for each robot after finishing its genome
        for robot in population:
            robot.fitness = robot.player.gold
        
        # Sort robots by fitness (higher is better)
        population.sort(key=lambda r: r.fitness, reverse=True)
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

if __name__ == "__main__":
    pygame.init()

    screen = pygame.display.set_mode((GAME_WIDTH, GAME_HEIGHT))
    pygame.display.set_caption("Footsoldier Melee Simulation - AI")
    
    run_evolution_single_display(screen)

    pygame.quit()
