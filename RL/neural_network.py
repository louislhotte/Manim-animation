import pygame
import random
import time
import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F

# Initialize Pygame and set up display
pygame.init()

GAME_WIDTH = 1200
GAME_HEIGHT = 800
FPS = 20
SIMULATION_TIME = 30
NUM_GENERATIONS = 50
GENERATIONS_TO_CAPTURE = [1, 3, 5, 10, 20, 35, 50]  # Specific generations to capture video
ENCOUNTER_RADIUS = 200

screen = pygame.display.set_mode((GAME_WIDTH, GAME_HEIGHT))
pygame.display.set_caption("Footsoldier Melee Simulation")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)

# Dummy classes to replace the external modules for this example
class Footsoldier:
    def __init__(self, position, screen):
        self.position = position
        self.health = 100
        self.alive = True
        self.gold = 0
        self.screen = screen

    def move(self, direction):
        if direction == 'left':
            self.position[0] -= 10
        elif direction == 'right':
            self.position[0] += 10
        elif direction == 'up':
            self.position[1] -= 10
        elif direction == 'down':
            self.position[1] += 10

    def attack(self, monsters):
        for monster in monsters:
            if np.linalg.norm(np.array(self.position) - np.array(monster.position)) < 50:
                monster.alive = False

    def draw(self, camera_x, camera_y):
        pygame.draw.circle(self.screen, (0, 255, 0), (self.position[0] - camera_x, self.position[1] - camera_y), 10)

class Monster:
    def __init__(self, position, monster_type):
        self.position = position
        self.health = 50 if monster_type == 'weak' else 100
        self.alive = True

    def draw(self, screen, camera_x, camera_y):
        if self.alive:
            pygame.draw.circle(screen, (255, 0, 0), (self.position[0] - camera_x, self.position[1] - camera_y), 10)

class NeuralNet(nn.Module):
    def __init__(self):
        super(NeuralNet, self).__init__()
        self.fc1 = nn.Linear(8, 64)
        self.fc2 = nn.Linear(64, 32)
        self.fc3 = nn.Linear(32, 5)  # 5 possible actions

    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = self.fc3(x)
        return x

class Robot:
    def __init__(self, robot_id, model=None):
        self.robot_id = robot_id
        self.fitness = 0
        self.player = Footsoldier([100, 100], screen)  
        self.monsters = self.spawn_monsters(seed=34)  
        self.encountered_monsters = set()

        self.model = model if model else NeuralNet()

        self.optimizer = optim.Adam(self.model.parameters(), lr=0.001)
        self.criterion = nn.MSELoss()

    def spawn_monsters(self, seed):
        random.seed(seed)
        return [Monster(position=(random.randint(0, GAME_WIDTH), random.randint(0, GAME_HEIGHT)),
                        monster_type='strong' if i % 5 == 0 else 'weak') for i in range(20)]

    def evaluate_fitness(self):
        self.fitness += self.player.gold
        for monster in self.monsters:
            distance_to_monster = np.linalg.norm(np.array(self.player.position) - np.array(monster.position))
            if distance_to_monster < ENCOUNTER_RADIUS and monster not in self.encountered_monsters:
                self.encountered_monsters.add(monster)
                self.fitness += 1
            if not monster.alive:
                self.fitness += 30 

    def simulate(self, capture_video=False, out=None, generation=None):
        start_time = time.time()
        state = self.get_state()

        for _ in range(4000):
            if time.time() - start_time > SIMULATION_TIME or not self.player.alive:
                break

            action = self.choose_action(state)
            self.perform_action(action)
            new_state = self.get_state()
            reward = self.calculate_reward()
            self.optimize_model(state, action, reward, new_state)

            state = new_state

            if capture_video:
                frame = pygame.surfarray.array3d(screen)
                frame = np.rot90(frame)
                frame = np.flipud(frame)
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                out.write(frame)

            clock.tick(FPS)

        self.evaluate_fitness()

    def get_state(self):
        player_x, player_y = self.player.position
        nearest_monster = min(self.monsters, key=lambda m: np.linalg.norm(np.array(self.player.position) - np.array(m.position)))
        monster_x, monster_y = nearest_monster.position
        return np.array([player_x, player_y, self.player.health, nearest_monster.health,
                         monster_x, monster_y, nearest_monster.alive, len(self.encountered_monsters)])

    def choose_action(self, state):
        state = torch.FloatTensor(state)
        with torch.no_grad():
            action_values = self.model(state)
        return torch.argmax(action_values).item()

    def perform_action(self, action):
        actions = ['left', 'right', 'up', 'down', 'attack']
        chosen_action = actions[action]
        if chosen_action == 'attack':
            self.player.attack(monsters=self.monsters)
        else:
            self.player.move(chosen_action)

    def calculate_reward(self):
        reward = 0
        for monster in self.monsters:
            if not monster.alive:
                reward += 30
        return reward

    def optimize_model(self, state, action, reward, next_state):
        state = torch.FloatTensor(state)
        next_state = torch.FloatTensor(next_state)
        reward = torch.FloatTensor([reward])
        action = torch.LongTensor([action])

        q_values = self.model(state)
        next_q_values = self.model(next_state)

        target_q_value = reward + 0.99 * torch.max(next_q_values)
        expected_q_value = q_values[action]

        loss = self.criterion(expected_q_value, target_q_value)

        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

def train_neural_network():
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter('robot_training.avi', fourcc, FPS, (GAME_WIDTH, GAME_HEIGHT))

    model = NeuralNet()

    for generation in range(NUM_GENERATIONS):
        print(f"Generation {generation + 1}")
        capture_video = (generation + 1) in GENERATIONS_TO_CAPTURE

        robot = Robot(robot_id=0, model=model)
        robot.simulate(capture_video=capture_video, out=out, generation=generation)

        print(f"Robot Fitness: {robot.fitness}")

    out.release()

if __name__ == '__main__':
    train_neural_network()
    pygame.quit()
    cv2.destroyAllWindows()
