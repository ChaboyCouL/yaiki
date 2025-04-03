import pygame
import os
from src.menu import MainMenu
from src.game import Game
from src.records import Records
from src.sound_manager import SoundManager


def main():
    pygame.init()
    pygame.display.set_caption("Pixel Bird")
    screen = pygame.display.set_mode((800, 600))
    clock = pygame.time.Clock()

    # Инициализация систем
    sound_manager = SoundManager()
    records = Records()
    game = Game(screen, records, sound_manager)
    menu = MainMenu(screen, records, sound_manager)

    running = True
    while running:
        sound_manager.play_music('menu')
        menu_result = menu.run()

        if menu_result == 'play':
            sound_manager.play_music('game')
            game_result = game.run()
            if game_result == 'quit':
                running = False
        else:
            running = False

        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()