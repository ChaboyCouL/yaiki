import pygame
import random
import os
import json
import math
import time

pygame.init()
pygame.mixer.init()


class LoadingBar:
    def __init__(self, screen, width=400, height=30):
        self.screen = screen
        self.width = width
        self.height = height
        self.progress = 0
        self.max_progress = 100
        self.x = (screen.get_width() - width) // 2
        self.y = screen.get_height() - 100
        self.border_color = (255, 255, 255)
        self.bar_color = (0, 255, 0)
        self.bg_color = (50, 50, 50)

    def update(self, progress):
        self.progress = min(progress, self.max_progress)

    def draw(self):

        pygame.draw.rect(self.screen, self.border_color,
                         (self.x - 2, self.y - 2,
                          self.width + 4, self.height + 4), 2)

        pygame.draw.rect(self.screen, self.bg_color,
                         (self.x, self.y, self.width, self.height))

        bar_width = int((self.progress / self.max_progress) * self.width)
        pygame.draw.rect(self.screen, self.bar_color,
                         (self.x, self.y, bar_width, self.height))


        font = pygame.font.Font(None, 36)
        text = font.render(f"{int(self.progress)}%", True, (255, 255, 255))
        text_rect = text.get_rect(center=(self.x + self.width // 2, self.y + self.height // 2))
        self.screen.blit(text, text_rect)


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
        self.max_speed = 600
        self.base_speed = 500
        self.last_bounce_wall = None

    def jump(self):
        self.velocity_y = self.jump_force
        if self.sound_manager:
            self.sound_manager.play_sound('jump')

    def reverse(self, surface_normal_angle):
        if surface_normal_angle == 270:
            self.last_bounce_wall = 'top'
        elif surface_normal_angle == 90:
            self.last_bounce_wall = 'bottom'
        elif surface_normal_angle == 0:
            self.last_bounce_wall = 'left'
        elif surface_normal_angle == 180:
            self.last_bounce_wall = 'right'
        normal_angle_rad = math.radians(surface_normal_angle)
        reflection_angle = normal_angle_rad - math.radians(60)
        self.velocity_x = self.base_speed * math.cos(reflection_angle)
        self.velocity_y = -self.base_speed * math.sin(reflection_angle)
        self.direction = 'right' if self.velocity_x > 0 else 'left'
        if self.sound_manager:
            self.sound_manager.play_sound('bounce')

    def update(self, dt, spike_generator):
        self.velocity_y += self.gravity * dt
        speed = math.sqrt(self.velocity_x ** 2 + self.velocity_y ** 2)
        if speed > self.max_speed:
            scale = self.max_speed / speed
            self.velocity_x *= scale
            self.velocity_y *= scale
        new_x = self.rect.x + self.velocity_x * dt
        new_y = self.rect.y + self.velocity_y * dt
        screen_width, screen_height = 800, 600
        collision = False
        if new_y < 0:
            new_y = 0
            self.reverse(270)
            collision = True
        elif new_y + self.rect.height > screen_height:
            new_y = screen_height - self.rect.height
            self.reverse(90)
            collision = True

        if new_x < 0:
            new_x = 0
            self.reverse(0)
            collision = True
        elif new_x + self.rect.width > screen_width:
            new_x = screen_width - self.rect.width
            self.reverse(180)
            collision = True
        self.rect.x = new_x
        self.rect.y = new_y
        if collision:
            return True
        return False


class SpikeGenerator:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.spike_images = self._load_sprites()
        self.spike_margin = 20
        self.bird_radius = 50
        self.hitbox_reduction = 50

    def _load_sprites(self):
        spikes_path = os.path.join(self.base_dir, 'assets', 'images', 'spikes')
        return {
            'top': pygame.transform.rotate(self._load_image(spikes_path, 'spike_wall.png'), 180),
            'bottom': self._load_image(spikes_path, 'spike_wall.png'),
            'left': pygame.transform.rotate(self._load_image(spikes_path, 'spike_wall.png'), -90),
            'right': pygame.transform.rotate(self._load_image(spikes_path, 'spike_wall.png'), 90)
        }

    def _load_image(self, path, filename):
        try:
            img = pygame.image.load(os.path.join(path, filename)).convert_alpha()
            return pygame.transform.scale2x(img)
        except (FileNotFoundError, pygame.error) as e:
            print(f"Error loading image: {e}")
            return pygame.Surface((64, 64), pygame.SRCALPHA)

    def generate(self, avoid_direction=None, bird_pos=None, bounce_wall=None):
        spikes = []
        directions = ['top', 'bottom', 'left', 'right']

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
                    if random.random() < 0.7:
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
                    if random.random() < 0.7:
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
        bird_x, bird_y = bird_pos
        distance = math.sqrt((spike_rect.centerx - bird_x) ** 2 + (spike_rect.centery - bird_y) ** 2)
        return distance < self.bird_radius


class Records:
    def __init__(self):
        self.scores = []
        self.load_scores()

    def load_scores(self):
        try:
            with open('records.json', 'r') as f:
                self.scores = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.scores = [3167, 1879, 1774]

    def save_scores(self):
        with open('records.json', 'w') as f:
            json.dump(sorted(self.scores, reverse=True)[:3], f)

    def add_score(self, new_score):
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
        font = pygame.font.Font(None, 36)
        text = font.render("Top Scores:", True, (255, 255, 255))
        surface.blit(text, (20, 20))

        y = 60
        for i, score in enumerate(self.scores):
            color = (255, 215, 0) if i == 0 else (192, 192, 192) if i == 1 else (205, 127, 50)
            text = font.render(f"{i + 1}. {score}", True, color)
            surface.blit(text, (20, y))
            y += 40


class SoundManager:
    def __init__(self):
        self.sounds = {}
        self.music = {}
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self._load_audio()

    def _load_audio(self):
        audio_path = os.path.join(self.base_dir, 'assets', 'audio')


        music_files = {
            'menu': 'menu_music.mp3',
            'game': 'game_music.mp3'
        }

        for name, filename in music_files.items():
            self.music[name] = os.path.join(audio_path, 'music', filename)

    def play_sound(self, name):
        if name in self.sounds:
            self.sounds[name].play()

    def play_music(self, name, loops=-1):
        if name in self.music:
            pygame.mixer.music.load(self.music[name])
            pygame.mixer.music.play(loops)


class MainMenu:
    def __init__(self, screen, records, sound_manager):
        self.screen = screen
        self.records = records
        self.sound_manager = sound_manager
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.selected_button = 0
        self.load_assets()

    def load_assets(self):
        assets_path = os.path.join(self.base_dir, 'assets', 'images', 'ui')
        self.button_play_img = self._load_image(assets_path, 'button_play_0.png')
        self.button_exit_img = self._load_image(assets_path, 'button_exit_0.png')
        try:
            self.splash_img = pygame.image.load(os.path.join(assets_path, 'splash.png')).convert_alpha()
            self.menu_background = pygame.image.load(os.path.join(assets_path, 'splash_menu.png')).convert_alpha()
            self.menu_background = pygame.transform.scale(self.menu_background, (800, 600))
        except FileNotFoundError as e:
            print(f"Error loading splash images: {e}")
            self.splash_img = pygame.Surface((800, 600), pygame.SRCALPHA)
            self.menu_background = pygame.Surface((800, 600), pygame.SRCALPHA)
            self.menu_background.fill((30, 144, 255))  # Default blue background

    def _load_image(self, path, filename):
        try:
            return pygame.image.load(os.path.join(path, filename)).convert_alpha()
        except FileNotFoundError:
            print(f"UI image {filename} not found!")
            return pygame.Surface((200, 80), pygame.SRCALPHA)

    def show_splash_screen(self):
        loading_bar = LoadingBar(self.screen)

        # Simulate loading process
        for i in range(101):
            self.screen.blit(self.splash_img, (0, 0))
            loading_bar.update(i)
            loading_bar.draw()
            pygame.display.flip()
            time.sleep(0.03)  # Adjust speed of loading

        # Keep splash screen visible for a moment after loading completes
        time.sleep(0.5)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'quit'
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP or event.key == pygame.K_DOWN:
                    self.selected_button = 1 - self.selected_button
                    self.sound_manager.play_sound('button')
                elif event.key == pygame.K_RETURN:
                    if self.selected_button == 0:
                        return 'play'
                    else:
                        return 'quit'
        return None

    def draw(self):

        self.screen.blit(self.menu_background, (0, 0))


        self.records.draw_records(self.screen)


        play_pos = (400 - self.button_play_img.get_width() // 2, 300)
        exit_pos = (400 - self.button_exit_img.get_width() // 2, 400)


        if self.selected_button == 0:
            pygame.draw.rect(self.screen, (255, 255, 0),
                             (play_pos[0] - 5, play_pos[1] - 5,
                              self.button_play_img.get_width() + 10,
                              self.button_play_img.get_height() + 10), 3)
        else:
            pygame.draw.rect(self.screen, (255, 255, 0),
                             (exit_pos[0] - 5, exit_pos[1] - 5,
                              self.button_exit_img.get_width() + 10,
                              self.button_exit_img.get_height() + 10), 3)

        self.screen.blit(self.button_play_img, play_pos)
        self.screen.blit(self.button_exit_img, exit_pos)

        pygame.display.flip()

    def run(self):
        self.sound_manager.play_music('menu')
        while True:
            result = self.handle_events()
            if result:
                return result
            self.draw()
            pygame.time.Clock().tick(60)


class Game:
    def __init__(self, screen, records, sound_manager):
        self.screen = screen
        self.records = records
        self.sound_manager = sound_manager
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.width, self.height = screen.get_size()
        self.load_backgrounds()
        self.reset()

    def load_backgrounds(self):
        assets_path = os.path.join(self.base_dir, 'assets', 'images', 'ui')
        try:
            self.game_background = pygame.image.load(os.path.join(assets_path, 'splash_game.png')).convert_alpha()
            self.game_background = pygame.transform.scale(self.game_background, (800, 600))
        except FileNotFoundError:
            print("Game background not found, using default")
            self.game_background = pygame.Surface((800, 600))
            self.game_background.fill((30, 144, 255))  # Default blue background

    def reset(self):
        assets_path = os.path.join(self.base_dir, 'assets')

        try:
            bird_img = pygame.image.load(
                os.path.join(assets_path, 'images', 'birds', 'bird1.png')
            ).convert_alpha()
            self.bird = Bird(bird_img, self.sound_manager)
        except (FileNotFoundError, pygame.error) as e:
            print(f"Error loading game assets: {e}")
            raise

        initial_direction = self._get_initial_direction(self.bird)
        self.spike_generator = SpikeGenerator(self.width, self.height)
        self.spikes = self.spike_generator.generate(avoid_direction=initial_direction)
        self.score = 0
        self.running = True
        self.game_started = True

    def _get_initial_direction(self, bird):
        if abs(bird.velocity_x) > abs(bird.velocity_y):
            return 'right' if bird.velocity_x > 0 else 'left'
        else:
            return 'bottom' if bird.velocity_y > 0 else 'top'

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                if not self.game_started:
                    self.game_started = True
                self.bird.jump()

    def check_collisions(self):
        for spike in self.spikes:
            if self.bird.rect.colliderect(spike['rect']):
                if self.sound_manager:
                    self.sound_manager.play_sound('collision')
                self.running = False

    def draw(self):
        # Draw game background
        self.screen.blit(self.game_background, (0, 0))

        for spike in self.spikes:
            self.screen.blit(spike['image'], spike['image_rect'])
        self.screen.blit(self.bird.image, self.bird.rect)

        font = pygame.font.Font(None, 36)
        text = font.render(f"Score: {self.score}", True, (255, 255, 255))
        self.screen.blit(text, (10, 10))
        pygame.display.flip()

    def run(self):
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
                        bounce_wall=self.bird.last_bounce_wall
                    )

                self.check_collisions()
                self.score += 1

            self.draw()

        self.records.add_score(self.score)
        return 'menu'

    def _get_current_direction(self, bird):
        if abs(bird.velocity_x) > abs(bird.velocity_y):
            return 'right' if bird.velocity_x > 0 else 'left'
        else:
            return 'bottom' if bird.velocity_y > 0 else 'top'


def main():
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Pixel Bird")
    clock = pygame.time.Clock()

    sound_manager = SoundManager()
    records = Records()
    game = Game(screen, records, sound_manager)
    menu = MainMenu(screen, records, sound_manager)
    menu.show_splash_screen()

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
            game.reset()
            current_screen = result if result else 'menu'

        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()