import pygame, random

pygame.init()

SCREEN_WIDTH = 400
SCREEN_HEIGHT = 600
SPEED = 4
GRAVITY = 0.5
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

    def update(self):
        self.speed += GRAVITY
        self.rect.y += self.speed
        self.trail.append(self.rect.copy())
        if len(self.trail) > 20:
            self.trail.pop(0)

    def bump(self):
        self.speed = -SPEED * 1.5

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

clock = pygame.time.Clock()

score = 0

running = True
while running:
    clock.tick(30)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE or event.key == pygame.K_UP:
                bird.bump()

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

    for i, pos in enumerate(bird.trail):
        alpha = 255 * (i / len(bird.trail))
        color = (alpha, alpha, alpha)
        pygame.draw.ellipse(screen, color, pos)
    
    for pipe in pipe_group:
        pygame.draw.rect(screen, PIPE_COLOR, pipe.rect)
    for ground in ground_group:
        pygame.draw.rect(screen, GROUND_COLOR, ground.rect)
    
    font = pygame.font.Font(None, 36)
    score_text = font.render(f'Score: {score}', True, BIRD_COLOR)
    screen.blit(score_text, (10, 10))

    pygame.display.update()

    if (pygame.sprite.spritecollideany(bird, ground_group) or
            pygame.sprite.spritecollideany(bird, pipe_group)):
        running = False

pygame.quit()
