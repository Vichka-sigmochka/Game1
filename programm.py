import os
import sys
import math
import pygame

player_start_x = 100
player_start_y = 300
player_x = player_start_x
player_y = player_start_y
initial_speed = 400
jump_angle = 80
gravity = 1000
jump_start_time = 0
is_jumping = False


class Tile(pygame.sprite.Sprite):
    def __init__(self, app, tile_type, pos_x, pos_y):
        super().__init__(app.all_sprites)
        tile_images = {
            'wall': app.load_image('block.jpg'),
            'empty': app.load_image('empty.jpg')
        }
        player_image = app.load_image('player.jpg')
        tile_width = tile_height = 50
        self.image = tile_images[tile_type]
        self.rect = self.image.get_rect().move(
            tile_width * pos_x, tile_height * pos_y)


class Hero(pygame.sprite.Sprite):
    def __init__(self, app, pos):
        global player_start_x, player_start_y
        super().__init__(app.all_sprites, app.player_group)
        self.image = app.load_image("player.jpg")
        self.rect = self.image.get_rect()
        self.app = app
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect().move(
            app.tile_width * pos[0] + 15, app.tile_height * pos[1] + 5)
        player_start_x = self.rect.x
        player_start_y = self.rect.y

    def angled_jump(self, start_x, start_y, initial_speed, jump_angle, gravity, current_time):
        jump_angle_rad = math.radians(jump_angle)
        initial_velocity_x = initial_speed * math.cos(jump_angle_rad)
        initial_velocity_y = -initial_speed * math.sin(jump_angle_rad)
        velocity_y = initial_velocity_y + gravity * current_time
        velocity_x = initial_velocity_x
        x = start_x + velocity_x * current_time
        y = start_y + velocity_y * current_time - 0.5 * gravity * current_time ** 2
        return x, y

    def update_jump(self, pos):
        self.rect.x = pos[0]
        self.rect.y = pos[1]

    def update(self, pos):
        self.rect.x += pos[0]


class App:
    def __init__(self):
        pygame.init()
        self.width, self.height = 700, 400
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
                #if level[y][x] == '.':
                 #   Tile(self, 'empty', x, y)
                if level[y][x] == '#':
                    self.tiles_group.add(Tile(self, 'wall', x, y))
                elif level[y][x] == '@':
                    Tile(self, 'empty', x, y)
                    new_player = Hero(self, (x, y))
        return new_player, x, y

    def load_level(self, filename):
        filename = "data/" + filename
        with open(filename, 'r') as mapFile:
            level_map = [line.strip() for line in mapFile]
        max_width = max(map(len, level_map))
        return list(map(lambda x: x.ljust(max_width, '.'), level_map))

    def run_game(self):
        global player_start_x, player_start_y, player_x, player_y, initial_speed, jump_angle, gravity, jump_start_time, is_jumping
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
            if keys[pygame.K_UP] and not is_jumping:
                is_jumping = True
                jump_start_time = pygame.time.get_ticks() / 1000
            if is_jumping:
                current_time = (pygame.time.get_ticks() / 1000) - jump_start_time
                player_x, player_y = self.hero.angled_jump(player_start_x, player_start_y, initial_speed, jump_angle, gravity,
                                                 current_time)
                if player_y > player_start_y:  # Если игрок вернулся на землю
                    is_jumping = False
                    player_x = player_start_x
                    player_y = player_start_y
                self.hero.update_jump((player_x, player_y))
            else:
                self.hero.update((5, 0))
            self.screen.fill(pygame.Color('blue'))
            self.all_sprites.draw(self.screen)
            self.player_group.draw(self.screen)
            pygame.display.flip()
            self.clock.tick(10)
            self.camera.update(self.hero)
            for sprite in self.all_sprites:
                self.camera.apply(sprite)

    def start_screen(self):
        intro_text = ["Это ГеометрияДэш", "",
                      "Вы находитесь на 1 уровне"]
        fon = pygame.transform.scale(self.load_image('screen.jpg'), (self.width, self.height))
        self.screen.blit(fon, (0, 0))
        font = pygame.font.Font(None, 30)
        text_coord = 50
        for line in intro_text:
            string_rendered = font.render(line, 1, pygame.Color('white'))
            intro_rect = string_rendered.get_rect()
            text_coord += 10
            intro_rect.top = text_coord
            intro_rect.x = 10
            text_coord += intro_rect.height
            self.screen.blit(string_rendered, intro_rect)
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.terminate()
                elif event.type == pygame.KEYDOWN or \
                        event.type == pygame.MOUSEBUTTONDOWN:
                    return  # начинаем игру
            pygame.display.flip()
            self.clock.tick(self.fps)

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