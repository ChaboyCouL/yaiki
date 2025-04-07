# sound_manager.py
import pygame
import os


class SoundManager:
    def __init__(self):
        pygame.mixer.init()
        self.sound_volume = 0.5
        self.music_volume = 0.3
        self.current_music = None
        self.sounds = {}
        self.music = {}

        # Получаем абсолютный путь к корню проекта
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.sounds_dir = os.path.join(self.base_dir, 'assets', 'sounds')

        self.load_sounds()
        self.set_volumes()

    def load_sounds(self):
        sound_files = {
            'jump': 'jump.ogg',
            'collision': 'collision.ogg',
            'candy': 'candy_pickup.ogg',
            'button': 'button_click.ogg',
            'record': 'record.ogg'
        }

        music_files = {
            'menu': 'menu_music.ogg',
            'game': 'game_music.ogg'
        }

        # Загрузка звуковых эффектов
        for name, filename in sound_files.items():
            path = os.path.join(self.sounds_dir, filename)
            if os.path.exists(path):
                self.sounds[name] = pygame.mixer.Sound(path)
            else:
                print(f"Warning: Sound file {filename} not found at {path}")

        # Загрузка музыки
        for name, filename in music_files.items():
            path = os.path.join(self.sounds_dir, filename)
            if os.path.exists(path):
                self.music[name] = path
            else:
                print(f"Warning: Music file {filename} not found at {path}")

    def set_volumes(self):
        for sound in self.sounds.values():
            sound.set_volume(self.sound_volume)
        pygame.mixer.music.set_volume(self.music_volume)

    def play_music(self, track_name, loops=-1):
        if track_name in self.music:
            if pygame.mixer.music.get_busy() and self.current_music == track_name:
                return

            try:
                pygame.mixer.music.load(self.music[track_name])
                pygame.mixer.music.play(loops)
                self.current_music = track_name
            except pygame.error as e:
                print(f"Error playing music: {e}")

    def play_sound(self, name):
        if name in self.sounds:
            try:
                self.sounds[name].play()
            except pygame.error as e:
                print(f"Error playing sound {name}: {e}")

    def stop_music(self):
        pygame.mixer.music.stop()
        self.current_music = None

    def fadeout_music(self, duration=1000):
        pygame.mixer.music.fadeout(duration)
        self.current_music = None