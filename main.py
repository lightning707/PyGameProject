import pygame

import os
import random
import json

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
            # if self.rect.x > 0:
            self.rect.x -= self.move_speed
        if keys_pressed[pygame.K_d] or keys_pressed[pygame.K_RIGHT]:
            # if self.rect.x + self.WIDTH < Game.WIDTH:
            self.rect.x += self.move_speed
        if keys_pressed[pygame.K_w] or keys_pressed[pygame.K_UP]:
            # if self.rect.y > 0:
            self.rect.y -= self.move_speed
        if keys_pressed[pygame.K_s] or keys_pressed[pygame.K_DOWN]:
            # if self.rect.y + self.HEIGHT < Game.HEIGHT:
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
            if "weapon_spin" in self.WEAPONS[name].keys():
                self.weapon_spin = self.WEAPONS[name]["weapon_spin"]
            else:
                self.weapon_spin = False
            if "bullet_spin" in self.WEAPONS[name].keys():
                self.bullet_spin = self.WEAPONS[name]["bullet_spin"]
            else:
                self.bullet_spin = False
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
        if not self.weapon_spin:
            coord = (self.center_vector.x - self.image.get_width() / 2 - cam_offset[0],
                     self.center_vector.y - self.image.get_height() / 2 - cam_offset[1])
        if self.weapon_spin:
            coord = (self.center_vector.x - self.current_image.get_width() / 2 - cam_offset[0],
                     self.center_vector.y - self.current_image.get_height() / 2 - cam_offset[1])
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

class Item:
    def __init__(self, type_):
        pass


class Enemy:
    TYPES = {
        'default': {'hp': 20, 'move_speed': 1, 'damage': 10}
    }
    WIDTH, HEIGHT = 20, 20
    IMMUNITY_FRAME_DURATION = 1000

    def __init__(self, coord_x, coord_y, type_='default'):
        self.type_ = type_
        self.hp = self.TYPES[type_]['hp']
        self.move_speed = self.TYPES[type_]['move_speed']
        self.damage = self.TYPES[type_]['damage']
        self.rect = pygame.Rect(coord_x, coord_y, self.WIDTH, self.HEIGHT)
        self.position_vector = pygame.Vector2(coord_x, coord_y)
        self.immunity_timers = {}
        self.image = pygame.image.load(os.path.join('Assets', 'Enemy.png')).convert_alpha()

    def add_immunity(self, bullet):
        hit_time = pygame.time.get_ticks()
        self.immunity_timers.update({bullet: hit_time})

    def draw(self, window, cam_offset):
        window.blit(self.image, (self.rect.x + (Enemy.WIDTH - self.image.get_width()) // 2 - cam_offset[0],
                                 self.rect.y + (Enemy.HEIGHT - self.image.get_height()) // 2 - cam_offset[1]))

    def die(self):
        print('I am dead')


class Game:
    WIDTH, HEIGHT = 1000, 600
    ENEMY_SPAWN_RATE = 1000
    SPAWN_BOX_SIZE = 300
    SPAWN_BOX_OFFSET = 50
    TEXT_FONT = pygame.font.Font(None, 30)
    SPAWN_LIMIT = 30
    BULLET_DELETION_INTERVAL = 5000
    HP_BAR_WIDTH, HP_BAR_HEIGHT, HP_BAR_BORDER = 200, 50, 3
    YOU_DIED_FONT = pygame.font.Font(None, 100)

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
        self.window.fill(WHITE)
        self.player.draw(self.window, self.camera_offset)
        for weapon in self.player.weapons:
            for bullet in weapon.bullets:
                bullet.draw(self.window, self.camera_offset)

        def get_coord_y(obj):
            return obj.position_vector.y
        self.enemies.sort(key=get_coord_y)

        for enemy in self.enemies:
            enemy.draw(self.window, self.camera_offset)
        kills = self.TEXT_FONT.render(f"Kills: {self.player.kills}", True, BLACK)
        self.window.blit(kills, (10, 10))
        self.draw_hp_bar()

    def move_bullets(self):
        for weapon in self.player.weapons:
            for bullet in weapon.bullets:
                bullet.move(self.camera_offset)

    def move_enemies(self):
        for enemy in self.enemies:
            vector_to_player = pygame.Vector2(self.player.rect.centerx - enemy.rect.centerx,
                                              self.player.rect.centery - enemy.rect.centery)
            if not (vector_to_player.x == 0 and vector_to_player.y == 0):
                vector_to_player.normalize_ip()
            enemy.position_vector.x += vector_to_player.x * enemy.move_speed
            enemy.position_vector.y += vector_to_player.y * enemy.move_speed
            enemy.rect.x = enemy.position_vector.x
            enemy.rect.y = enemy.position_vector.y

    def create_enemy(self, coord_x, coord_y, type_='default'):
        enemy = Enemy(coord_x, coord_y, type_=type_)
        self.enemies.append(enemy)

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
        if self.player.current_hp <= 0:
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

    def draw_main_menu(self):
        pass


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
