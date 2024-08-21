import pygame
import random

pygame.init()

SCREEN_WIDTH = 400
SCREEN_HEIGHT = 600
SPEED = 8
GRAVITY = 1
GAME_SPEED = 5

PIPE_WIDTH = 50
PIPE_HEIGHT = 300
PIPE_GAP = 150

BIRD_SIZE = 20
BIRD_COLOR = (0, 0, 0)
PIPE_COLOR = (0, 0, 0)
BACKGROUND_COLOR = (255, 255, 255)
GROUND_COLOR = (0, 0, 0)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Obstacle Game - Enhanced Version')
class Bird(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.rect = pygame.Rect(SCREEN_WIDTH / 6, SCREEN_HEIGHT / 2, BIRD_SIZE, BIRD_SIZE)
        self.speed = SPEED
        self.trail = []
        self.horizontal_speed = 5  # Assume a constant horizontal speed

    def update(self):
        self.speed += GRAVITY
        self.rect.y += self.speed
        # Update the trail
        for i in range(len(self.trail)):
            self.trail[i] = (self.trail[i][0] - self.horizontal_speed, self.trail[i][1])
        self.trail.append((self.rect.centerx, self.rect.centery))
        if len(self.trail) > 20:
            self.trail.pop(0)

    def draw_trail(self, screen):
        if len(self.trail) > 1:
            for i in range(1, len(self.trail)):
                start_pos = self.trail[i - 1]
                end_pos = self.trail[i]
                pygame.draw.line(screen, (31, 31, 31), start_pos, end_pos, BIRD_SIZE // 2)

    def bump(self):
        self.speed = -SPEED * 1.2

class Pipe(pygame.sprite.Sprite):
    def __init__(self, inverted, xpos, ysize):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.Surface((PIPE_WIDTH, PIPE_HEIGHT))
        self.image.fill(PIPE_COLOR)
        self.rect = self.image.get_rect()
        self.rect.x = xpos
        if inverted:
            self.rect.y = -(self.rect.height - ysize)
        else:
            self.rect.y = SCREEN_HEIGHT - ysize

    def update(self):
        self.rect.x -= GAME_SPEED

class Ground(pygame.sprite.Sprite):
    def __init__(self, xpos):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.Surface((SCREEN_WIDTH, 100))
        self.image.fill(GROUND_COLOR)
        self.rect = self.image.get_rect()
        self.rect.x = xpos
        self.rect.y = SCREEN_HEIGHT - 100

    def update(self):
        self.rect.x -= GAME_SPEED

class Boundary(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.Surface((SCREEN_WIDTH, 5))
        self.image.fill(GROUND_COLOR)
        self.rect = self.image.get_rect()
        self.rect.x = 0
        self.rect.y = SCREEN_HEIGHT - 5

class Ceiling(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.Surface((SCREEN_WIDTH, 5))
        self.image.fill(GROUND_COLOR)
        self.rect = self.image.get_rect()
        self.rect.x = 0
        self.rect.y = 0

def is_off_screen(sprite):
    return sprite.rect.x < -sprite.rect.width

def get_random_pipes(xpos):
    size = random.randint(100, 300)
    pipe = Pipe(False, xpos, size)
    pipe_inverted = Pipe(True, xpos, SCREEN_HEIGHT - size - PIPE_GAP)
    return pipe, pipe_inverted

bird_group = pygame.sprite.Group()
bird = Bird()
bird_group.add(bird)

ground_group = pygame.sprite.Group()
ground = Ground(0)
ground_group.add(ground)

pipe_group = pygame.sprite.Group()
for i in range(2):
    pipes = get_random_pipes(SCREEN_WIDTH * i + 800)
    pipe_group.add(pipes[0])
    pipe_group.add(pipes[1])

boundary_group = pygame.sprite.Group()
boundary = Boundary()
boundary_group.add(boundary)

ceiling_group = pygame.sprite.Group()
ceiling = Ceiling()
ceiling_group.add(ceiling)

clock = pygame.time.Clock()

score = 0
game_over = False

running = True
while running:
    clock.tick(30)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE or event.key == pygame.K_UP:
                if not game_over:
                    bird.bump()
                else:
                    game_over = False
                    score = 0
                    bird.rect.y = SCREEN_HEIGHT / 2
                    bird.speed = SPEED
                    bird.trail.clear()
                    pipe_group.empty()
                    for i in range(2):
                        pipes = get_random_pipes(SCREEN_WIDTH * i + 800)
                        pipe_group.add(pipes[0])
                        pipe_group.add(pipes[1])

    if not game_over:
        screen.fill(BACKGROUND_COLOR)
        
        if is_off_screen(ground):
            ground_group.remove(ground)
            new_ground = Ground(SCREEN_WIDTH - 20)
            ground_group.add(new_ground)
        
        if is_off_screen(pipe_group.sprites()[0]):
            pipe_group.remove(pipe_group.sprites()[0])
            pipe_group.remove(pipe_group.sprites()[0])
            pipes = get_random_pipes(SCREEN_WIDTH * 2)
            pipe_group.add(pipes[0])
            pipe_group.add(pipes[1])
            score += 1

        bird_group.update()
        ground_group.update()
        pipe_group.update()
        boundary_group.update()
        ceiling_group.update()

        bird.draw_trail(screen)
        pygame.draw.ellipse(screen, BIRD_COLOR, bird.rect)
        
        for pipe in pipe_group:
            screen.blit(pipe.image, pipe.rect)
        for ground in ground_group:
            screen.blit(ground.image, ground.rect)
        for boundary in boundary_group:
            screen.blit(boundary.image, boundary.rect)
        for ceiling in ceiling_group:
            screen.blit(ceiling.image, ceiling.rect)
        
        font = pygame.font.Font(None, 36)
        score_text = font.render(f'Score: {score}', True, BIRD_COLOR)
        screen.blit(score_text, (10, 10))

        pygame.display.update()

        if (pygame.sprite.spritecollideany(bird, ground_group) or
                pygame.sprite.spritecollideany(bird, pipe_group) or
                pygame.sprite.spritecollideany(bird, boundary_group) or
                pygame.sprite.spritecollideany(bird, ceiling_group)):
            game_over = True
    
    else:
        font = pygame.font.Font(None, 74)
        game_over_text = font.render('Game Over', True, BIRD_COLOR)
        screen.blit(game_over_text, (SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 - 50))
        pygame.display.update()

pygame.quit()
