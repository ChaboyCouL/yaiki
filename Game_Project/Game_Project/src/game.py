import pygame
import random
import os
from src.bird import Bird
from src.spikes import SpikeGenerator


class Game:
    def __init__(self, screen, records, sound_manager):
        self.screen = screen
        self.records = records
        self.sound_manager = sound_manager
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.width, self.height = screen.get_size()
        self.reset()

    def reset(self):
        assets_path = os.path.join(self.base_dir, 'assets')

        try:
            # Загрузка изображений
            bird_img = pygame.image.load(
                os.path.join(assets_path, 'images', 'birds', 'bird1.png')
            ).convert_alpha()
            self.bird = Bird(bird_img, self.sound_manager)

            self.candy_img = pygame.image.load(
                os.path.join(assets_path, 'images', 'ui', 'candy.png')
            ).convert_alpha()

            self.background = pygame.image.load(
                os.path.join(assets_path, 'images', 'ui', 'game_bg.png')
            ).convert()
        except FileNotFoundError as e:
            print(f"Error loading image: {e}")
            raise

        self.spike_generator = SpikeGenerator(self.width, self.height)
        self.spikes = self.spike_generator.generate()
        self.candy = None
        self.score = 0
        self.running = True
        self.game_started = False

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                if not self.game_started:
                    self.game_started = True
                self.bird.jump()

    def check_collisions(self):
        # Проверка столкновений с шипами
        for spike in self.spikes:
            if self.bird.rect.colliderect(spike['rect']):
                self.sound_manager.play_sound('collision')
                self.running = False
        # Сбор конфет
        if self.candy and self.bird.rect.colliderect(self.candy['rect']):
            self.sound_manager.play_sound('candy')
            self.score += 50
            self.candy = None

    def draw(self):
        self.screen.blit(self.background, (0, 0))
        for spike in self.spikes:
            self.screen.blit(spike['image'], spike['rect'])
        self.screen.blit(self.bird.image, self.bird.rect)
        if self.candy:
            self.screen.blit(self.candy['image'], self.candy['rect'])
        # Отрисовка счета
        font = pygame.font.Font(None, 36)
        text = font.render(f"Score: {self.score}", True, (255, 255, 255))
        self.screen.blit(text, (10, 10))
        pygame.display.flip()

    def run(self):
        clock = pygame.time.Clock()
        while self.running:
            dt = clock.tick(60) / 1000
            self.handle_input()

            if self.game_started:
                self.bird.update(dt)
                self.check_collisions()
                self.score += 1

            self.draw()

        self.records.add_score(self.score)
        return 'menu'