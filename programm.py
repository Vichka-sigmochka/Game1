import os
import sys
from pygame.draw import rect
import random
import pygame


class Tile(pygame.sprite.Sprite):
    def __init__(self, app, tile_type, pos_x, pos_y):
        super().__init__(app.all_sprites)
        tile_images = {
            'wall': app.load_image('block.jpg'),
            'empty': app.load_image('empty.jpg'),
            'img': app.load_image('img.png')
        }
        player_image = app.load_image('player.png')
        tile_width = tile_height = 50
        self.image = tile_images[tile_type]
        self.rect = self.image.get_rect().move(
            tile_width * pos_x, tile_height * pos_y)


class Hero(pygame.sprite.Sprite):
    def __init__(self, app, pos):
        super().__init__(app.all_sprites, app.player_group)
        self.image = app.load_image("player.png")
        self.rect = self.image.get_rect()
        self.app = app
        # вычисляем маску для эффективного сравнения
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect().move(
            app.tile_width * pos[0] + 15, app.tile_height * pos[1] + 5)

    def update(self, pos):
        self.rect.x += pos[0]
        self.rect.y += pos[1]
        #if pygame.sprite.spritecollideany(self, self.app.tiles_group):
         #   self.rect.x -= pos[0]
          #  self.rect.y -= pos[1]

    def jump(self):
        for i in range(40):
            self.rect.y -= 2
        for i in range(40):
            self.rect.y += 2



class App:
    def __init__(self):
        pygame.init()
        self.width, self.height = 800, 600
        self.clock = pygame.time.Clock()
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption('ГеометрияДэш')
        self.hero = None
        self.all_sprites = pygame.sprite.Group()
        self.tile_width = self.tile_height = 50
        self.tiles_group = pygame.sprite.Group()
        self.player_group = pygame.sprite.Group()
        self.fps = 50
        self.camera = Camera()

    def terminate(self):
        pygame.quit()
        sys.exit()

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
        new_player, x, y = None, None, None
        for y in range(len(level)):
            for x in range(len(level[y])):
                if level[y][x] == '.':
                    Tile(self, 'empty', x, y)
                if level[y][x] == '#':
                    self.tiles_group.add(Tile(self, 'wall', x, y))
                if level[y][x] == '!':
                    Tile(self, 'empty', x, y)
                    self.tiles_group.add(Tile(self, 'img', x, y))
                elif level[y][x] == '@':
                    Tile(self, 'empty', x, y)
                    new_player = Hero(self, (x, y))
        # вернем игрока, а также размер поля в клетках
        return new_player, x, y

    def load_level(self, filename):
        filename = "data/" + filename
        with open(filename, 'r') as mapFile:
            level_map = [line.strip() for line in mapFile]
        max_width = max(map(len, level_map))
        return list(map(lambda x: x.ljust(max_width, '.'), level_map))

    def run_game(self):
        run = True
        self.hero, level_x, level_y = self.generate_level(self.load_level('map.txt'))
        while run:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.terminate()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_1:  # измениться при реализации столкновений
                     self.end_screen()
                     run = False
            keys = pygame.key.get_pressed()
            if keys[pygame.K_UP]:
                self.hero.jump()
            else:
                self.hero.update((3, 0))
            self.screen.fill(pygame.Color('blue'))
            self.all_sprites.draw(self.screen)
            self.player_group.draw(self.screen)
            pygame.display.flip()
            self.clock.tick(self.fps)
            self.camera.update(self.hero)
            for sprite in self.all_sprites:
                self.camera.apply(sprite)

    def start_screen(self):
        intro_text = [" ГеометрияДэш", "",
                      "Выбери уровень"]
        self.screen.fill((0, 0, 0))
        self.click1 = True
        self.click2 = False
        font = pygame.font.Font(None, 30)
        text_coord = 50
        for line in intro_text:
            string_rendered = font.render(line, 0, pygame.Color('white'))
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
                        return
                    if self.width / 2 - 70 <= mouse[0] <= self.width / 2 - 10 and self.height / 2 - 100 <= mouse[1] <= self.height / 2 - 40:
                        self.click1 = True
                        self.click2 = False
                    if self.width / 2 + 10 <= mouse[0] <= self.width / 2 + 70 and self.height / 2 - 100 <= mouse[1] <= self.height / 2 - 40:
                        self.click1 = False
                        self.click2 = True
            mouse = pygame.mouse.get_pos()
            if self.width / 2 - 70 <= mouse[0] <= self.width / 2 + 70 and self.height / 2 - 20 <= mouse[1] <= self.height / 2 + 20:
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

    def new_scren(self):
        self.screen.fill((255, 0, 255))


    def end_screen(self):
        fon = pygame.transform.scale(self.load_image('fon1.jpg'), (self.width, self.height))
        self.screen.blit(fon, (0, 0))
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.terminate()
            pygame.display.flip()
            self.clock.tick(self.fps)


class Camera:
    def __init__(self):
        self.dx = 0
        self.dy = 0

    def apply(self, obj):
        obj.rect.x += self.dx
        obj.rect.y += self.dy

    def update(self, target):
        self.dx = -(target.rect.x + target.rect.w // 2 - app.width // 2 + 210)
       # self.dy = -(target.rect.y + target.rect.h // 2 - app.height // 2 - 100)


if __name__ == '__main__':
    app = App()
    app.start_screen()
    app.run_game()