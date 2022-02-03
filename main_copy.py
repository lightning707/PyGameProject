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


class Player(pygame.sprite.Sprite):
    WIDTH, HEIGHT = 35, 35
    CLASSES = {
        'default': {'hp': 100, 'items': [], 'move_speed': 5}
    }
    IMMUNITY_FRAME_DURATION = 500
    WEAPON_COOLDOWN = 500

    def __init__(self, coord_x, coord_y, class_='default', *groups):
        super().__init__(*groups)
        self.image = pygame.image.load(os.path.join('Assets', 'Player.png')).convert_alpha()
        self.kills = 0
        self.class_ = class_
        self.max_hp = self.CLASSES[class_]['hp']
        self.current_hp = self.max_hp
        self.items = self.CLASSES[class_]['items']
        self.move_speed = self.CLASSES[class_]['move_speed']
        self.rect = pygame.Rect(coord_x, coord_y, self.WIDTH, self.HEIGHT)

        self.current_weapon = Weapon('default')
        self.weapons = [self.current_weapon]
        self.last_damage_taken_time = pygame.time.get_ticks()

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

    def draw(self, window):
        window.blit(self.image, (self.rect.x + (Player.WIDTH - self.image.get_width()) // 2,
                                 self.rect.y + (Player.HEIGHT - self.image.get_height()) // 2))
        self.current_weapon.draw(window)


class Weapon(pygame.sprite.Sprite):
    DISTANCE_FROM_PLAYER = 15

    with open('Const/weapons.json') as fd:
        WEAPONS = json.load(fd)

    def __init__(self, name, *groups):
        super().__init__(*groups)
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
            self.default_image = pygame.image.load(os.path.join('Assets', 'Weapon.png')).convert_alpha()
            self.image = self.default_image

            self.center_vector = pygame.Vector2()
            self.rect = pygame.Rect(self.center_vector, (self.image.get_width(), self.image.get_height()))
            self.vector_to_mouse = pygame.Vector2()
            self.prev_vector_to_mouse = self.vector_to_mouse

    def shoot(self):
        if pygame.time.get_ticks() - self.last_shoot_time >= self.cooldown:
            self.last_shoot_time = pygame.time.get_ticks()
            bullet = Bullet(self.center_vector.x, self.center_vector.y, self.vector_to_mouse, speed=self.bullet_speed,
                            damage=self.damage, bounce=self.bounce, chain=self.chain, pierce=self.pierce)
            self.bullets.append(bullet)

    def update_position(self, player_center_x, player_center_y):
        self.vector_to_mouse = pygame.Vector2(pygame.mouse.get_pos()[0] - player_center_x,
                                              pygame.mouse.get_pos()[1] - player_center_y)
        self.vector_to_mouse.normalize_ip()
        self.center_vector = pygame.Vector2(player_center_x, player_center_y) + self.vector_to_mouse * self.DISTANCE_FROM_PLAYER

        if self.vector_to_mouse.x > 0:
            self.image = pygame.transform.rotate(self.default_image, self.vector_to_mouse.angle_to(pygame.Vector2(1,0)))
        else:
            self.image = pygame.transform.flip(self.default_image, flip_x=True, flip_y=False)
            self.image = pygame.transform.rotate(self.image, self.vector_to_mouse.angle_to(pygame.Vector2(-1, 0)))
        image_width = self.image.get_width()
        image_height = self.image.get_height()
        self.rect.x = self.center_vector.x - image_width / 2
        self.rect.y = self.center_vector.y - image_height / 2
        self.rect.width = image_width
        self.rect.height = image_height
        print(self.rect)

    def draw(self, window):
        window.blit(self.image, self.rect)


class Bullet(pygame.sprite.Sprite):
    WIDTH, HEIGHT = 3, 3
    DELETION_OFFSET = 300

    def __init__(self, coord_x, coord_y, vector, *groups, speed=3, color=BLACK, damage=5, is_allied=False, bounce=False,
                 pierce=0, chain=0, duration=2000):
        super().__init__(*groups)
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

    def draw(self, window):
        pygame.draw.rect(window, self.color, self.rect)


class Item:
    def __init__(self, type_):
        pass


class Enemy(pygame.sprite.Sprite):
    TYPES = {
        'default': {'hp': 20, 'move_speed': 1, 'damage': 10}
    }
    WIDTH, HEIGHT = 20, 20
    IMMUNITY_FRAME_DURATION = 1000

    def __init__(self, coord_x, coord_y, *groups, type_='default'):
        print(*groups)
        super().__init__()
        self.add(*groups)
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

    def draw(self, window):
        window.blit(self.image, (self.rect.x + (Enemy.WIDTH - self.image.get_width()) // 2,
                                 self.rect.y + (Enemy.HEIGHT - self.image.get_height()) // 2))

    def die(self):
        print('I am dead')

    def update(self):
        pass


class CameraGroup(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        self.offset = pygame.Vector2()

    def custom_draw(self):
        for sprite in self.sprites():
            offset_rect = sprite.rect.topleft - self.offset
            self.display_surface.blit(sprite.image, offset_rect)


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
        self.camera_group = CameraGroup()
        self.enemy_group = pygame.sprite.Group()

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

        self.all_sprites = pygame.sprite.Group()


    def draw_hp_bar(self):
        hp_bar_border_rect = pygame.Rect(self.WIDTH - self.HP_BAR_WIDTH - 10, 10,
                                         self.HP_BAR_WIDTH, self.HP_BAR_HEIGHT)
        current_hp_percentage = self.player.current_hp / self.player.max_hp
        hp_bar_rect = pygame.Rect(self.WIDTH - self.HP_BAR_WIDTH - 10 + self.HP_BAR_BORDER, 10 + self.HP_BAR_BORDER,
                                  (self.HP_BAR_WIDTH - self.HP_BAR_BORDER * 2) * current_hp_percentage, self.HP_BAR_HEIGHT - self.HP_BAR_BORDER * 2)
        pygame.draw.rect(self.window, BLACK, rect=hp_bar_border_rect, width=self.HP_BAR_BORDER)
        pygame.draw.rect(self.window, RED, rect=hp_bar_rect)

    def draw(self):
        self.window.fill(WHITE)
        self.player.draw(self.window)
        for weapon in self.player.weapons:
            for bullet in weapon.bullets:
                bullet.draw(self.window)

        def get_coord_y(obj):
            return obj.position_vector.y
        self.enemies.sort(key=get_coord_y)

        for enemy in self.enemies:
            enemy.draw(self.window)
        kills = self.TEXT_FONT.render(f"Kills: {self.player.kills}", True, BLACK)
        self.window.blit(kills, (10, 10))
        self.draw_hp_bar()

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
        enemy = Enemy(coord_x, coord_y, CameraGroup, type_=type_)
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

    def player_collision(self):
        if pygame.time.get_ticks() - self.player.last_damage_taken_time > Player.IMMUNITY_FRAME_DURATION:
            self.player.last_damage_taken_time = pygame.time.get_ticks()
            for enemy in self.enemies:
                if self.player.rect.colliderect(enemy.rect):
                    self.player.current_hp -= enemy.damage

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
        game.state_handler()
        if game.state == 'running':
            game.player.current_weapon.update_position(game.player.rect.centerx, game.player.rect.centery)
            game.player.move_handler()
            game.player.shoot_handler()
            game.move_bullets()
            game.move_enemies()
            game.spawn_enemies()
            game.bullet_collision()
            game.player_collision()
            game.delete_bullets_out_of_bounds()
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
        print(game.state)
    pygame.quit()


main()
