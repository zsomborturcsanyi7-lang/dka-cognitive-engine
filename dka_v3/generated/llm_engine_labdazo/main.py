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
    global ball_x, ball_y, ball_speed_x, ball_speed_y, player_y, score
    ball_x, ball_y = 400, 300
    ball_speed_x, ball_speed_y = 5, 5
    player_y = 250
    score = 0

def update_game(keys):
    global ball_x, ball_y, ball_speed_x, ball_speed_y, player_y, score
    ball_x += ball_speed_x
    ball_y += ball_speed_y
    if ball_x <= 0 or ball_x >= SCREEN_WIDTH:
        ball_speed_x = -ball_speed_x
    if ball_y <= 0:
        ball_speed_y = -ball_speed_y
    if keys[pygame.K_UP]:
        player_y -= 7
    if keys[pygame.K_DOWN]:
        player_y += 7
    # Ütő visszaveri a labdát
    if ball_x >= 760 and abs(ball_y - player_y) < 60:
        ball_speed_x = -ball_speed_x
        score += 1
    # Ha a labda elhagyja a képernyőt jobbra
    if ball_x > SCREEN_WIDTH:
        ball_x, ball_y = 400, 300

def draw_game(screen):
    pygame.draw.circle(screen, WHITE, (int(ball_x), int(ball_y)), 10)
    pygame.draw.rect(screen, BLUE, (770, player_y, 20, 80))

def collision_check():
    global ball_x
    return ball_x < 0

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
