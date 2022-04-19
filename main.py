import pygame
from os import environ
from strings import CONTROLS_TEXT #@UnresolvedImport
from settings import Settings #@UnresolvedImport
from game import Game #@UnresolvedImport

if __name__ == '__main__':
    print("\n" + CONTROLS_TEXT + "\n\nPress 'Play' or 'm' to close the menu and start!\n")
    
    settings = Settings()
    environ["SDL_VIDEO_WINDOW_POS"] = settings.window_loc # environ['SDL_VIDEO_CENTERED'] = '1'
    pygame.display.init()
    pygame.display.set_caption("Avoid the bugs (Balloons)")
    pygame.display.set_icon(pygame.image.load("game_data/icon.png"))
    screen = pygame.display.set_mode([750, 750]) if settings.frame else pygame.display.set_mode([750, 750], pygame.NOFRAME)
    clock = pygame.time.Clock()
    game = Game(settings, True)
    game.loop(screen, clock)
    settings.save_settings()
    pygame.display.quit()