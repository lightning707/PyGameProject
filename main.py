import pygame

import os
import random
import json

pygame.font.init()
pygame.display.set_caption('My game')
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
FPS = 60


class Player:
    IMAGE = pygame.image.load(os.path.join('Assets', 'Player.png'))
    WIDTH, HEIGHT = 35, 35
    CLASSES = {
        'default': {'hp': 100, 'items': [], 'move_speed': 5}
    }
    IMMUNITY_FRAME_DURATION = 0.5
    WEAPON_COOLDOWN = 500

    def __init__(self, coord_x, coord_y, class_='default'):
        self.kills = 0
        self.class_ = class_
        self.hp = self.CLASSES[class_]['hp']
        self.items = self.CLASSES[class_]['items']
        self.move_speed = self.CLASSES[class_]['move_speed']
        self.rect = pygame.Rect(coord_x, coord_y, self.WIDTH, self.HEIGHT)

        self.current_weapon = Weapon('default')
        self.weapons = [self.current_weapon]

        self.vector = (0, 0)
        self.speed = 0
        self.weapon_cd_clock = pygame.time.Clock()
        self.last_shoot_time = pygame.time.get_ticks()

    def move_handler(self):
        keys_pressed = pygame.key.get_pressed()
        if (keys_pressed[pygame.K_a] or keys_pressed[pygame.K_LEFT]) and self.rect.x > 0:
            self.rect.x -= self.move_speed
        if (keys_pressed[pygame.K_d] or keys_pressed[pygame.K_RIGHT]) and (
                self.rect.x + self.WIDTH < Game.WIDTH):
            self.rect.x += self.move_speed
        if (keys_pressed[pygame.K_w] or keys_pressed[pygame.K_UP]) and self.rect.y > 0:
            self.rect.y -= self.move_speed
        if (keys_pressed[pygame.K_s] or keys_pressed[pygame.K_DOWN]) and (
                self.rect.y + self.HEIGHT < Game.HEIGHT):
            self.rect.y += self.move_speed

    def shoot_handler(self):
        keys_pressed = pygame.key.get_pressed()
        if keys_pressed[pygame.K_SPACE]:
            self.current_weapon.shoot()


class Weapon:
    DISTANCE_FROM_PLAYER = 15
    with open('Const/weapons.json') as fd:
        WEAPONS = json.load(fd)
        print(WEAPONS)

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
            self.last_shoot_time = pygame.time.get_ticks()
            self.bullets = []

            self.position_vector = pygame.Vector2(-100, -100)
            self.vector_to_mouse = pygame.Vector2(0, 0)

    def shoot(self):
        if pygame.time.get_ticks() - self.last_shoot_time >= self.cooldown:
            self.last_shoot_time = pygame.time.get_ticks()
            bullet = Bullet(self.position_vector.x, self.position_vector.y, self.vector_to_mouse, speed=self.bullet_speed,
                            damage=self.damage)
            self.bullets.append(bullet)

    def update_position(self, player_center_x, player_center_y):
        self.vector_to_mouse = pygame.Vector2(pygame.mouse.get_pos()[0] - player_center_x,
                                              pygame.mouse.get_pos()[1] - player_center_y)
        self.vector_to_mouse.normalize_ip()
        self.position_vector = pygame.Vector2(player_center_x, player_center_y) + self.vector_to_mouse * self.DISTANCE_FROM_PLAYER


class Bullet:
    WIDTH, HEIGHT = 3, 3
    DELETION_OFFSET = 300
    instances = []

    def __init__(self, coord_x, coord_y, vector, speed=3, color=BLACK, damage=5, is_allied=False, bounce=False,
                 pierce=0, chain=0, duration=2000):
        self.rect = pygame.Rect(coord_x, coord_y, self.WIDTH, self.HEIGHT)
        self.vector = vector
        self.is_allied = is_allied
        self.color = color
        self.speed = speed
        self.bounce = bounce
        self.damage = damage
        self.pierce = pierce
        self.chain = chain
        self.duration = duration
        self.position_vector = pygame.Vector2(coord_x, coord_y)
        self.__class__.instances.append(self)

    def move(self):
        if self.bounce:
            if self.rect.right >= Game.WIDTH or self.rect.left <= 0:
                self.vector.x *= -1
            if self.rect.bottom >= Game.HEIGHT or self.rect.top <= 0:
                self.vector.y *= -1
        self.position_vector.x += self.vector.x * self.speed
        self.position_vector.y += self.vector.y * self.speed
        self.rect.x = self.position_vector.x
        self.rect.y = self.position_vector.y


class Item:
    def __init__(self, type_):
        pass


class Enemy:
    TYPES = {
        'default': {'hp': 20, 'move_speed': 1}
    }
    IMAGE = pygame.image.load(os.path.join('Assets', 'Enemy.png'))
    WIDTH, HEIGHT = 20, 20
    IMMUNITY_FRAME_DURATION = 1000
    instances = []

    def __init__(self, coord_x, coord_y, type_='default'):
        self.type_ = type_
        self.hp = self.TYPES[type_]['hp']
        self.move_speed = self.TYPES[type_]['move_speed']
        self.rect = pygame.Rect(coord_x, coord_y, self.WIDTH, self.HEIGHT)
        self.position_vector = pygame.Vector2(coord_x, coord_y)
        self.immunity_timers = {}
        self.__class__.instances.append(self)

    def add_immunity(self, bullet):
        hit_time = pygame.time.get_ticks()
        self.immunity_timers.update({bullet: hit_time})

    def die(self):
        print('I am dead')


class Game:
    WIDTH, HEIGHT = 1000, 600
    ENEMY_SPAWN_RATE = 1000
    SPAWN_BOX_SIZE = 300
    SPAWN_BOX_OFFSET = 50
    TEXT_FONT = pygame.font.Font(None, 30)
    SPAWN_LIMIT = 10
    BULLET_DELETION_INTERVAL = 5000

    def __init__(self):
        self.window = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        self.player = Player((self.WIDTH - Player.WIDTH) // 2, (self.HEIGHT - Player.HEIGHT) // 2)
        self.state = 'running'
        self.enemies = []
        self.last_spawn_time = pygame.time.get_ticks()
        self.last_bullet_deletion_time = pygame.time.get_ticks()

    def draw(self):
        self.window.fill(WHITE)
        self.window.blit(Player.IMAGE,
                         (self.player.rect.x + (Player.WIDTH - Player.IMAGE.get_width()) // 2,
                          self.player.rect.y + (Player.HEIGHT - Player.IMAGE.get_height()) // 2))
        for weapon in self.player.weapons:
            for bullet in weapon.bullets:
                pygame.draw.rect(self.window, bullet.color, bullet.rect)
        for enemy in self.enemies:
            self.window.blit(Enemy.IMAGE,
                         (enemy.rect.x + (Enemy.WIDTH - Enemy.IMAGE.get_width()) // 2,
                          enemy.rect.y + (Enemy.HEIGHT - Enemy.IMAGE.get_height()) // 2))
        kills = self.TEXT_FONT.render(f"Kills: {self.player.kills}", True, BLACK)
        self.window.blit(kills, (10, 10))
        pygame.display.update()

    def move_bullets(self):
        for weapon in self.player.weapons:
            for bullet in weapon.bullets:
                bullet.move()

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
                spawn_coord = (random.randint(0, self.WIDTH), random.randint(-self.SPAWN_BOX_SIZE, -self.SPAWN_BOX_OFFSET))
            elif spawn_sector == 'left':
                spawn_coord = (random.randint(-self.SPAWN_BOX_SIZE, -self.SPAWN_BOX_OFFSET), random.randint(0, self.HEIGHT))
            elif spawn_sector == 'right':
                spawn_coord = (random.randint(self.WIDTH + self.SPAWN_BOX_OFFSET, self.WIDTH + self.SPAWN_BOX_SIZE),
                               random.randint(0, self.HEIGHT))
            elif spawn_sector == 'bottom':
                spawn_coord = (random.randint(0, self.WIDTH),
                               random.randint(self.HEIGHT + self.SPAWN_BOX_OFFSET, self.HEIGHT + self.SPAWN_BOX_SIZE))
            self.create_enemy(spawn_coord[0], spawn_coord[1])

    def state_handler(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.state = 'quit'
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    self.state = 'paused'
                else:
                    self.state = 'running'

    def bullet_collision(self):
        for bullet in Bullet.instances:
            for enemy in self.enemies:
                if bullet.rect.colliderect(enemy.rect):
                    current_time = pygame.time.get_ticks()
                    if bullet not in enemy.immunity_timers.keys() or \
                            current_time - enemy.immunity_timers[bullet] > enemy.IMMUNITY_FRAME_DURATION:
                        enemy.add_immunity(bullet)
                        enemy.hp -= bullet.damage
                        print(enemy.hp)
                        if enemy.hp <= 0:
                            enemy.die()
                            self.player.kills += 1
                            self.enemies.remove(enemy)

    def delete_bullets_out_of_bounds(self):
        if self.last_bullet_deletion_time >= self.BULLET_DELETION_INTERVAL:
            for weapon in self.player.weapons:
                for bullet in weapon.bullets:
                    if not bullet.bounce:
                        if bullet.rect.left + bullet.DELETION_OFFSET < 0 or \
                                bullet.rect.right - bullet.DELETION_OFFSET > Game.WIDTH or \
                                bullet.rect.top + bullet.DELETION_OFFSET < 0 or \
                                bullet.rect.bottom - bullet.DELETION_OFFSET > Game.HEIGHT:
                            weapon.bullets.remove(bullet)


def main():
    clock = pygame.time.Clock()
    game = Game()
    while game.state != 'quit':
        clock.tick(FPS)
        game.state_handler()
        if game.state == 'running':
            game.player.current_weapon.update_position(game.player.rect.centerx, game.player.rect.centery)
            game.player.move_handler()
            game.player.shoot_handler()
            game.move_bullets()
            game.move_enemies()
            game.spawn_enemies()
            game.bullet_collision()
            game.delete_bullets_out_of_bounds()
        game.draw()
    pygame.quit()


main()
