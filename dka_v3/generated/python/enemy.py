import pygame
import random

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
PLAYER_COL = (0, 102, 204)
ENEMY_COL = (255, 50, 50)

class Enemy:
    def __init__(self):
        self.x = random.randint(0, SCREEN_WIDTH - 47)
        self.y = -50
        self.width = 47
        self.height = 47
        self.speed = random.randint(1, 7)

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