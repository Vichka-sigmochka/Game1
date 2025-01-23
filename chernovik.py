import os
import sys
from pygame.draw import rect
import random
import pygame


class Hero(pygame.sprite.Sprite):
    def __init__(self, app, pos):
        super().__init__()
        self.image = app.load_image("player.png")
        self.rect = self.image.get_rect()
        self.app = app
        # вычисляем маску для эффективного сравнения
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect().move(
            app.tile_width * pos[0] + 15, app.tile_height * pos[1] + 5)
        self.tail = []
        self.alpha_surf = pygame.Surface((700, 400), pygame.SRCALPHA)

    def update(self, pos):
        self.rect.x += pos[0]
        self.rect.y += pos[1]
        if pygame.sprite.spritecollideany(self, self.app.tiles_group):
            self.rect.x -= pos[0]
            self.rect.y -= pos[1]

        self.tail.append([[self.rect.x - 5, self.rect.y - 8],
                               [random.randint(0, 25) / 10 - 1, random.choice([0, 0])],
                               random.randint(5, 8)])
        for t in self.tail:
            t[0][0] += t[1][0]
            t[0][1] += t[1][1]
            t[2] -= 0.5
            t[1][0] -= 0.4
            rect(self.alpha_surf, (255, 255, 255),([int(t[0][0]), int(t[0][1])], [int(t[2]) for i in range(2)]))
            if t[2] <= 0:
                self.tail.remove(t)




if __name__ == '__main__':
