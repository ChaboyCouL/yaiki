import pygame
import random
import os

class SpikeGenerator:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.spike_images = self.load_sprites()

    def load_sprites(self):
        spikes_path = os.path.join(self.base_dir, 'assets', 'images', 'spikes')
        return {
            'top': self.load_image(spikes_path, 'spike_top.png'),
            'side': self.load_image(spikes_path, 'spike_wall.png')
        }

    def load_image(self, path, filename):
        try:
            img = pygame.image.load(os.path.join(path, filename)).convert_alpha()
            return pygame.transform.scale2x(img)
        except FileNotFoundError:
            print(f"Spike image {filename} not found!")
            return pygame.Surface((64, 64))

    def generate(self):
        spikes = []
        # Генерация верхних шипов
        spike_width = self.spike_images['top'].get_width()
        for x in range(0, self.width, spike_width):
            if random.random() < 0.4:
                spikes.append({
                    'rect': pygame.Rect(x, 0, spike_width, self.spike_images['top'].get_height()),
                    'image': self.spike_images['top']
                })
        return spikes