import pygame
import os


class MainMenu:
    def __init__(self, screen, records, sound_manager):
        self.screen = screen
        self.records = records
        self.sound_manager = sound_manager
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.current_bird = 0
        self.selected_button = 0
        self.running = True
        self.load_assets()

    def load_assets(self):
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

        # Загрузка UI элементов
        ui_path = os.path.join(assets_path, 'images', 'ui')
        self.ui = {
            'play_btn': [
                self.load_image(ui_path, 'button_play_0.png'),
                self.load_image(ui_path, 'button_play_1.png')
            ],
            'exit_btn': [
                self.load_image(ui_path, 'button_exit_0.png'),
                self.load_image(ui_path, 'button_exit_1.png')
            ],
            'arrow': self.load_image(ui_path, 'arrow.png'),
            'background': self.load_image(ui_path, 'menu_bg.png')
        }

    def load_image(self, path, filename):
        try:
            return pygame.image.load(os.path.join(path, filename)).convert_alpha()
        except FileNotFoundError:
            print(f"UI image {filename} not found!")
            return pygame.Surface((100, 40))

    def handle_events(self):
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
                elif event.key == pygame.K_RETURN:
                    return 'play' if self.selected_button == 0 else 'exit'
        return None

    def draw(self):
        self.screen.blit(self.ui['background'], (0, 0))
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
        pygame.display.flip()

    def run(self):
        self.running = True
        while self.running:
            result = self.handle_events()
            if result:
                return result
            self.draw()
            pygame.time.Clock().tick(60)
        return 'quit'