import os
import sys
import pygame
from pygame.draw import rect
from pygame.math import Vector2


jump_start_time = 0
GRAVITY = Vector2(0, 0.86)


class Hero(pygame.sprite.Sprite):
    def __init__(self, app, image, pos, platforms, *groups):
        super().__init__(*groups) # app.all_sprites
        self.image = app.load_image("player.jpg")
        self.rect = self.image.get_rect(center=pos)
        self.app = app
        self.jump_amount = 11
        self.vel = Vector2(0, 0) # скорость
        self.rect = self.image.get_rect(center=pos)
        self.platforms = platforms  # все объекты(блоки, треугольники, монеты)
        self.is_jump = False # прыгал или нет
        self.on_ground = False # находится на земле или нет
        self.died = False  # умер или нет
        self.win = False # выиграл или нет

    def collide(self, yvel, platforms): # столкновения
        global coins
        for p in platforms:
            if pygame.sprite.collide_rect(self, p):
                if isinstance(p, Block):
                    if yvel > 0:
                        self.rect.bottom = p.rect.top
                        self.vel.y = 0
                        self.on_ground = True
                        self.is_jump = False
                    elif yvel < 0:
                        self.rect.top = p.rect.bottom
                    else:
                        self.vel.x = 0
                        self.rect.right = p.rect.left
                if isinstance(p, Triangle):
                    self.died = True
                if isinstance(p, Coin):
                    coins += 1
                    p.rect.x = 0
                    p.rect.y = 0
                if isinstance(p, End):
                    self.win = True



    def update(self):
        if self.is_jump:
            if self.on_ground:
                self.vel.y = -self.jump_amount
        if not self.on_ground:
            self.vel = self.vel + GRAVITY
            if self.vel.y > 100:
                self.vel.y = 100
        self.collide(0, self.platforms)
        self.rect.top = self.rect.top + self.vel.y
        self.on_ground = False
        self.collide(self.vel.y, self.platforms)


class Draw(pygame.sprite.Sprite):
    def __init__(self, img, pos, *groups):
        super().__init__(*groups)
        self.image = img
        self.rect = self.image.get_rect(topleft=pos)


class Block(Draw):
    def __init__(self, img, pos, *groups):
        super().__init__(img, pos, *groups)


class Triangle(Draw):
    def __init__(self, img, pos, *groups):
        super().__init__(img, pos, *groups)


class Coin(Draw):
    def __init__(self, img, pos, *groups):
        super().__init__(img, pos, *groups)


class End(Draw):
    def __init__(self, img, pos, *groups):
        super().__init__(img, pos, *groups)


def Spin(surf, image, pos, item, angle):
    width, height = image.get_size()
    box = [Vector2(0, 0), Vector2(width, 0), Vector2(width, -height), Vector2(0, -height)]
    box_spin = []
    for b in box:
        box_spin.append(b.rotate(angle))
    min_box = (min(box_spin, key=lambda p: p[0])[0], min(box_spin, key=lambda p: p[1])[1])
    max_box = (max(box_spin, key=lambda p: p[0])[0], max(box_spin, key=lambda p: p[1])[1])
    turn = Vector2(item[0], -item[1])
    turn_spin = turn.rotate(angle)
    turn_move = turn_spin - turn
    first = (pos[0] - item[0] + min_box[0] - turn_move[0], pos[1] - item[1] - max_box[1] + turn_move[1])
    spin_img = pygame.transform.rotozoom(image, angle, 1)
    surf.blit(spin_img, first)


class App:
    def __init__(self):
        pygame.init()
        self.width = 800
        self.height = 600
        self.clock = pygame.time.Clock()
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption('ГеометрияДэш')
        self.hero = None
        self.angle = 0
        self.all_sprites = pygame.sprite.Group()
        self.elements = pygame.sprite.Group()
        self.fps = 50
        self.Camera = 0

    def terminate(self):
        pygame.quit()
        sys.exit()

    def move_map(self):
        for sprite in self.elements:
            sprite.rect.x -= self.Camera

    def load_image(self, name, colorkey=None):
        fullname = os.path.join('data', name)
        if not os.path.isfile(fullname):
            print(f"Файл с изображением '{fullname}' не найден")
            sys.exit()
        image = pygame.image.load(fullname)
        if colorkey is not None:
            image = image.convert()
            if colorkey == -1:
                colorkey = image.get_at((0, 0))
            image.set_colorkey(colorkey)
        else:
            image = image.convert_alpha()
        return image

    def generate_level(self, level):
        x = 0
        y = 0
        for i in range(len(level)):
            for j in range(len(level[i])):
                if level[i][j] == '#':
                    Block(self.load_image('block.jpg'), (x, y), self.elements)
                x += 35
            y += 35
            x = 0
        new_player = Hero(self, self.load_image('player.jpg'), (100, 100), self.elements, self.all_sprites)
        return new_player

    def load_level(self, filename):
        filename = "data/" + filename
        with open(filename, 'r') as mapFile:
            level_map = [line.strip() for line in mapFile]
        max_width = max(map(len, level_map))
        return list(map(lambda x: x.ljust(max_width, '.'), level_map))

    def run_game(self, map):
        icon = self.load_image("player.jpg")
        pygame.display.set_icon(icon)
        run = True
        self.hero = self.generate_level(self.load_level('map.txt'))
        while run:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.terminate()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_1:  # измениться при реализации столкновений
                    self.end_screen()
                    run = False
            keys = pygame.key.get_pressed()
            self.hero.vel.x = 5  # скорость
            if keys[pygame.K_SPACE] or keys[pygame.K_UP]:
                self.hero.is_jump = True
            self.all_sprites.update()
            self.Camera = self.hero.vel.x
            self.move_map()
            self.screen.fill(pygame.Color('blue'))
            if self.hero.is_jump:
                self.angle -= 8.1712
                Spin(self.screen, self.hero.image, self.hero.rect.center, (16, 16), self.angle)
            else:
                self.all_sprites.draw(self.screen)
            self.elements.draw(self.screen)
            pygame.display.flip()
            self.clock.tick(50)

    def start_screen(self):
        intro_text = [" ГеометрияДэш", "",
                      "Выбери уровень"]
        fon = pygame.transform.scale(self.load_image('screen.jpg'), (self.width, self.height))
        self.screen.blit(fon, (0, 0))
        self.click1 = True
        self.click2 = False
        self.start = False
        font = pygame.font.Font(None, 30)
        text_coord = 50
        for line in intro_text:
            string_rendered = font.render(line, 0, pygame.Color('black'))
            intro_rect = string_rendered.get_rect()
            text_coord += 10
            intro_rect.top = text_coord
            intro_rect.x = self.width / 2 - 85
            text_coord += intro_rect.height
            self.screen.blit(string_rendered, intro_rect)
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.terminate()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.width / 2 - 70 <= mouse[0] <= self.width / 2 + 70 and self.height / 2 - 20 <= mouse[1] <= self.height / 2 + 20:
                        app.run_game('map.txt')
                    if self.width / 2 - 70 <= mouse[0] <= self.width / 2 - 10 and self.height / 2 - 100 <= mouse[1] <= self.height / 2 - 40:
                        self.click1 = True
                        self.click2 = False
                    if self.width / 2 + 10 <= mouse[0] <= self.width / 2 + 70 and self.height / 2 - 100 <= mouse[1] <= self.height / 2 - 40:
                        self.click1 = False
                        self.click2 = True
            keys = pygame.key.get_pressed()
            if keys[pygame.K_RIGHT]:
                self.click1 = False
                self.click2 = True
            if keys[pygame.K_LEFT]:
                self.click1 = True
                self.click2 = False
            if keys[pygame.K_DOWN]:
                self.start = True
            if keys[pygame.K_SPACE] and self.start:
                app.run_game('map.txt')
            mouse = pygame.mouse.get_pos()
            if self.start or self.width / 2 - 70 <= mouse[0] <= self.width / 2 + 70 and self.height / 2 - 20 <= mouse[1] <= self.height / 2 + 20:
                pygame.draw.rect(self.screen, (128, 255, 0), [self.width / 2 - 70, self.height / 2 - 20, 140, 40])
            else:
                pygame.draw.rect(self.screen, (0, 255, 0), [self.width / 2 - 70, self.height / 2 - 20, 140, 40])
            if self.width / 2 - 70 <= mouse[0] <= self.width / 2 - 10 and self.height / 2 - 100 <= mouse[1] <= self.height / 2 - 40:
                if self.click1:
                    pygame.draw.rect(self.screen, (0, 255, 0), [self.width / 2 - 70, self.height / 2 - 100, 60, 60])
                else:
                    pygame.draw.rect(self.screen, (128, 255, 0), [self.width / 2 - 70, self.height / 2 - 100, 60, 60])
            else:
                if self.click1:
                    pygame.draw.rect(self.screen, (0, 255, 0), [self.width / 2 - 70, self.height / 2 - 100, 60, 60])
                else:
                    pygame.draw.rect(self.screen, (0, 0, 0), [self.width / 2 - 70, self.height / 2 - 100, 60, 60])
                    pygame.draw.rect(self.screen, (0, 255, 0), [self.width / 2 - 70, self.height / 2 - 100, 60, 60], 5)
            if self.width / 2 + 10 <= mouse[0] <= self.width / 2 + 70 and self.height / 2 - 100 <= mouse[1] <= self.height / 2 - 40:
                if self.click2:
                    pygame.draw.rect(self.screen, (0, 255, 0), [self.width / 2 + 10, self.height / 2 - 100, 60, 60])
                else:
                    pygame.draw.rect(self.screen, (128, 255, 0), [self.width / 2 + 10, self.height / 2 - 100, 60, 60])
            else:
                if self.click2:
                    pygame.draw.rect(self.screen, (0, 255, 0), [self.width / 2 + 10, self.height / 2 - 100, 60, 60])
                else:
                    pygame.draw.rect(self.screen, (0, 0, 0), [self.width / 2 + 10, self.height / 2 - 100, 60, 60])
                    pygame.draw.rect(self.screen, (0, 255, 0), [self.width / 2 + 10, self.height / 2 - 100, 60, 60], 5)
            string_rendered = font.render("Start", 1, pygame.Color('white'))
            self.screen.blit(string_rendered, (self.width / 2 - 22, self.height / 2 - 7))
            string_rendered = font.render("1", 1, pygame.Color('white'))
            self.screen.blit(string_rendered, (self.width / 2 - 60, self.height / 2 - 90))
            string_rendered = font.render("2", 1, pygame.Color('white'))
            self.screen.blit(string_rendered, (self.width / 2 + 20, self.height / 2 - 90))
            pygame.display.flip()
            self.clock.tick(self.fps)

    def end_screen(self):
        fon = pygame.transform.scale(self.load_image('gameover.jpg'), (self.width, self.height))
        self.screen.blit(fon, (0, 0))
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.terminate()
            pygame.display.flip()
            self.clock.tick(self.fps)


if __name__ == '__main__':
    app = App()
    app.start_screen()