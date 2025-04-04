import pygame
import random
import os
import json
import math
from typing import List, Dict, Any

# Инициализация pygame
pygame.init()
pygame.mixer.init()


# ======================== Класс Bird ========================
class Bird:
    def __init__(self, image, sound_manager):
        self.original_image = image
        self.image = pygame.transform.scale2x(image)
        self.rect = self.image.get_rect(center=(400, 300))
        self.sound_manager = sound_manager
        self.velocity_x = random.choice([-200, 200])
        self.velocity_y = random.choice([-200, 200])
        self.gravity = 1050
        self.jump_force = -500
        self.direction = 'right' if self.velocity_x > 0 else 'left'
        self.max_speed = 500
        self.base_speed = 400
        self.last_bounce_wall = None  # Последняя стена, от которой отскочила птица

    def jump(self):
        """Обрабатывает прыжок птицы"""
        self.velocity_y = self.jump_force
        if self.sound_manager:
            self.sound_manager.play_sound('jump')

    def reverse(self, surface_normal_angle):
        """Обрабатывает отскок с постоянной скоростью"""
        # Определяем стену, от которой отскакиваем
        if surface_normal_angle == 270:  # Верхняя стена
            self.last_bounce_wall = 'top'
        elif surface_normal_angle == 90:  # Нижняя стена
            self.last_bounce_wall = 'bottom'
        elif surface_normal_angle == 0:  # Левая стена
            self.last_bounce_wall = 'left'
        elif surface_normal_angle == 180:  # Правая стена
            self.last_bounce_wall = 'right'

        # Конвертируем угол нормали в радианы
        normal_angle_rad = math.radians(surface_normal_angle)

        # Угол отражения (60 градусов от нормали)
        reflection_angle = normal_angle_rad - math.radians(60)

        # Устанавливаем постоянную скорость при отскоке
        self.velocity_x = self.base_speed * math.cos(reflection_angle)
        self.velocity_y = -self.base_speed * math.sin(reflection_angle)

        # Обновляем направление
        self.direction = 'right' if self.velocity_x > 0 else 'left'
        if self.sound_manager:
            self.sound_manager.play_sound('bounce')

    def update(self, dt, spike_generator):
        """Обновляет положение птицы с учетом физики и границ"""
        # Применяем гравитацию только по Y
        self.velocity_y += self.gravity * dt

        # Ограничение скорости
        speed = math.sqrt(self.velocity_x ** 2 + self.velocity_y ** 2)
        if speed > self.max_speed:
            scale = self.max_speed / speed
            self.velocity_x *= scale
            self.velocity_y *= scale

        # Новые координаты
        new_x = self.rect.x + self.velocity_x * dt
        new_y = self.rect.y + self.velocity_y * dt

        # Проверка границ экрана
        screen_width, screen_height = 800, 600

        # Столкновение с границами
        collision = False
        if new_y < 0:  # Верхняя граница
            new_y = 0
            self.reverse(270)  # Нормаль вниз (270 градусов)
            collision = True
        elif new_y + self.rect.height > screen_height:  # Нижняя граница
            new_y = screen_height - self.rect.height
            self.reverse(90)  # Нормаль вверх (90 градусов)
            collision = True

        if new_x < 0:  # Левая граница
            new_x = 0
            self.reverse(0)  # Нормаль вправо (0 градусов)
            collision = True
        elif new_x + self.rect.width > screen_width:  # Правая граница
            new_x = screen_width - self.rect.width
            self.reverse(180)  # Нормаль влево (180 градусов)
            collision = True

        # Обновляем позицию
        self.rect.x = new_x
        self.rect.y = new_y

        # Если было столкновение, обновляем шипы
        if collision:
            return True
        return False

# ======================== Класс SpikeGenerator ========================
class SpikeGenerator:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.spike_images = self._load_sprites()
        self.spike_margin = 20
        self.bird_radius = 50
        self.hitbox_reduction = 15

    def _load_sprites(self):
        """Загружает изображения шипов"""
        spikes_path = os.path.join(self.base_dir, 'assets', 'images', 'spikes')
        return {
            'top': self._load_image(spikes_path, 'spike_top.png'),
            'bottom': self._load_image(spikes_path, 'spike_top.png'),
            'left': pygame.transform.rotate(self._load_image(spikes_path, 'spike_wall.png'), 90),
            'right': pygame.transform.rotate(self._load_image(spikes_path, 'spike_wall.png'), -90)
        }

    def _load_image(self, path, filename):
        """Загружает и масштабирует изображение"""
        try:
            img = pygame.image.load(os.path.join(path, filename)).convert_alpha()
            return pygame.transform.scale2x(img)
        except (FileNotFoundError, pygame.error) as e:
            print(f"Error loading image: {e}")
            return pygame.Surface((64, 64), pygame.SRCALPHA)

    def generate(self, avoid_direction=None, bird_pos=None, bounce_wall=None):
        """Генерирует шипы, избегая указанного направления и зоны вокруг птицы"""
        spikes = []
        directions = ['top', 'bottom', 'left', 'right']

        # Удаляем направление стены, от которой отскочила птица
        if bounce_wall:
            directions.remove(bounce_wall)
        elif avoid_direction:
            directions.remove(avoid_direction)

        for direction in directions:
            spike_image = self.spike_images[direction]
            spike_width = spike_image.get_width()
            spike_height = spike_image.get_height()

            if direction in ['top', 'bottom']:
                y = 0 if direction == 'top' else self.height - spike_height
                for x in range(0, self.width - spike_width, spike_width + self.spike_margin):
                    if random.random() < 0.4:
                        hitbox = pygame.Rect(
                            x + self.hitbox_reduction,
                            y + (self.hitbox_reduction if direction == 'bottom' else 0),
                            spike_width - 2 * self.hitbox_reduction,
                            spike_height - self.hitbox_reduction
                        )
                        if bird_pos is None or not self._is_near_bird(hitbox, bird_pos):
                            spikes.append({
                                'rect': hitbox,
                                'image_rect': pygame.Rect(x, y, spike_width, spike_height),
                                'image': spike_image,
                                'type': direction
                            })
            else:
                x = 0 if direction == 'left' else self.width - spike_width
                for y in range(0, self.height - spike_height, spike_height + self.spike_margin):
                    if random.random() < 0.4:
                        hitbox = pygame.Rect(
                            x + (0 if direction == 'left' else self.hitbox_reduction),
                            y + self.hitbox_reduction,
                            spike_width - self.hitbox_reduction,
                            spike_height - 2 * self.hitbox_reduction
                        )
                        if bird_pos is None or not self._is_near_bird(hitbox, bird_pos):
                            spikes.append({
                                'rect': hitbox,
                                'image_rect': pygame.Rect(x, y, spike_width, spike_height),
                                'image': spike_image,
                                'type': direction
                            })
        return spikes

    def _is_near_bird(self, spike_rect, bird_pos):
        """Проверяет, находится ли шип слишком близко к птице"""
        bird_x, bird_y = bird_pos
        distance = math.sqrt((spike_rect.centerx - bird_x) ** 2 + (spike_rect.centery - bird_y) ** 2)
        return distance < self.bird_radius

# ======================== Класс Records ========================
class Records:
    def __init__(self):
        self.scores = []
        self.load_scores()

    def load_scores(self):
        """Загружает рекорды из файла"""
        try:
            with open('records.json', 'r') as f:
                self.scores = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.scores = [200, 150, 100]  # Значения по умолчанию

    def save_scores(self):
        """Сохраняет рекорды в файл"""
        with open('records.json', 'w') as f:
            json.dump(sorted(self.scores, reverse=True)[:3], f)

    def add_score(self, new_score):
        """Добавляет новый результат"""
        updated = False
        for i in range(len(self.scores)):
            if new_score > self.scores[i]:
                self.scores.insert(i, new_score)
                updated = True
                break
        if not updated and len(self.scores) < 3:
            self.scores.append(new_score)
        self.scores = sorted(self.scores, reverse=True)[:3]
        self.save_scores()
        return updated

    def draw_records(self, surface):
        """Отрисовывает таблицу рекордов"""
        font = pygame.font.Font(None, 48)
        text = font.render("Top Scores:", True, (255, 255, 255))
        surface.blit(text, (300, 200))

        y = 250
        for i, score in enumerate(self.scores):
            color = (255, 215, 0) if i == 0 else (192, 192, 192) if i == 1 else (205, 127, 50)
            text = font.render(f"{i + 1}. {score}", True, color)
            surface.blit(text, (320, y))
            y += 50


# ======================== Класс SoundManager ========================
class SoundManager:
    def __init__(self):
        self.sounds = {}
        self.music = {}
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self._load_audio()

    def _load_audio(self):
        """Загружает звуки и музыку"""
        audio_path = os.path.join(self.base_dir, 'assets', 'audio')

        # Загрузка звуков
        sound_files = {
            'jump': 'jump.ogg',
            'bounce': 'jump.ogg',
            'collision': 'collision.ogg',
            'candy': 'candy_pickup.ogg',
            'button': 'button_click.ogg'
        }

        for name, filename in sound_files.items():
            try:
                self.sounds[name] = pygame.mixer.Sound(os.path.join(audio_path, 'sounds', filename))
            except pygame.error:
                print(f"Failed to load sound: {filename}")

        # Загрузка музыки
        music_files = {
            'menu': 'menu_music.ogg',
            'game': 'game_music.ogg'
        }

        for name, filename in music_files.items():
            self.music[name] = os.path.join(audio_path, 'music', filename)

    def play_sound(self, name):
        """Проигрывает звуковой эффект"""
        if name in self.sounds:
            self.sounds[name].play()

    def play_music(self, name, loops=-1):
        """Проигрывает фоновую музыку"""
        if name in self.music:
            pygame.mixer.music.load(self.music[name])
            pygame.mixer.music.play(loops)


# ======================== Класс MainMenu ========================
class MainMenu:
    def __init__(self, screen, records, sound_manager):
        self.screen = screen
        self.records = records
        self.sound_manager = sound_manager
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.current_bird = 0
        self.selected_button = 0
        self.load_assets()

    def load_assets(self):
        """Загружает ресурсы для меню"""
        assets_path = os.path.join(self.base_dir, 'assets')

        # Загрузка птичек
        self.bird_images = []
        birds_path = os.path.join(assets_path, 'images', 'birds')
        for i in range(1, 4):
            try:
                img = pygame.image.load(os.path.join(birds_path, f'bird{i}.png')).convert_alpha()
                self.bird_images.append(pygame.transform.scale2x(img))
            except FileNotFoundError:
                print(f"Bird image bird{i}.png not found!")
                self.bird_images.append(pygame.Surface((64, 64), pygame.SRCALPHA))

        # Загрузка UI элементов
        ui_path = os.path.join(assets_path, 'images', 'ui')
        self.ui = {
            'play_btn': [
                self._load_image(ui_path, 'button_play_0.png'),
                self._load_image(ui_path, 'button_play_1.png')
            ],
            'exit_btn': [
                self._load_image(ui_path, 'button_exit_0.png'),
                self._load_image(ui_path, 'button_exit_1.png')
            ],
            'arrow': self._load_image(ui_path, 'arrow.png'),
            'background': None  # Будем использовать синий фон вместо изображения
        }

    def _load_image(self, path, filename):
        """Загружает изображение"""
        try:
            return pygame.image.load(os.path.join(path, filename)).convert_alpha()
        except FileNotFoundError:
            print(f"UI image {filename} not found!")
            return pygame.Surface((100, 40), pygame.SRCALPHA)

    def handle_events(self):
        """Обрабатывает события в меню"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'quit'
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    self.current_bird = max(0, self.current_bird - 1)
                    self.sound_manager.play_sound('button')
                elif event.key == pygame.K_RIGHT:
                    self.current_bird = min(2, self.current_bird + 1)
                    self.sound_manager.play_sound('button')
                elif event.key == pygame.K_UP or event.key == pygame.K_DOWN:
                    self.selected_button = 1 - self.selected_button
                    self.sound_manager.play_sound('button')
                elif event.key == pygame.K_RETURN:
                    return 'play' if self.selected_button == 0 else 'exit'
        return None

    def draw(self):
        """Отрисовывает меню"""
        # Рисуем синий фон
        self.screen.fill((30, 144, 255))  # DodgerBlue

        # Рисуем полупрозрачное затемнение для лучшей читаемости
        overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        self.screen.blit(overlay, (0, 0))

        # Отрисовка птиц
        for i, img in enumerate(self.bird_images):
            x = 200 + i * 200
            y = 300
            self.screen.blit(img, (x, y))
            if i == self.current_bird:
                self.screen.blit(self.ui['arrow'], (x - 40, y))

        # Отрисовка кнопок
        play_img = self.ui['play_btn'][1 if self.selected_button == 0 else 0]
        exit_img = self.ui['exit_btn'][1 if self.selected_button == 1 else 0]
        self.screen.blit(play_img, (350, 450))
        self.screen.blit(exit_img, (350, 510))

        # Отрисовка рекордов
        self.records.draw_records(self.screen)

        pygame.display.flip()

    def run(self):
        """Главный цикл меню"""
        self.sound_manager.play_music('menu')
        while True:
            result = self.handle_events()
            if result:
                return result
            self.draw()
            pygame.time.Clock().tick(60)


# ======================== Класс Game ========================
class Game:
    def __init__(self, screen, records, sound_manager):
        self.screen = screen
        self.records = records
        self.sound_manager = sound_manager
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.width, self.height = screen.get_size()
        self.reset()

    def reset(self):
        """Сбрасывает состояние игры"""
        assets_path = os.path.join(self.base_dir, 'assets')

        try:
            bird_img = pygame.image.load(
                os.path.join(assets_path, 'images', 'birds', 'bird1.png')
            ).convert_alpha()
            self.bird = Bird(bird_img, self.sound_manager)

            self.candy_img = pygame.image.load(
                os.path.join(assets_path, 'images', 'ui', 'candy.png')
            ).convert_alpha()

            self.background = None
        except (FileNotFoundError, pygame.error) as e:
            print(f"Error loading game assets: {e}")
            raise

        initial_direction = self._get_initial_direction(self.bird)
        self.spike_generator = SpikeGenerator(self.width, self.height)
        self.spikes = self.spike_generator.generate(avoid_direction=initial_direction)
        self.candy = None
        self.score = 0
        self.running = True
        self.game_started = True

    def _get_initial_direction(self, bird):
        """Определяет начальное направление движения птицы"""
        if abs(bird.velocity_x) > abs(bird.velocity_y):
            return 'right' if bird.velocity_x > 0 else 'left'
        else:
            return 'bottom' if bird.velocity_y > 0 else 'top'

    def handle_input(self):
        """Обрабатывает пользовательский ввод"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                if not self.game_started:
                    self.game_started = True
                self.bird.jump()

    def check_collisions(self):
        """Проверяет столкновения"""
        for spike in self.spikes:
            if self.bird.rect.colliderect(spike['rect']):
                if self.sound_manager:
                    self.sound_manager.play_sound('collision')
                self.running = False

        if self.candy and self.bird.rect.colliderect(self.candy['rect']):
            if self.sound_manager:
                self.sound_manager.play_sound('candy')
            self.score += 50
            self.candy = None

    def draw(self):
        """Отрисовывает игровое поле"""
        self.screen.fill((30, 144, 255))

        for spike in self.spikes:
            self.screen.blit(spike['image'], spike['image_rect'])
        self.screen.blit(self.bird.image, self.bird.rect)

        if self.candy:
            self.screen.blit(self.candy['image'], self.candy['rect'])

        font = pygame.font.Font(None, 36)
        text = font.render(f"Score: {self.score}", True, (255, 255, 255))
        self.screen.blit(text, (10, 10))
        pygame.display.flip()

    def run(self):
        """Главный игровой цикл"""
        clock = pygame.time.Clock()
        self.sound_manager.play_music('game')

        while self.running:
            dt = clock.tick(60) / 1000

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    self.bird.jump()

            if self.game_started:
                needs_spike_update = self.bird.update(dt, self.spike_generator)

                if needs_spike_update:
                    current_direction = self._get_current_direction(self.bird)
                    bird_pos = (self.bird.rect.centerx, self.bird.rect.centery)
                    self.spikes = self.spike_generator.generate(
                        avoid_direction=current_direction,
                        bird_pos=bird_pos,
                        bounce_wall=self.bird.last_bounce_wall  # Передаем стену отскока
                    )

                self.check_collisions()
                self.score += 1

            self.draw()

        self.records.add_score(self.score)
        return 'menu'

    def _get_current_direction(self, bird):
        """Определяет текущее основное направление движения птицы"""
        if abs(bird.velocity_x) > abs(bird.velocity_y):
            return 'right' if bird.velocity_x > 0 else 'left'
        else:
            return 'bottom' if bird.velocity_y > 0 else 'top'

# ======================== Главная функция ========================
def main():
    """Точка входа в приложение"""
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Pixel Bird")
    clock = pygame.time.Clock()

    sound_manager = SoundManager()
    records = Records()
    game = Game(screen, records, sound_manager)
    menu = MainMenu(screen, records, sound_manager)

    current_screen = 'menu'
    running = True

    while running:
        if current_screen == 'menu':
            result = menu.run()
            if result == 'play':
                current_screen = 'game'
            else:
                running = False
        elif current_screen == 'game':
            result = game.run()
            game.reset()  # Сброс игры перед возвратом в меню
            current_screen = result if result else 'menu'

        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()