import os
import sys
import pygame
from pygame.draw import rect
import sqlite3
from pygame.math import Vector2

jump_start_time = 0
GRAVITY = Vector2(0, 0.86)
coins = 0
died = False  # умер или нет
win = False  # выиграл или нет
level = 1
attempt = 0
text = ''
levels = []


class Hero(pygame.sprite.Sprite):
    def __init__(self, app, image, pos, platforms, *groups):
        super().__init__(*groups)  # app.all_sprites
        self.image = app.load_image("player.jpg")
        self.rect = self.image.get_rect(center=pos)
        self.app = app
        self.jump_amount = 12
        self.vel = Vector2(0, 0)  # скорость
        self.rect = self.image.get_rect(center=pos)
        self.platforms = platforms  # все объекты(блоки, треугольники, монеты)
        self.is_jump = False  # прыгал или нет
        self.on_ground = False  # находится на земле или нет

    def collide(self, yvel, platforms):  # столкновения
        global coins, died, win
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
                        died = True
                if isinstance(p, Triangle):
                    died = True
                if isinstance(p, AnimatedSprite):
                    coins += 1
                    p.rect.x = -100
                    p.rect.y = -100
                if isinstance(p, End):
                    win = True
                keys = pygame.key.get_pressed()
                if isinstance(p, Gif) and (keys[pygame.K_UP] or keys[pygame.K_SPACE]):
                    app.screen.blit(app.load_image("sphere.gif"), p.rect.center)
                    self.vel.y = -(self.jump_amount + 2)

    def update(self):
        global win, died
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
        died_or_won(win, died)


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


class End(Draw):
    def __init__(self, img, pos, *groups):
        super().__init__(img, pos, *groups)


class Gif(Draw):
    def __init__(self, img, pos, *groups):
        super().__init__(img, pos, *groups)


class AnimatedSprite(pygame.sprite.Sprite):
    def __init__(self, app, sheet, columns, rows, x, y):
        super().__init__(app.elements)
        self.frames = []
        self.cut_sheet(sheet, columns, rows)
        self.cur_frame = 0
        self.image = self.frames[self.cur_frame]
        self.rect = self.rect.move(x, y)

    def cut_sheet(self, sheet, columns, rows):
        self.rect = pygame.Rect(0, 0, sheet.get_width() // columns,
                                sheet.get_height() // rows)
        for j in range(rows):
            for i in range(columns):
                frame_location = (self.rect.w * i, self.rect.h * j)
                self.frames.append(sheet.subsurface(pygame.Rect(
                    frame_location, self.rect.size)))

    def update(self):
        self.cur_frame = (self.cur_frame + 1) % len(self.frames)
        self.image = self.frames[self.cur_frame]


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


def died_or_won(w, d):
    global level, levels
    if d:
        app.end_screen()
    if w:
        if level not in levels:
            levels += [level]
        if len(levels) == 1:
            app.win_screen1()
        else:
            app.win_screen2()


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
        self.run = True
        self.coins = []
        self.pause = False

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

    def load_music(self, name):
        fullname = os.path.join('data', name)
        if not os.path.isfile(fullname):
            print(f"Файл с музыкой '{fullname}' не найден")
            sys.exit()
        pygame.mixer.music.load(fullname)

    def generate_level(self, level):
        x = 0
        y = 0
        for i in range(len(level)):
            for j in range(len(level[i])):
                if level[i][j] == '#':
                    Block(self.load_image('block.jpg'), (x, y), self.elements)
                if level[i][j] == '!':
                    Triangle(self.load_image('triangle.png'), (x, y), self.elements)
                if level[i][j] == 'G':
                    Gif(self.load_image('sphere.png'), (x, y), self.elements)
                if level[i][j] == 'C':
                    coin = AnimatedSprite(self, self.load_image("gold.png"), 8, 1, x, y)
                    self.coins.append(pygame.sprite.Group(coin))
                if level[i][j] == '@':
                    End(self.load_image('end.jpg'), (x, y), self.elements)
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

    def run_game(self, map, n=0):
        global coins, attempt
        if n == 1:
            pygame.mixer.music.pause()
        self.load_music('music1.mp3')
        pygame.mixer.music.play()
        fon = pygame.transform.scale(self.load_image('bakeground.jpg'), (self.width, self.height))
        self.screen.blit(fon, (0, 0))
        self.run = True
        attempt += 1
        coins = 0
        icon = self.load_image("player.jpg")
        pygame.display.set_icon(icon)
        self.hero = self.generate_level(self.load_level(map))
        font = pygame.font.Font(None, 40)
        self.pause = False
        while self.run:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.terminate()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    self.pause = not (self.pause)
                if event.type == pygame.KEYDOWN and event.key == pygame.K_1:
                    self.end_screen()
                    self.run = False
                elif event.type == pygame.KEYUP:
                    if event.key == pygame.K_3:
                        pygame.mixer.music.pause()
                    elif event.key == pygame.K_2:
                        pygame.mixer.music.unpause()
                        pygame.mixer.music.set_volume(0.5)
                    pygame.time.delay(20)
            keys = pygame.key.get_pressed()
            if self.pause:
                fon1 = pygame.transform.scale(self.load_image('img.png'), (self.width, self.height))
                self.screen.blit(fon1, (0, 0))
            else:
                self.hero.vel.x = 5  # скорость
                if keys[pygame.K_SPACE] or keys[pygame.K_UP]:
                    self.hero.is_jump = True
                self.all_sprites.update()
                self.Camera = self.hero.vel.x
                self.move_map()
                self.screen.blit(fon, (0, 0))
                if self.hero.is_jump:
                    self.angle -= 8.1712
                    Spin(self.screen, self.hero.image, self.hero.rect.center, (16, 16), self.angle)
                else:
                    self.all_sprites.draw(self.screen)
                self.elements.draw(self.screen)
                for group in self.coins:
                    group.update()
                    group.draw(self.screen)
                tries = font.render(f" Attempt {str(attempt)}", True, (255, 255, 255))
                for i in range(1, coins + 1):
                    self.screen.blit(self.load_image('coin.png'), (735 - i * 35, 50))
                self.screen.blit(tries, (600, 20))
            pygame.display.flip()
            self.clock.tick(60)

    def start_screen(self):
        global level, text
        intro_text = [" ГеометрияДэш", "",
                      "Выбери уровень"]
        fon = pygame.transform.scale(self.load_image('screen.jpg'), (self.width, self.height))
        self.screen.blit(fon, (0, 0))
        self.click1 = True
        self.click2 = False
        self.click3 = False
        self.start = False
        font = pygame.font.Font(None, 30)
        text_coord = 50
        # player = Hero(self, self.load_image('player.jpg'), (0, 550), self.elements, self.all_sprites)
        for line in intro_text:
            string_rendered = font.render(line, 0, pygame.Color('black'))
            intro_rect = string_rendered.get_rect()
            text_coord += 10
            intro_rect.top = text_coord
            intro_rect.x = self.width / 2 - 85
            text_coord += intro_rect.height
            self.screen.blit(string_rendered, intro_rect)
        string_rendered = font.render('Введите никнейм пользователя:', 0, pygame.Color('white'))
        intro_rect = string_rendered.get_rect()
        text_coord = 350
        intro_rect.top = text_coord
        intro_rect.x = 70
        text_coord += intro_rect.height
        self.screen.blit(string_rendered, intro_rect)
        self.base_font = pygame.font.Font(None, 35)
        self.input_rect = pygame.Rect(400, 345, 180, 35)
        self.color = pygame.Color((0, 255, 0))
        self.active = False
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.terminate()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.width / 2 - 70 <= mouse[0] <= self.width / 2 + 70 and self.height / 2 - 20 <= mouse[
                        1] <= self.height / 2 + 20:
                        self.con = sqlite3.connect("result.sqlite")
                        cur = self.con.cursor()
                        sqlite_insert_with_param = """INSERT INTO result (name, score1, poputki1, score2, poputki2)
                                                                    VALUES(?, ?, ?, ?, ?);"""
                        data_tuple = (text, 0, 0, 0, 0)
                        cur.execute(sqlite_insert_with_param, data_tuple)
                        self.con.commit()
                        self.con.close()
                        if self.click1:
                            level = 1
                            app.run_game('map1.txt')
                        else:
                            level = 2
                            app.run_game('map.txt')
                    if self.width / 2 - 70 <= mouse[0] <= self.width / 2 - 10 and self.height / 2 - 100 <= mouse[
                        1] <= self.height / 2 - 40:
                        self.click1 = True
                        self.click2 = False
                    if self.width / 2 + 10 <= mouse[0] <= self.width / 2 + 70 and self.height / 2 - 100 <= mouse[
                        1] <= self.height / 2 - 40:
                        self.click1 = False
                        self.click2 = True
                    if 400 <= mouse[0] <= 580 and 345 <= mouse[1] <= 380:
                        self.click3 = True
                    else:
                        self.click3 = False
                    if self.click3:
                        if self.input_rect.collidepoint(event.pos):
                            self.active = True
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_BACKSPACE and self.click3:
                        text = text[0:-1]
                    elif self.click3:
                        text += event.unicode
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
                if self.click1:
                    app.run_game('map1.txt')
                else:
                    app.run_game('map.txt')
            mouse = pygame.mouse.get_pos()
            if self.start or self.width / 2 - 70 <= mouse[0] <= self.width / 2 + 70 and self.height / 2 - 20 <= mouse[
                1] <= self.height / 2 + 20:
                pygame.draw.rect(self.screen, (128, 255, 0), [self.width / 2 - 70, self.height / 2 - 20, 140, 40])
            else:
                pygame.draw.rect(self.screen, (0, 255, 0), [self.width / 2 - 70, self.height / 2 - 20, 140, 40])
            if self.width / 2 - 70 <= mouse[0] <= self.width / 2 - 10 and self.height / 2 - 100 <= mouse[
                1] <= self.height / 2 - 40:
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
            if self.width / 2 + 10 <= mouse[0] <= self.width / 2 + 70 and self.height / 2 - 100 <= mouse[
                1] <= self.height / 2 - 40:
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
            if not self.click3:
                if 400 <= mouse[0] <= 580 and 345 <= mouse[1] <= 380:
                    self.active = True
                else:
                    self.active = False
            pygame.draw.line(self.screen, (0, 255, 0), [0, 550], [800, 550], 10)
            string_rendered = font.render("Start", 1, pygame.Color('white'))
            self.screen.blit(string_rendered, (self.width / 2 - 22, self.height / 2 - 7))
            string_rendered = font.render("1", 1, pygame.Color('white'))
            self.screen.blit(string_rendered, (self.width / 2 - 60, self.height / 2 - 90))
            string_rendered = font.render("2", 1, pygame.Color('white'))
            self.screen.blit(string_rendered, (self.width / 2 + 20, self.height / 2 - 90))
            if self.active:
                self.color = pygame.Color((128, 255, 0))
            else:
                self.color = pygame.Color((0, 255, 0))
            pygame.draw.rect(self.screen, self.color, self.input_rect)
            if len(text) > 7:
                text = text[0:-1]
            self.text1 = self.base_font.render(text, True, (255, 255, 255))
            self.screen.blit(self.text1, (self.input_rect.x + 5, self.input_rect.y + 5))
            self.input_rect.w = 180
            pygame.display.flip()
            self.clock.tick(self.fps)

    def update_sqlit(self):
        global level, attempt, text, coins
        self.con = sqlite3.connect("result.sqlite")
        cur = self.con.cursor()
        if level == 1:
            sqlite_insert_with_param = """UPDATE result SET  score1 = ? WHERE name = ?"""
            data_tuple = (coins, text)
            cur.execute(sqlite_insert_with_param, data_tuple)
            sqlite_insert_with_param = """UPDATE result SET  poputki1 = ? WHERE name = ?"""
            data_tuple = (attempt, text)
            cur.execute(sqlite_insert_with_param, data_tuple)
        else:
            sqlite_insert_with_param = """UPDATE result SET  score2 = ? WHERE name = ?"""
            data_tuple = (coins, text)
            cur.execute(sqlite_insert_with_param, data_tuple)
            sqlite_insert_with_param = """UPDATE result SET  poputki2 = ? WHERE name = ?"""
            data_tuple = (attempt, text)
            cur.execute(sqlite_insert_with_param, data_tuple)
        self.con.commit()
        self.con.close()

    def end_screen(self):
        global died
        self.update_sqlit()
        pygame.mixer.music.pause()
        self.load_music('Game_Over.mp3')
        pygame.mixer.music.play()
        fon = pygame.transform.scale(self.load_image('gameover.jpg'), (self.width, self.height))
        self.screen.blit(fon, (0, 0))
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.terminate()
                elif event.type == pygame.KEYUP:
                    if event.key == pygame.K_3:
                        pygame.mixer.music.pause()
                    elif event.key == pygame.K_2:
                        pygame.mixer.music.unpause()
                        pygame.mixer.music.set_volume(0.5)
                    pygame.time.delay(20)
            keys = pygame.key.get_pressed()
            if keys[pygame.K_SPACE]:
                died = False
                self.hero = None
                self.angle = 0
                self.all_sprites = pygame.sprite.Group()
                self.elements = pygame.sprite.Group()
                for i in range(len(self.coins)):
                    self.coins[i] = pygame.sprite.Group()
                self.Camera = 0
                self.run = True
                if level == 1:
                    app.run_game('map1.txt', 1)
                else:
                    app.run_game('map.txt', 1)
            pygame.display.flip()
            self.clock.tick(self.fps)

    def win_screen1(self):
        global coins, attempt, level, win, levels
        self.update_sqlit()
        self.hero = None
        self.angle = 0
        self.all_sprites = pygame.sprite.Group()
        self.elements = pygame.sprite.Group()
        self.Camera = 0
        self.run = True
        win = False
        pygame.mixer.music.pause()
        self.load_music('win.mp3')
        pygame.mixer.music.play()
        intro_text = [f"Вы набрали {coins} монет", "",
                      f"Вы потратили {attempt} попыток"]
        coins = 0
        attempt = 0
        fon = pygame.transform.scale(self.load_image('win.jpg'), (self.width, self.height))
        self.screen.blit(fon, (0, 0))
        font = pygame.font.Font(None, 30)
        text_coord = 50
        for line in intro_text:
            string_rendered = font.render(line, 0, pygame.Color('white'))
            intro_rect = string_rendered.get_rect()
            text_coord += 10
            intro_rect.top = text_coord
            intro_rect.x = self.width / 2 - len(line) * 6
            text_coord += intro_rect.height
            self.screen.blit(string_rendered, intro_rect)
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.terminate()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if 60 <= mouse[0] <= 410 and 440 <= mouse[1] <= 500:
                        app.start_screen()
                    if 480 <= mouse[0] <= 730 and 440 <= mouse[1] <= 500:
                        if levels[0] == 1:
                            level = 2
                            app.run_game('map.txt', 1)
                        else:
                            level = 1
                            app.run_game('map1.txt', 1)
                elif event.type == pygame.KEYUP:
                    if event.key == pygame.K_3:
                        pygame.mixer.music.pause()
                    elif event.key == pygame.K_2:
                        pygame.mixer.music.unpause()
                        pygame.mixer.music.set_volume(0.5)
                    pygame.time.delay(20)
            mouse = pygame.mouse.get_pos()
            pygame.draw.rect(self.screen, (128, 255, 0), [60, 440, 350, 60])
            if 480 <= mouse[0] <= 730 and 440 <= mouse[1] <= 500:
                pygame.draw.rect(self.screen, (128, 255, 0), [480, 440, 250, 60])
            else:
                pygame.draw.rect(self.screen, (0, 0, 0), [480, 440, 250, 60])
                pygame.draw.rect(self.screen, (0, 255, 0), [480, 440, 250, 60], 5)
            string_rendered = font.render("Вернуться на стартовую страницу", 1, pygame.Color('white'))
            self.screen.blit(string_rendered, (65, 460))
            string_rendered = font.render(f"Пройти уровень {3 - levels[0]}", 1, pygame.Color('white'))
            self.screen.blit(string_rendered, (485, 460))
            pygame.display.flip()
            self.clock.tick(self.fps)

    def win_screen2(self):
        global coins, attempt, level, win
        self.update_sqlit()
        self.hero = None
        self.angle = 0
        self.all_sprites = pygame.sprite.Group()
        self.elements = pygame.sprite.Group()
        self.Camera = 0
        self.run = True
        win = False
        pygame.mixer.music.pause()
        self.load_music('win.mp3')
        pygame.mixer.music.play()
        self.con = sqlite3.connect("result.sqlite")
        cur = self.con.cursor()
        result = cur.execute('SELECT score1, poputki1, score2, poputki2 FROM result WHERE name = ?',
                             (text,)).fetchall()
        score1, poputki1, score2, poputki2 = result[0][0], result[0][1], result[0][2], result[0][3]
        self.con.commit()
        self.con.close()
        intro_text = ["Вы прошли все уровни", "", f"Вы набрали в сумме {score1 + score2} монет", "",
                      f"Вы потрали в сумме {poputki1 + poputki2} попыток"]
        coins = 0
        attempt = 0
        fon = pygame.transform.scale(self.load_image('win.jpg'), (self.width, self.height))
        self.screen.blit(fon, (0, 0))
        font = pygame.font.Font(None, 30)
        text_coord = 50
        for line in intro_text:
            string_rendered = font.render(line, 0, pygame.Color('white'))
            intro_rect = string_rendered.get_rect()
            text_coord += 10
            intro_rect.top = text_coord
            intro_rect.x = self.width / 2 - len(line) * 6
            text_coord += intro_rect.height
            self.screen.blit(string_rendered, intro_rect)
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.terminate()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if 200 <= mouse[0] <= 550 and 440 <= mouse[1] <= 500:
                        app.start_screen()
                elif event.type == pygame.KEYUP:
                    if event.key == pygame.K_3:
                        pygame.mixer.music.pause()
                    elif event.key == pygame.K_2:
                        pygame.mixer.music.unpause()
                        pygame.mixer.music.set_volume(0.5)
                    pygame.time.delay(20)
            mouse = pygame.mouse.get_pos()
            pygame.draw.rect(self.screen, (128, 255, 0), [200, 440, 350, 60])
            string_rendered = font.render("Вернуться на стартовую страницу", 1, pygame.Color('white'))
            self.screen.blit(string_rendered, (205, 460))
            pygame.display.flip()
            self.clock.tick(self.fps)


if __name__ == '__main__':
    app = App()
    app.start_screen()
