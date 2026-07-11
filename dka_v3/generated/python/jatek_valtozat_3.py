import pygame
import random
import sys

# === KONSTANSONS ===
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# === SZÍNEK ===
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
PLAYER_COL = (255, 20, 147)
ENEMY_COL = (0, 255, 255)
BG_COL = (25, 25, 35)
SCORE_COL = (0, 0, 0)

# === OSZTÁLYOK ===
class Player:
    def __init__(self):
        self.x = SCREEN_WIDTH // 2
        self.y = SCREEN_HEIGHT - 100
        self.width = 48
        self.height = 48
        self.speed = 8

    def move(self, keys):
        if keys[pygame.K_LEFT] and self.x > 0:
            self.x -= self.speed
        if keys[pygame.K_RIGHT] and self.x < SCREEN_WIDTH - self.width:
            self.x += self.speed
        if keys[pygame.K_UP] and self.y > 0:
            self.y -= self.speed
        if keys[pygame.K_DOWN] and self.y < SCREEN_HEIGHT - self.height:
            self.y += self.speed

    def draw(self, screen):
        pygame.draw.rect(screen, PLAYER_COL, (self.x, self.y, self.width, self.height))
        pygame.draw.rect(screen, BLACK, (self.x, self.y, self.width, self.height), 2)
class Enemy:
    def __init__(self):
        self.x = random.randint(0, SCREEN_WIDTH - 25)
        self.y = -50
        self.width = 25
        self.height = 25
        self.speed = random.randint(3, 6)

    def move(self):
        self.y += self.speed

    def draw(self, screen):
        pygame.draw.rect(screen, ENEMY_COL, (self.x, self.y, self.width, self.height))
        pygame.draw.rect(screen, BLACK, (self.x, self.y, self.width, self.height), 2)

    def collides_with(self, other):
        return (self.x < other.x + other.width and
                self.x + self.width > other.x and
                self.y < other.y + other.height and
                self.y + self.height > other.y)

# === FŐ JÁTÉK ===
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("DKA V3 Játék")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 36)
    big_font = pygame.font.Font(None, 72)

    player = Player()
    enemies = []
    score = 0
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        player.move(keys)

        # Ellenfelek spawnolása
        if random.random() < 0.032:
            enemies.append(Enemy())

        # Ellenfelek frissítése
        for enemy in enemies[:]:
            enemy.move()
            if enemy.y > SCREEN_HEIGHT:
                enemies.remove(enemy)
                score += 1
            elif enemy.collides_with(player):
                running = False

        # Rajzolás
        screen.fill(BG_COL)
        player.draw(screen)
        for enemy in enemies:
            enemy.draw(screen)

        # Pontszám
        score_text = font.render(f"Score: {score}", True, SCORE_COL)
        screen.blit(score_text, (10, 10))

        pygame.display.flip()
        clock.tick(FPS)

    # Játék vége
    screen.fill(BG_COL)
    game_over = big_font.render("GAME OVER", True, ENEMY_COL)
    text_rect = game_over.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30))
    screen.blit(game_over, text_rect)
    final_score = font.render(f"Végső pontszám: {score}", True, SCORE_COL)
    score_rect = final_score.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30))
    screen.blit(final_score, score_rect)
    pygame.display.flip()
    pygame.time.wait(3000)
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()