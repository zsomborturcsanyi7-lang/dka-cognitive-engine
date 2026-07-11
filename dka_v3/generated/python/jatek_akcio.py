import import pygame, random, sys

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
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
CYAN = (0, 255, 255)

# === OSZTÁLYOK ===


# === FŐ JÁTÉK ===
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("DKA V3 - {game_title}")
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
        if random.random() < 0.02:
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
        screen.fill(WHITE)
        player.draw(screen)
        for enemy in enemies:
            enemy.draw(screen)

        # Pontszám
        score_text = font.render(f"Score: {score}", True, BLACK)
        screen.blit(score_text, (10, 10))

        pygame.display.flip()
        clock.tick(FPS)

    # Játék vége
    screen.fill(WHITE)
    game_over = big_font.render("GAME OVER", True, RED)
    text_rect = game_over.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30))
    screen.blit(game_over, text_rect)
    final_score = font.render(f"Végső pontszám: {score}", True, BLACK)
    score_rect = final_score.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30))
    screen.blit(final_score, score_rect)
    pygame.display.flip()
    pygame.time.wait(3000)
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()