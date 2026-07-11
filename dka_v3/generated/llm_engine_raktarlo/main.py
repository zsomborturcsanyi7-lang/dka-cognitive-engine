import pygame
import random
import sys
import math

# === KONSTANSOK ===
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
ORANGE = (255, 165, 0)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)

# === JÁTÉKLOGIKA (LLM) ===

def init_game():
    global player_x, player_y, items, score, lives
    player_x, player_y = 400, 300
    items = [[random.randint(50, 750), random.randint(50, 550), random.choice(['good','bad'])] for _ in range(10)]
    score = 0
    lives = 3

def update_game(keys):
    global player_x, player_y, items, score, lives
    if keys[pygame.K_LEFT] and player_x > 20: player_x -= 5
    if keys[pygame.K_RIGHT] and player_x < 780: player_x += 5
    if keys[pygame.K_UP] and player_y > 20: player_y -= 5
    if keys[pygame.K_DOWN] and player_y < 580: player_y += 5
    for item in items[:]:
        dx = abs(player_x - item[0])
        dy = abs(player_y - item[1])
        if dx < 20 and dy < 20:
            if item[2] == 'good':
                score += 1
            else:
                lives -= 1
            items.remove(item)
    if len(items) < 5:
        items.append([random.randint(50, 750), random.randint(50, 550), random.choice(['good','bad'])])

def draw_game(screen):
    pygame.draw.rect(screen, BLUE, (player_x-15, player_y-15, 30, 30))
    for item in items:
        color = GREEN if item[2] == 'good' else RED
        pygame.draw.rect(screen, color, (item[0]-8, item[1]-8, 16, 16))
    try:
        lives_text = pygame.font.Font(None, 36).render(f'Lives: {lives}', True, WHITE)
        screen.blit(lives_text, (700, 10))
    except: pass

def collision_check():
    return lives <= 0

# === FŐ JÁTÉKCIKLUS (DKA) ===
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("DKA + LLM Játék")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 36)
    big_font = pygame.font.Font(None, 72)
    
    init_game()
    running = True
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        keys = pygame.key.get_pressed()
        update_game(keys)
        
        if collision_check():
            running = False
        
        screen.fill(BLACK)
        draw_game(screen)
        
        # Pontszám kijelzés (ha van score változó)
        try:
            score_text = font.render(f"Score: {score}", True, WHITE)
            screen.blit(score_text, (10, 10))
        except:
            pass
        
        pygame.display.flip()
        clock.tick(FPS)
    
    # Game Over
    screen.fill(BLACK)
    game_over = big_font.render("GAME OVER", True, RED)
    text_rect = game_over.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 30))
    screen.blit(game_over, text_rect)
    try:
        fs = font.render(f"Végső pontszám: {score}", True, WHITE)
        sr = fs.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 30))
        screen.blit(fs, sr)
    except:
        pass
    pygame.display.flip()
    pygame.time.wait(3000)
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
