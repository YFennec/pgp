import pygame
import os
import sys
import json
import random

file = open('data/maps/progress.json')
try:
    level = int(json.load(file)['level'])
except Exception:
    file.close()
    with open('data/maps/progress.json', 'w') as file:
        json.dump({'level': 1}, file)
        level = 1

pygame.init()
screen_size = (1050, 800)
screen = pygame.display.set_mode(screen_size)
FPS = 50


class SpriteGroup(pygame.sprite.Group):
    def __init__(self):
        super().__init__()

    def get_event(self, event):
        for sprite in self:
            sprite.get_event(event)


clock_counter = 0

sprite_groups = [
        tile_group := SpriteGroup(),
        end_portal := SpriteGroup(),
        portal := SpriteGroup(),
        active_walls := SpriteGroup(),
        buttons := SpriteGroup(),
        hero_group := SpriteGroup()
    ]
particles_groups = [
        portal_particles := SpriteGroup(),
        player_particles := SpriteGroup()
    ]
portal_list = []
buttons_list = []
active_walls_list = []


def groups_load():
    global sprite_groups, tile_group, hero_group, end_portal, portal, active_walls, buttons
    global portal_list, buttons_list, active_walls_list
    global particles_groups, portal_particles, player_particles
    sprite_groups = [
        tile_group := SpriteGroup(),
        end_portal := SpriteGroup(),
        portal := SpriteGroup(),
        active_walls := SpriteGroup(),
        buttons := SpriteGroup(),
        hero_group := SpriteGroup()
    ]
    particles_groups = [
        portal_particles := SpriteGroup(),
        player_particles := SpriteGroup()
    ]
    portal_list = []
    buttons_list = []
    active_walls_list = []


def load_image(name, color_key=None):
    fullname = os.path.join('data', name)
    try:
        image = pygame.image.load(fullname)
    except pygame.error as message:
        print('Не удаётся загрузить:', name)
        raise SystemExit(message)
    image = image.convert_alpha()
    if color_key is not None:
        if color_key == -1:
            color_key = image.get_at((0, 0))
        image.set_colorkey(color_key)
    return image


def next_level():
    global hero, level, max_x, max_y
    global level_map, level
    with open('data/maps/progress.json', 'w') as file:
        level += 1
        json.dump({'level': level}, file)
    groups_load()
    try:
        tile_images['empty'] = load_image(f'sprites/free{level}.png')
        level_map = load_level(f"maps/map{level}.map")
        hero, max_x, max_y = generate_level(level_map)
    except Exception:
        level -= 1
        with open('data/maps/progress.json', 'w') as file:
            json.dump({"level": level}, file)
        print('not found')
        sys.exit()


tile_images = {
    'wall': load_image('sprites/wall.png'),
    'empty': load_image(f'sprites/free{level}.png')
}

tile_width = tile_height = 50


class ScreenFrame(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.rect = (0, 0, 500, 500)


class Sprite(pygame.sprite.Sprite):
    def __init__(self, group):
        super().__init__(group)
        self.rect = None

    def get_event(self, event):
        pass


class Tile(Sprite):
    def __init__(self, tile_type, pos_x, pos_y):
        super().__init__(tile_group)
        self.image = tile_images[tile_type]
        self.rect = self.image.get_rect().move(
            tile_width * pos_x, tile_height * pos_y)


class AnimatedSpriteHero(Sprite):
    def __init__(self, sheet, columns, rows, pos_x, pos_y, reverse=False):
        super().__init__(hero_group)
        self.frames = []
        self.cut_sheet(sheet, columns, rows)
        self.cur_frame = 0
        self.image = self.frames[self.cur_frame]
        self.rect = self.rect.move(tile_width * pos_x + 5, tile_height * pos_y + 5)
        self.pos = (pos_x, pos_y)
        self.reverse = reverse

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

    def move(self, x, y):
        self.pos = (x, y)
        self.rect = self.image.get_rect().move(
            tile_width * self.pos[0] + 5, tile_height * self.pos[1] + 5)


class AnimatedSpriteEndPortal(Sprite):
    def __init__(self, sheet, columns, rows, pos_x, pos_y):
        super().__init__(end_portal)
        self.frames = []
        self.cut_sheet(sheet, columns, rows)
        self.cur_frame = 0
        self.image = self.frames[self.cur_frame]
        self.rect = self.rect.move(tile_width * pos_x, tile_height * pos_y)

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


class AnimatedSpritePortal(pygame.sprite.Sprite):
    def __init__(self, sheet, columns, rows, pos_x, pos_y, portal_index):
        super().__init__(portal)
        self.index = portal_index
        self.frames = []
        self.cut_sheet(sheet, columns, rows)
        self.cur_frame = 0
        self.image = self.frames[self.cur_frame]
        self.rect = self.rect.move(tile_width * pos_x, tile_height * pos_y)
        self.pos = (pos_x, pos_y)

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


class Button(Sprite):
    def __init__(self, image, pos_x, pos_y):
        super().__init__(buttons)
        self.image = image
        self.rect = self.image.get_rect().move(
            tile_width * pos_x, tile_height * pos_y)
        self.pos = (pos_x, pos_y)

    def update(self):
        hero_poses = set([x.pos for x in hero_group])
        buttons_poses = set([x[0] for x in buttons_list])
        pos_set = hero_poses & buttons_poses
        if pos_set and all(map(lambda x: x[1] == 0, buttons_list)):
            buttons_list[0][1] = 1
        elif not pos_set and any(map(lambda x: x[1] == 1, buttons_list)):
            for ind, butt in enumerate(buttons_list):
                buttons_list[ind][1] = 0


class ActiveWall(Sprite):
    def __init__(self, image, pos_x, pos_y):
        super().__init__(active_walls)
        self.image = image
        self.rect = self.image.get_rect().move(
            tile_width * pos_x, tile_height * pos_y)
        self.active = 0
        self.pos = (pos_x, pos_y)

    def update(self):
        global active_walls
        if any(map(lambda x: x[1] == 1, buttons_list)) and self.active == 0:
            for x, y in active_walls_list:
                self.image = load_image(f'sprites/free{level}.png')
                create_player_particles(self.pos, 'wall')
                level_map[y][x] = "."
                self.active = 1
        elif all(map(lambda x: x[1] == 0, buttons_list)) and self.active == 1:
            for x, y in active_walls_list:
                self.image = load_image('sprites/active_wall.png')
                create_portal_particles(self.pos)
                level_map[y][x] = "/"
                self.active = 0


class PortalParticle(Sprite):
    particles_images = []
    for x in range(1, 8):
        particles_images.append(load_image(f"sprites/particles/portal particles/particle{x}.png"))
    particles = []
    for x in range(7):
        scale = random.choice(range(3, 7))
        particles.append(pygame.transform.scale(particles_images[x], (scale, scale)))

    def __init__(self, pos, dx, dy):
        super().__init__(portal_particles)
        self.image = random.choice(self.particles)
        self.rect = self.image.get_rect()
        self.velocity = [dx, dy]
        self.rect.x, self.rect.y = pos
        self.updates = 0

    def update(self):
        self.updates += 1
        self.rect.x += self.velocity[0]
        self.rect.y += self.velocity[1]
        if self.updates >= 7:
            self.kill()


def create_portal_particles(position):
    x, y = position
    pos = [x * tile_width + 24, y * tile_width + 24]
    particle_count = random.randint(1, 3)
    numbers = range(-5, 5)
    for _ in range(particle_count):
        portal_particles.add(PortalParticle(pos, random.choice(numbers), random.choice(numbers)))


class PlayerParticle(Sprite):
    particles_image = load_image(f"sprites/particles/player particles/player particle.png")
    particles = []
    for scale in range(3, 7):
        particles.append(pygame.transform.scale(particles_image, (scale, scale)))

    def __init__(self, pos, dx, dy):
        super().__init__(portal_particles)
        self.image = random.choice(self.particles)
        self.rect = self.image.get_rect()
        self.velocity = [dx, dy]
        self.rect.x, self.rect.y = pos
        self.updates = 0

    def update(self):
        self.updates += 1
        self.rect.x += round(self.velocity[0] * 0.5)
        self.rect.y += round(self.velocity[1] * 0.5)
        if self.updates >= 12:
            self.kill()


def create_player_particles(position, movement):
    x, y = position
    if movement == 'up':
        pos = [x * tile_width + 24, y * tile_width]
        numbers_x = range(-5, 5)
        numbers_y = range(0, 13)

    elif movement == 'down':
        pos = [x * tile_width + 24, (y + 1) * tile_width]
        numbers_x = range(-5, 5)
        numbers_y = range(-13, 0)

    elif movement == 'left':
        pos = [x * tile_width, y * tile_width + 24]
        numbers_x = range(0, 13)
        numbers_y = range(-5, 5)

    elif movement == 'right':
        pos = [(x + 1) * tile_width, y * tile_width + 24]
        numbers_x = range(-13, 0)
        numbers_y = range(-5, 5)

    else:
        pos = [x * tile_width + 24, y * tile_width + 24]
        numbers_x = range(-5, 5)
        numbers_y = range(-5, 5)

    particle_count = random.randint(3, 7)
    for _ in range(particle_count):
        player_particles.add(PlayerParticle(pos, random.choice(numbers_x), random.choice(numbers_y)))


player = None
running = True
clock = pygame.time.Clock()
groups_load()


def start_screen():
    clock_counter = 0
    fon = pygame.transform.scale(load_image('fon/fon.jpg'), screen_size)
    screen.blit(fon, (0, 0))
    fon_sprites = []
    for sprite in '7_1 7_2 7_3 7_4 7_5 7_6 7_7'.split()[::-1]:
        fon_sprites.append(load_image(f'fon/{sprite}.png'))
    x, y = 300, 270
    for sprite in fon_sprites:
        sprite = pygame.transform.scale(sprite, (136, 258))
        screen.blit(sprite, (x, y))
        x -= 35
        y -= 20
    i = 1
    i1 = 1
    while True:
        screen2 = pygame.Surface(screen.get_size())
        screen2.blit(fon, (0, 0))
        x, y = 300, 270
        dx, dy = 1, 0.3
        for sprite in fon_sprites:
            sprite = pygame.transform.scale(sprite, (136, 258))
            screen2.blit(sprite, (x, y))
            x -= int(dx * i)
            y -= int(dy * i)
        screen.blit(screen2, (0, 0))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN or \
                    event.type == pygame.MOUSEBUTTONDOWN:
                return
        pygame.display.flip()
        clock.tick(FPS)
        clock_counter += 1
        if clock_counter % 3 == 0:
            if i == 15:
                i1 = -1
            elif i == 1:
                i1 = 1
            i += i1


def load_level(filename):
    filename = "data/" + filename
    with open(filename, 'r') as mapFile:
        level_map = [line.strip() for line in mapFile]
    max_width = max(map(len, level_map))
    return list(map(lambda x: list(x.ljust(max_width, '.')), level_map))


def generate_level(level):
    new_player, x, y = None, None, None
    global portal_list
    for y in range(len(level)):
        for x in range(len(level[y])):
            if level[y][x] == '.':
                Tile('empty', x, y)

            elif level[y][x] == '#':
                Tile('wall', x, y)

            elif level[y][x] == '@':
                Tile('empty', x, y)
                hero_group.add(AnimatedSpriteHero(load_image("sprites/player_animate.png"), 7, 2, x, y))
                level_map[y][x] = "."
            elif level[y][x] == '&':
                Tile('empty', x, y)
                hero_group.add(AnimatedSpriteHero(load_image("sprites/player_animate.png"), 7, 2, x, y, reverse=True))
                level_map[y][x] = "."

            elif level[y][x] == '%':
                end_portal.add(AnimatedSpriteEndPortal(load_image('sprites/end_portal_animate.png'), 6, 2, x, y))
                level_map[y][x] = "%"
                portal_list.append((10, (x, y)))

            elif level[y][x] in '0123456789':
                portal.add(AnimatedSpritePortal(load_image('sprites/portal_animate.png'), 4, 2, x, y, int(level[y][x])))
                level_map[y][x] = level[y][x]
                portal_list = [(x.index, x.pos) for x in sorted(portal, key=lambda x: x.index)]

            elif level[y][x] == '*':
                buttons.add(Button(load_image('sprites/button.png'), x, y))
                level_map[y][x] = "*"
                buttons_list.append([(x, y), 0])
            elif level[y][x] == '/':
                active_walls.add(ActiveWall(load_image('sprites/active_wall.png'), x, y))
                level_map[y][x] = "/"
                active_walls_list.append((x, y))

    return new_player, x, y


def move(hero, movement):
    x, y = hero.pos
    if hero.reverse:
        if movement == "up":
            movement = 'down'
        elif movement == 'down':
            movement = 'up'
        elif movement == 'right':
            movement = 'left'
        else:
            movement = 'right'

    if movement == "up":
        if y > 0 and level_map[y - 1][x] == ".":
            hero.move(x, y - 1)
            create_player_particles((x, y), movement)

        elif y > 0 - 1 and level_map[y - 1][x] == "%":
            hero.move(x, y - 1)
            create_player_particles((x, y), movement)
            next_level()

        elif y > 0 - 1 and level_map[y - 1][x] in "0123456789":
            portal_index = int(level_map[y - 1][x])
            if portal_index % 2 == 0:
                x, y = portal_list[portal_index + 1][1]
            else:
                x, y = portal_list[portal_index - 1][1]
            if level_map[y - 1][x] in ".*":
                hero.move(x, y - 1)
                create_player_particles((x, y), movement)

        elif y > 0 - 1 and level_map[y - 1][x] == "*":
            hero.move(x, y - 1)
            create_player_particles((x, y), movement)

    elif movement == "down":
        if y < max_y - 1 and level_map[y + 1][x] == ".":
            hero.move(x, y + 1)
            create_player_particles((x, y), movement)

        elif y < max_y - 1 and level_map[y + 1][x] == "%":
            hero.move(x, y + 1)
            create_player_particles((x, y), movement)
            next_level()

        elif y < max_y - 1 and level_map[y + 1][x] in "0123456789":
            portal_index = int(level_map[y + 1][x])
            if portal_index % 2 == 0:
                x, y = portal_list[portal_index + 1][1]
            else:
                x, y = portal_list[portal_index - 1][1]
            if level_map[y + 1][x] in ".*":
                hero.move(x, y + 1)
                create_player_particles((x, y), movement)

        elif y < max_y - 1 and level_map[y + 1][x] == "*":
            hero.move(x, y + 1)
            create_player_particles((x, y), movement)

    elif movement == "left":
        if x > 0 and level_map[y][x - 1] == ".":
            hero.move(x - 1, y)
            create_player_particles((x, y), movement)

        elif x > 0 - 1 and level_map[y][x - 1] == "%":
            hero.move(x - 1, y)
            create_player_particles((x, y), movement)
            next_level()

        elif x > 0 - 1 and level_map[y][x - 1] in "0123456789":
            portal_index = int(level_map[y][x - 1])
            if portal_index % 2 == 0:
                x, y = portal_list[portal_index + 1][1]
            else:
                x, y = portal_list[portal_index - 1][1]
            if level_map[y][x - 1] in ".*":
                hero.move(x - 1, y)
                create_player_particles((x, y), movement)

        elif x > 0 and level_map[y][x - 1] == "*":
            hero.move(x - 1, y)
            create_player_particles((x, y), movement)

    elif movement == "right":
        if x < max_x - 1 and level_map[y][x + 1] == ".":
            hero.move(x + 1, y)
            create_player_particles((x, y), movement)

        elif x < max_x - 1 and level_map[y][x + 1] == "%":
            hero.move(x + 1, y)
            create_player_particles((x, y), movement)
            next_level()

        elif x < max_x - 1 and level_map[y][x + 1] in "0123456789":
            portal_index = int(level_map[y][x + 1])
            if portal_index % 2 == 0:
                x, y = portal_list[portal_index + 1][1]
            else:
                x, y = portal_list[portal_index - 1][1]
            if level_map[y][x + 1] in ".*":
                hero.move(x + 1, y)
                create_player_particles((x, y), movement)

        elif x < max_x - 1 and level_map[y][x + 1] == "*":
            hero.move(x + 1, y)
            create_player_particles((x, y), movement)


start_screen()
level_map = load_level(f"maps/map{level}.map")
hero, max_x, max_y = generate_level(level_map)
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                for hero in hero_group:
                    move(hero, "up")
            elif event.key == pygame.K_DOWN:
                for hero in hero_group:
                    move(hero, "down")
            elif event.key == pygame.K_LEFT:
                for hero in hero_group:
                    move(hero, "left")
            elif event.key == pygame.K_RIGHT:
                for hero in hero_group:
                    move(hero, "right")
            elif event.key == pygame.K_ESCAPE:
                level -= 1
                next_level()
    screen.fill(pygame.Color("black"))
    for group in sprite_groups:
        group.draw(screen)
    for group in particles_groups:
        group.draw(screen)
    if clock_counter % 5 == 0:
        active_walls.update()
        hero_group.update()
    if clock_counter % 3 == 0:
        buttons.update()
        end_portal.update()
        portal.update()
    if clock_counter % 2 == 0:
        for portal1 in portal_list:
            create_portal_particles(portal1[1])
        portal_particles.update()
    player_particles.update()
    clock.tick(FPS)
    pygame.display.flip()
    clock_counter += 1
pygame.quit()
