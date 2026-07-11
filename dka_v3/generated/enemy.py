import pygame
import random

class Enemy:
    def __init__(self):
        self.x = random.randint(0, SCREEN_WIDTH - 40)
        self.y = -50
        self.width = 40
        self.height = 40
        self.speed = random.randint(2, 5)

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