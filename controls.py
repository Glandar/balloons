import pygame

controls = [pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d, pygame.K_UP, pygame.K_LEFT, pygame.K_DOWN, pygame.K_RIGHT, pygame.K_SPACE, pygame.K_LALT, pygame.K_RALT, pygame.K_r]
names = ["pygame.K_w", "pygame.K_a", "pygame.K_s", "pygame.K_d", "pygame.K_UP", "pygame.K_LEFT", "pygame.K_DOWN", "pygame.K_RIGHT", "pygame.K_SPACE", "pygame.K_LALT", "pygame.K_RALT", "pygame.K_r"]
name_map = {key : value for key, value in zip(controls, names)}
replay_blitmap = {pygame.K_w : ["w", [285, 757]], pygame.K_a : ["a", [270, 777]], pygame.K_s : ["s", [285, 777]], pygame.K_d : ["d", [300, 777]],
                  pygame.K_UP : ["up", [460, 757]], pygame.K_LEFT : ["left", [430, 777]], pygame.K_DOWN : ["down", [455, 777]], pygame.K_RIGHT : ["right", [500, 777]],
                  pygame.K_SPACE : ["space", [355, 777]], pygame.K_LALT : ["l-alt", [325, 777]], pygame.K_RALT : ["r-alt", [395, 777]], pygame.K_r : ["r", [250, 767]]}
arrow_icon = [(-1, -1), (-1, -10), (-7, -10), ( 0, -17), ( 7, -10), ( 1, -10),
              ( 1, -1), ( 10, -1), ( 10, -7), ( 17,  0), ( 10,  7), ( 10,  1),
              ( 1,  1), ( 1,  10), ( 7,  10), ( 0,  17), (-7,  10), (-1,  10),
              (-1,  1), (-10,  1), (-10,  7), (-17,  0), (-10, -7), (-10, -1)]