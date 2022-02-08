import pygame

import os
import random
import json
import copy
import math

pygame.font.init()
pygame.display.set_caption('My game')
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED_TRANSPARENT = (255, 0, 0, 128)
RED = (255, 0, 0)
FPS = 60


class Player:
    WIDTH, HEIGHT = 35, 35
    CLASSES = {
        'default': {'hp': 100, 'items': [], 'move_speed': 2}
    }
    IMMUNITY_FRAME_DURATION = 500
    WEAPON_COOLDOWN = 500

    def __init__(self, coord_x, coord_y, class_='default'):
        self.image = pygame.image.load("Assets/Maxim_verylowres.png").convert_alpha()
        self.kills = 0
        self.class_ = class_
        self.max_hp = self.CLASSES[class_]['hp']
        self.current_hp = self.max_hp
        self.items = self.CLASSES[class_]['items']
        self.move_speed = self.CLASSES[class_]['move_speed']
        self.rect = pygame.Rect(coord_x, coord_y, self.WIDTH, self.HEIGHT)

        self.weapons = [Weapon('sniper'), Weapon('flamethrower'), Weapon('default'), Weapon('spinner')]
        self.current_weapon = self.weapons[0]
        self.last_damage_taken_time = pygame.time.get_ticks()

    def input(self):
        keys_pressed = pygame.key.get_pressed()
        if keys_pressed[pygame.K_a] or keys_pressed[pygame.K_LEFT]:
            self.rect.x -= self.move_speed
        if keys_pressed[pygame.K_d] or keys_pressed[pygame.K_RIGHT]:
            self.rect.x += self.move_speed
        if keys_pressed[pygame.K_w] or keys_pressed[pygame.K_UP]:
            self.rect.y -= self.move_speed
        if keys_pressed[pygame.K_s] or keys_pressed[pygame.K_DOWN]:
            self.rect.y += self.move_speed
        if keys_pressed[pygame.K_SPACE]:
            self.current_weapon.shoot()

    def draw(self, window, cam_offset):
        window.blit(self.image, (self.rect.x + (Player.WIDTH - self.image.get_width()) // 2 - cam_offset[0],
                                 self.rect.y + (Player.HEIGHT - self.image.get_height()) // 2 - cam_offset[1]))
        self.current_weapon.draw(window, cam_offset)


class Weapon:
    DISTANCE_FROM_PLAYER = 15

    with open('Const/weapons.json') as fd:
        WEAPONS = json.load(fd)

    def __init__(self, name):
        if name in self.WEAPONS.keys():
            self.name = name
            self.damage = self.WEAPONS[name]['damage']
            self.cooldown = self.WEAPONS[name]['cooldown']
            self.pierce = self.WEAPONS[name]['pierce']
            self.chain = self.WEAPONS[name]['chain']
            self.bounce = self.WEAPONS[name]['bounce']
            self.bullet_speed = self.WEAPONS[name]['bullet_speed']
            self.bullet_duration = self.WEAPONS[name]['bullet_duration']
            self.bullet_spread = self.WEAPONS[name]['spread']
            self.last_shoot_time = pygame.time.get_ticks()
            self.image = pygame.image.load(self.WEAPONS[name]["weapon_img"]).convert_alpha()
            self.weapon_spin = self.WEAPONS[name].get("weapon_spin")
            self.bullet_spin = self.WEAPONS[name].get("bullet_spin")
            self.lifesteal = self.WEAPONS[name].get("lifesteal")

            if self.WEAPONS[name]["bullet_img"]:
                self.bullet_image = pygame.image.load(self.WEAPONS[name]["bullet_img"]).convert_alpha()
                self.bullet_rotate = self.WEAPONS[name]["bullet_rotate"]
            else:
                self.bullet_image = None
                self.bullet_rotate = False

            self.bullets = []
            self.current_image = self.image
            self.center_vector = pygame.Vector2(-100, -100)
            self.vector_to_mouse = pygame.Vector2(0, 0)
            self.rotate_angle = 0

    def shoot(self):
        spread_vector_left = self.vector_to_mouse.rotate_rad(self.bullet_spread)
        spread_vector_right = self.vector_to_mouse.rotate_rad(-self.bullet_spread)
        after_spread_vector = random.random() * spread_vector_left + random.random() * spread_vector_right
        after_spread_vector.normalize_ip()
        if pygame.time.get_ticks() - self.last_shoot_time >= self.cooldown:
            self.last_shoot_time = pygame.time.get_ticks()
            bullet = Bullet(self.center_vector.x, self.center_vector.y, after_spread_vector, speed=self.bullet_speed,
                            damage=self.damage, bounce=self.bounce, chain=self.chain, pierce=self.pierce, image=self.bullet_image,
                            duration=self.bullet_duration, rotate=self.bullet_rotate, spin=self.bullet_spin)
            self.bullets.append(bullet)

    def update_position(self, player_center_x, player_center_y, cam_offset):
        self.vector_to_mouse = pygame.Vector2(pygame.mouse.get_pos()[0] - player_center_x + cam_offset[0],
                                              pygame.mouse.get_pos()[1] - player_center_y + cam_offset[1])
        self.vector_to_mouse.normalize_ip()
        self.center_vector = pygame.Vector2(player_center_x, player_center_y) + self.vector_to_mouse * self.DISTANCE_FROM_PLAYER

        if self.vector_to_mouse.x > 0:
            self.current_image = pygame.transform.rotate(self.image, self.vector_to_mouse.angle_to(pygame.Vector2(1,0)))
        else:
            self.current_image = pygame.transform.flip(self.image, flip_x=True, flip_y=False)
            self.current_image = pygame.transform.rotate(self.current_image, self.vector_to_mouse.angle_to(pygame.Vector2(-1, 0)))
        if self.weapon_spin:
            self.current_image = pygame.transform.rotate(self.current_image, self.rotate_angle)
            self.rotate_angle = (self.rotate_angle + 3) % 360

    def draw(self, window, cam_offset):
        if self.weapon_spin:
            coord = (self.center_vector.x - self.current_image.get_width() / 2 - cam_offset[0],
                     self.center_vector.y - self.current_image.get_height() / 2 - cam_offset[1])
        else:
            coord = (self.center_vector.x - self.image.get_width() / 2 - cam_offset[0],
                     self.center_vector.y - self.image.get_height() / 2 - cam_offset[1])
        window.blit(self.current_image, coord)


class Bullet:
    WIDTH, HEIGHT = 7, 7
    DELETION_OFFSET = 500

    def __init__(self, coord_x, coord_y, vector, speed=3, color=BLACK, damage=5, is_allied=False, bounce=False,
                 pierce=False, chain=False, duration=2000, image=None, rotate=False, spin=False):
        self.vector = vector
        self.is_allied = is_allied
        self.color = color
        self.speed = speed
        self.bounce = bounce
        self.damage = damage
        self.pierce = pierce
        self.chain = chain
        self.duration = duration
        self.image = image
        self.rotate = rotate
        self.creation_time = pygame.time.get_ticks()
        self.spin = spin

        self.spin_angle = 0
        self.position_vector = pygame.Vector2(coord_x - self.WIDTH // 2, coord_y - self.HEIGHT // 2)
        self.rect = pygame.Rect(coord_x, coord_y, self.WIDTH, self.HEIGHT)

    def move(self, cam_offset):
        if self.bounce:
            surface = pygame.display.get_surface()
            if (self.rect.right - cam_offset[0] >= surface.get_width() and self.vector.x > 0) or (
                    self.rect.left - cam_offset[0] <= 0 and self.vector.x < 0):
                self.vector.x *= -1
            if (self.rect.bottom - cam_offset[1] >= Game.HEIGHT and self.vector.y > 0) or (
                    self.rect.top - cam_offset[1] <= 0 and self.vector.y < 0):
                self.vector.y *= -1
        self.position_vector.x += self.vector.x * self.speed
        self.position_vector.y += self.vector.y * self.speed
        self.rect.x = self.position_vector.x
        self.rect.y = self.position_vector.y

    def draw(self, window, cam_offset):
        if self.image is None:
            pygame.draw.rect(window, self.color, pygame.Rect(self.rect.x - cam_offset[0], self.rect.y - cam_offset[1], self.WIDTH, self.HEIGHT))
        else:

            if self.rotate:
                img = pygame.transform.rotate(self.image, self.vector.angle_to(pygame.Vector2(1,0)))
            elif self.spin:
                img = pygame.transform.rotate(self.image, self.spin_angle)
                self.spin_angle = (self.spin_angle + 10) % 360
            else:
                img = self.image

            img_rect = img.get_rect()
            img_rect.x = self.position_vector.x - img_rect.width // 2
            img_rect.y = self.position_vector.y - img_rect.height // 2
            window.blit(img, pygame.Rect(img_rect.x - cam_offset[0], img_rect.y - cam_offset[1],
                                                img_rect.width, img_rect.height))


class DamageNumber:
    DURATION = 500
    FONT = pygame.font.Font(None, 40)

    def __init__(self, text, coord_x, coord_y, color=WHITE):
        self.creation_time = pygame.time.get_ticks()
        self.image = self.FONT.render(str(text), True, color)
        self.rect = self.image.get_rect()
        self.rect.x = coord_x - self.image.get_width() // 2
        self.rect.y = coord_y - self.image.get_height() // 2

    def draw(self, cam_offset):
        surface = pygame.display.get_surface()
        surface.blit(self.image, (self.rect.x - cam_offset[0], self.rect.y - cam_offset[1]))


class Enemy:
    with open("Const/enemies.json") as fd:
        enemies = json.load(fd)
    print(enemies)
    with open("Const/bosses.json") as fd:
        bosses = json.load(fd)

    ANIMATION_FRAME_DURATION = 500
    WALK_ANIMATION_FRAMES = 4
    DAMAGE_TAKEN_ANIMATION_DURATION = 100
    IMMUNITY_FRAME_DURATION = 1000

    def __init__(self, coord_x, coord_y, width=50, height=50, type_="Goblin", stat_multiplier=1, is_boss=False):
        self.width = width
        self.height = height
        self.type_ = type_
        if is_boss:
            attributes = self.bosses[type_]
        else:
            attributes = self.enemies[type_]

        self.hp = attributes["hp"] * stat_multiplier
        self.move_speed = attributes['move_speed']
        self.damage = attributes['damage'] * stat_multiplier
        self.rect = pygame.Rect(coord_x, coord_y, self.width, self.height)
        self.position_vector = pygame.Vector2(coord_x, coord_y)
        self.immunity_timers = {}
        self.image = pygame.image.load(os.path.join('Assets', 'Enemy.png')).convert_alpha()
        self.walk_images = []
        img_path = attributes['image_path']
        self.variant = random.randint(0, 1)
        for img_id in range(self.WALK_ANIMATION_FRAMES):
            if not is_boss:
                img = pygame.image.load(f"{img_path}/Variant{self.variant}/{self.type_}_Walk_{img_id}.png").convert_alpha()
                self.walk_images.append(img)
            else:
                print(self.hp)
                img = pygame.image.load(f"{img_path}/{self.type_}_Walk_{img_id}.png").convert_alpha()
                self.walk_images.append(img)
        self.animation_id = 0
        self.last_animation_change = pygame.time.get_ticks()

        self.vector = pygame.math.Vector2()

        self.damage_taken = False
        img_copy = copy.copy(self.image)
        img_copy.fill(WHITE)
        self.damage_taken_image = img_copy
        self.last_damage_taken_time = pygame.time.get_ticks()

    def add_immunity(self, bullet):
        hit_time = pygame.time.get_ticks()
        self.immunity_timers.update({bullet: hit_time})

    def draw(self, window, cam_offset):
        # if self.damage_taken:
        #     window.blit(self.damage_taken_image, (self.rect.x + (Enemy.WIDTH - self.image.get_width()) // 2 - cam_offset[0],
        #                                           self.rect.y + (Enemy.HEIGHT - self.image.get_height()) // 2 - cam_offset[1]))
        # else:
        #     window.blit(self.image, (self.rect.x + (Enemy.WIDTH - self.image.get_width()) // 2 - cam_offset[0],
        #                              self.rect.y + (Enemy.HEIGHT - self.image.get_height()) // 2 - cam_offset[1]))
        if self.vector.x < 0:
            draw_img = pygame.transform.flip(self.walk_images[self.animation_id], flip_x=True, flip_y=False)
        else:
            draw_img = self.walk_images[self.animation_id]
        window.blit(draw_img, (self.rect.x - (draw_img.get_width() - self.width) // 2 - cam_offset[0],
                               self.rect.y - (draw_img.get_height() - self.height) // 2 - cam_offset[1]))
        if pygame.time.get_ticks() - self.last_animation_change > self.ANIMATION_FRAME_DURATION:
            self.animation_id = (self.animation_id + 1) % (len(self.walk_images) - 1)
            self.last_animation_change = pygame.time.get_ticks()


    def update(self, player):
        self.vector.x = player.rect.centerx - self.position_vector.x
        self.vector.y = player.rect.centery - self.position_vector.y
        self.vector.normalize_ip()
        self.vector *= self.move_speed

    def die(self):
        pass


class Game:
    WIDTH, HEIGHT = 1000, 600
    ENEMY_SPAWN_RATE = 500
    SPAWN_BOX_SIZE = 300
    SPAWN_BOX_OFFSET = 50
    TEXT_FONT = pygame.font.Font(None, 40)
    SPAWN_LIMIT = 200
    BULLET_DELETION_INTERVAL = 5000
    HP_BAR_WIDTH, HP_BAR_HEIGHT, HP_BAR_BORDER = 200, 50, 3
    YOU_DIED_FONT = pygame.font.Font(None, 100)
    GAME_DURATION = 600000
    WAVE_DURATION = 60000
    WAVE_ADDITIONAL_STATS = 0.3

    def __init__(self):
        self.camera_offset = pygame.math.Vector2()
        self.window = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        self.player = Player((self.WIDTH - Player.WIDTH) // 2, (self.HEIGHT - Player.HEIGHT) // 2)
        self.state = 'running'
        self.enemies = []
        self.last_spawn_time = pygame.time.get_ticks()
        self.last_bullet_deletion_time = pygame.time.get_ticks()
        self.game_over_surface = pygame.Surface((self.WIDTH, self.HEIGHT))
        self.game_over_surface.fill(BLACK)
        self.game_over_surface_alpha = 1
        self.game_over_surface_alpha_max = 200
        self.game_over_text_alpha = 1
        self.game_over_animation = False
        self.damage_numbers = []
        self.tiles = []
        tileset_image = pygame.image.load('Assets/Tile_grass.png')
        self.create_tileset(tileset_image)

        self.current_time = 0
        self.current_wave = 0

    def draw_hp_bar(self):
        hp_bar_border_rect = pygame.Rect(self.WIDTH - self.HP_BAR_WIDTH - 10, 10,
                                         self.HP_BAR_WIDTH, self.HP_BAR_HEIGHT)
        current_hp_percentage = self.player.current_hp / self.player.max_hp
        hp_bar_rect = pygame.Rect(self.WIDTH - self.HP_BAR_WIDTH - 10 + self.HP_BAR_BORDER, 10 + self.HP_BAR_BORDER,
                                  (self.HP_BAR_WIDTH - self.HP_BAR_BORDER * 2) * current_hp_percentage, self.HP_BAR_HEIGHT - self.HP_BAR_BORDER * 2)
        pygame.draw.rect(self.window, BLACK, rect=hp_bar_border_rect, width=self.HP_BAR_BORDER)
        pygame.draw.rect(self.window, RED, rect=hp_bar_rect)

    def draw(self):
        half_width = self.window.get_width() // 2
        half_height = self.window.get_height() // 2
        self.camera_offset = pygame.math.Vector2(self.player.rect.centerx - half_width, self.player.rect.centery - half_height)
        # self.window.fill(WHITE)
        self.draw_background()
        self.player.draw(self.window, self.camera_offset)

        def get_coord_y(obj):
            return obj.position_vector.y
        self.enemies.sort(key=get_coord_y)

        for enemy in self.enemies:
            enemy.draw(self.window, self.camera_offset)

        for weapon in self.player.weapons:
            for bullet in weapon.bullets:
                bullet.draw(self.window, self.camera_offset)

        for damage_num in self.damage_numbers:
            damage_num.draw(self.camera_offset)

        kills = self.TEXT_FONT.render(f"Kills: {self.player.kills}", True, BLACK)
        self.window.blit(kills, (10, 10))
        self.draw_hp_bar()
        self.draw_timer()

    def move_bullets(self):
        for weapon in self.player.weapons:
            for bullet in weapon.bullets:
                bullet.move(self.camera_offset)

    def move_enemies(self):
        for enemy_id, enemy in enumerate(self.enemies):
            if pygame.time.get_ticks() - enemy.last_damage_taken_time > Enemy.DAMAGE_TAKEN_ANIMATION_DURATION:
                enemy.damage_taken = False
            enemy.update(self.player)

            for second_enemy in self.enemies[enemy_id:]:
                if enemy.rect.colliderect(second_enemy.rect) and second_enemy != enemy:
                    first_vector = second_enemy.position_vector - enemy.position_vector
                    if first_vector.x != 0 and first_vector.y != 0:
                        first_vector.normalize_ip()
                    else:
                        first_vector *= 0.01
                    second_vector = -first_vector
                    enemy.position_vector += second_vector
                    second_enemy.position_vector += first_vector * 0.01

            enemy.position_vector.x += enemy.vector.x
            enemy.position_vector.y += enemy.vector.y
            enemy.rect.x = enemy.position_vector.x
            enemy.rect.y = enemy.position_vector.y

            vector_to_player = pygame.Vector2(self.player.rect.x - enemy.rect.x, self.player.rect.y - enemy.rect.y)
            if abs(vector_to_player.x) > self.WIDTH * 0.8 or abs(vector_to_player.y) > self.HEIGHT * 0.8:
                enemy.position_vector += vector_to_player * 2

    def spawn_boss(self, coord_x, coord_y):
        with open("Const/bosses.json") as fd:
            bosses = json.load(fd)
        boss_type = random.choice(list(bosses.keys()))
        stat_multiplier = 1 + self.WAVE_ADDITIONAL_STATS * self.current_wave / 2
        boss = Enemy(coord_x, coord_y, type_=boss_type, height=150, width=150, stat_multiplier=stat_multiplier, is_boss=True)
        self.enemies.append(boss)

    def create_enemy(self, coord_x, coord_y):
        if self.current_time // 60000 > self.current_wave:
            self.spawn_boss(coord_x, coord_y)
            self.current_wave += 1

        with open("Const/enemies.json") as fd:
            enemies = json.load(fd)
        enemy_type = random.choice(list(enemies.keys()))

        stat_multiplier = 1 + self.WAVE_ADDITIONAL_STATS * self.current_wave
        enemy = Enemy(coord_x, coord_y, type_=enemy_type, stat_multiplier=stat_multiplier)
        self.enemies.append(enemy)
        self.current_time = pygame.time.get_ticks()

    def spawn_enemies(self):
        if pygame.time.get_ticks() - self.last_spawn_time > self.ENEMY_SPAWN_RATE and len(self.enemies) <= self.SPAWN_LIMIT:
            self.last_spawn_time = pygame.time.get_ticks()
            spawn_sector = random.choice(['left', 'right', 'top', 'bottom'])
            if spawn_sector == 'top':
                spawn_coord = (random.randint(0, self.WIDTH) + self.camera_offset[0],
                               random.randint(-self.SPAWN_BOX_SIZE, -self.SPAWN_BOX_OFFSET) + self.camera_offset[1])
            elif spawn_sector == 'left':
                spawn_coord = (random.randint(-self.SPAWN_BOX_SIZE, -self.SPAWN_BOX_OFFSET) + self.camera_offset[0],
                               random.randint(0, self.HEIGHT) + self.camera_offset[1])
            elif spawn_sector == 'right':
                spawn_coord = (random.randint(self.WIDTH + self.SPAWN_BOX_OFFSET, self.WIDTH + self.SPAWN_BOX_SIZE) + self.camera_offset[0],
                               random.randint(0, self.HEIGHT) + + self.camera_offset[1])
            elif spawn_sector == 'bottom':
                spawn_coord = (random.randint(0, self.WIDTH) + self.camera_offset[0],
                               random.randint(self.HEIGHT + self.SPAWN_BOX_OFFSET, self.HEIGHT + self.SPAWN_BOX_SIZE) + self.camera_offset[1])
            self.create_enemy(spawn_coord[0], spawn_coord[1])

    def event_handler(self):
        if self.player.current_hp <= 0 or self.current_wave == 10:
            self.state = 'game_over'
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.state = 'quit'
            if self.state != 'game_over':
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_p:
                        self.state = 'paused'
                    else:
                        self.state = 'running'
            if event.type == pygame.MOUSEWHEEL:
                curr_weapon_idx = self.player.weapons.index(self.player.current_weapon)
                if event.y < 0:
                    if curr_weapon_idx < len(self.player.weapons) - 1:
                        self.player.current_weapon = self.player.weapons[curr_weapon_idx + 1]
                    else:
                        self.player.current_weapon = self.player.weapons[0]
                elif event.y > 0:
                    self.player.current_weapon = self.player.weapons[curr_weapon_idx - 1]

    def bullet_collision(self):
        for weapon in self.player.weapons:
            for bullet in weapon.bullets:
                for enemy in self.enemies:
                    if bullet.rect.colliderect(enemy.rect):
                        current_time = pygame.time.get_ticks()
                        if bullet not in enemy.immunity_timers.keys() or \
                                current_time - enemy.immunity_timers[bullet] > enemy.IMMUNITY_FRAME_DURATION:
                            self.damage_numbers.append(DamageNumber(bullet.damage, bullet.rect.x, bullet.rect.y))
                            if weapon.lifesteal:
                                heal = weapon.damage * weapon.lifesteal
                                if self.player.current_hp + heal <= self.player.max_hp:
                                    self.player.current_hp = self.player.current_hp + heal
                                    heal_number = DamageNumber(f"+{int(heal)}", self.player.rect.x, self.player.rect.y, color=RED)
                                    self.damage_numbers.append(heal_number)
                            enemy.damage_taken = True
                            enemy.last_damage_taken_time = pygame.time.get_ticks()
                            enemy.add_immunity(bullet)
                            enemy.hp -= bullet.damage
                            if enemy.hp <= 0:
                                enemy.die()
                                self.player.kills += 1
                                self.enemies.remove(enemy)
                            if bullet.chain:
                                bullet.vector = -bullet.vector
                            elif not bullet.pierce:
                                if bullet in weapon.bullets:
                                    weapon.bullets.remove(bullet)

    def update_damage_numbers(self):
        for dmg_number in self.damage_numbers:
            dmg_number.rect.y -= 1
            if pygame.time.get_ticks() - dmg_number.creation_time > DamageNumber.DURATION:
                self.damage_numbers.remove(dmg_number)

    def player_collision(self):
        if pygame.time.get_ticks() - self.player.last_damage_taken_time > Player.IMMUNITY_FRAME_DURATION:
            self.player.last_damage_taken_time = pygame.time.get_ticks()
            for enemy in self.enemies:
                if self.player.rect.colliderect(enemy.rect):
                    self.player.current_hp -= enemy.damage

    def update_bullets(self):
        if self.last_bullet_deletion_time >= self.BULLET_DELETION_INTERVAL:
            for weapon in self.player.weapons:
                for bullet in weapon.bullets:
                    if not bullet.bounce:
                        if bullet.rect.left + bullet.DELETION_OFFSET - self.camera_offset[0] < 0 or \
                                bullet.rect.right - bullet.DELETION_OFFSET - self.camera_offset[0] > Game.WIDTH or \
                                bullet.rect.top + bullet.DELETION_OFFSET - self.camera_offset[1] < 0 or \
                                bullet.rect.bottom - bullet.DELETION_OFFSET - self.camera_offset[1] > Game.HEIGHT:
                            if bullet in weapon.bullets:
                                weapon.bullets.remove(bullet)
        for weapon in self.player.weapons:
            for bullet in weapon.bullets:
                if pygame.time.get_ticks() - bullet.creation_time > bullet.duration:
                    if bullet in weapon.bullets:
                        weapon.bullets.remove(bullet)

    def draw_game_over(self):
        self.draw()
        if self.game_over_surface_alpha <= self.game_over_surface_alpha_max:
            self.game_over_surface.set_alpha(self.game_over_surface_alpha)
            self.game_over_surface_alpha += 1
        self.window.blit(self.game_over_surface, (0, 0))
        you_died_text = self.YOU_DIED_FONT.render('YOU DIED', True, RED)
        if self.game_over_text_alpha < 255:
            self.game_over_animation = True
            you_died_text.set_alpha(self.game_over_text_alpha)
            self.game_over_text_alpha += 1
        else:
            self.game_over_animation = False
        self.window.blit(you_died_text, ((self.WIDTH - you_died_text.get_width()) / 2, (self.HEIGHT - you_died_text.get_height()) / 2))

    def create_tileset(self, image):
        self.tiles = []
        img_height = image.get_height()
        img_width = image.get_width()
        full_width = self.WIDTH + 2 * img_width
        full_height = self.HEIGHT + 2 * img_height

        tile_x = 0
        tile_y = 0
        print(full_width, full_height)

        while tile_x <= full_width:
            while tile_y <= full_height:
                print(tile_x, tile_y)
                tile = Tile(tile_x, tile_y, image)
                self.tiles.append(tile)
                tile_y += img_height
            tile_y = 0
            tile_x += img_width
        print([tile.rect for tile in self.tiles])

    def draw_background(self):
        for tile in self.tiles:
            tile_offset = pygame.math.Vector2(self.camera_offset.x % tile.rect.width, self.camera_offset.y % tile.rect.height)
            self.window.blit(tile.image, (tile.rect.x - tile_offset.x, tile.rect.y - tile_offset.y))

    def draw_timer(self):
        self.current_time = pygame.time.get_ticks()
        minutes = (self.current_time // 1000) // 60
        seconds = (self.current_time // 1000) % 60
        if minutes == 0:
            minutes = '00'
        if seconds < 10:
            seconds = f"0{seconds}"

        time_text = self.TEXT_FONT.render(f"{minutes}:{seconds}", True, BLACK)
        self.window.blit(time_text, (self.WIDTH // 2 - time_text.get_width() // 2, 10))


class Tile:
    def __init__(self, coord_x, coord_y, image):
        self.rect = pygame.Rect(coord_x, coord_y, image.get_width(), image.get_height())
        self.image = image


def main():
    clock = pygame.time.Clock()
    game = Game()
    while game.state != 'quit':
        clock.tick(FPS)
        game.event_handler()
        if game.state == 'running':
            game.player.current_weapon.update_position(game.player.rect.centerx, game.player.rect.centery, game.camera_offset)
            game.player.input()
            game.move_bullets()
            game.move_enemies()
            game.spawn_enemies()
            game.bullet_collision()
            game.player_collision()
            game.update_bullets()
            game.update_damage_numbers()
            game.draw()
        elif game.state == 'game_over':
            game.draw_game_over()
            if not game.game_over_animation:
                keys_pressed = pygame.key.get_pressed()
                mouse_buttons_pressed = pygame.mouse.get_pressed()
                if keys_pressed or mouse_buttons_pressed:
                    game.state = 'main_menu'
        elif game.state == 'main_menu':
            pass
        pygame.display.update()
        # print(game.state)
    pygame.quit()


main()
