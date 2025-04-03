import pygame

class Bird:
    def __init__(self, image, sound_manager):
        self.original_image = image
        self.image = pygame.transform.scale2x(image)
        self.rect = self.image.get_rect(center=(400, 300))
        self.sound_manager = sound_manager
        self.velocity = 0
        self.gravity = 980
        self.jump_force = -450
        self.direction = 'right'

    def jump(self):
        self.velocity = self.jump_force
        self.sound_manager.play_sound('jump')

    def reverse(self):
        self.velocity *= -0.7
        self.direction = 'left' if self.direction == 'right' else 'right'
        self.sound_manager.play_sound('bounce')

    def update(self, dt):
        self.velocity += self.gravity * dt
        self.rect.y += self.velocity * dt
        # Ограничение скорости
        if self.velocity > 500:
            self.velocity = 500