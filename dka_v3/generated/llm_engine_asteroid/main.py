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
    global ship_x, ship_y, bullets, asteroids, score
    ship_x, ship_y = 400, 500
    bullets = []
    asteroids = []
    score = 0

def update_game(keys):
    global ship_x, ship_y, bullets, asteroids, score
    if keys[pygame.K_LEFT] and ship_x > 20: ship_x -= 5
    if keys[pygame.K_RIGHT] and ship_x < 780: ship_x += 5
    if keys[pygame.K_SPACE]:
        bullets.append([ship_x, ship_y - 20])
    for b in bullets[:]:
        b[1] -= 10
        if b[1] < 0: bullets.remove(b)
    if random.random() < 0.02:
        asteroids.append([random.randint(20, 780), -20])
    for a in asteroids[:]:
        a[1] += 3
        if a[1] > SCREEN_HEIGHT: asteroids.remove(a)
    for b in bullets[:]:
        for a in asteroids[:]:
            if abs(b[0]-a[0]) < 20 and abs(b[1]-a[1]) < 20:
                bullets.remove(b)
                asteroids.remove(a)
                score += 1
                break

def draw_game(screen):
    pygame.draw.polygon(screen, GREEN, [(ship_x, ship_y-20), (ship_x-15, ship_y+10), (ship_x+15, ship_y+10)])
    for a in asteroids:
        pygame.draw.circle(screen, RED, (int(a[0]), int(a[1])), 15)
    for b in bullets:
        pygame.draw.rect(screen, YELLOW, (b[0]-2, b[1]-5, 4, 10))

def collision_check():
    for a in asteroids:
        if abs(a[0]-ship_x) < 25 and abs(a[1]-ship_y) < 25:
            return True
    return False

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
