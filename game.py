import pygame, math, time, random, numpy as np
from scipy.ndimage import gaussian_filter
from pygame import gfxdraw, BLEND_RGB_ADD
from itertools import chain
from strings import INTRO_TEXT #@UnresolvedImport
from colors import BLACK, GRAY, WHITE, RED, GREEN, BLUE, ORANGE, MAGENTA, PURPLE, CYAN, YELLOW, GOLD, DARK_RED #@UnresolvedImport
from constants import MOVE_SPEED, INFLATE_SPEED, GRAVITY, PRECISION, FRAME_RATE #@UnresolvedImport
from controls import controls, name_map, arrow_icon #@UnresolvedImport
from fonts import font25, font100 #@UnresolvedImport
from border import Border #@UnresolvedImport
from ball import Ball #@UnusedImport #@UnresolvedImport
from beam import Beam #@UnusedImport #@UnresolvedImport
from goal import Goal #@UnusedImport #@UnresolvedImport
from teleporter import Teleporter #@UnusedImport #@UnresolvedImport
from remover import Remover #@UnusedImport #@UnresolvedImport
from deposit import Deposit #@UnusedImport #@UnresolvedImport
import overlay #@UnresolvedImport
import creator #@UnresolvedImport
import replay #@UnresolvedImport

class Game:
    def __init__(self, settings, output):
        self.settings = settings
        self.run = True
        self.dummy_count = 0
        self.border = Border(750, 750)
        self.creator = None
        self.level_count = None
        self.output = output
        if self.output:
            self.rng = np.random.default_rng()
            self.times = {}
            self.color_set = [WHITE, RED, ORANGE, YELLOW, GREEN, CYAN, BLUE, PURPLE, MAGENTA]
            self.path_color_id = 2
            self.actions = []
            self.mouse_actions = []
            self.invalid = False
            self.message_lock = False
            self.glow_radius = 0
            self.background_surface = pygame.Surface((750, 750))
            self.create_background()
            self.beam_surface_textured = pygame.Surface((750, 750))
            self.beam_surface_blue = pygame.Surface((750, 750))
            self.beam_surface_blue.set_colorkey(BLACK)
            self.beam_surface = pygame.Surface((750, 750))
            self.create_beam_surface()
            self.darkness_surface = pygame.Surface((750, 750))
            self.darkness_surface.set_colorkey(WHITE)
            self.draw_surface = pygame.Surface((750, 750))
            self.draw_surface.set_colorkey(BLACK)
            self.prev_mouse_pos = None
            self.drag = False
            
    def loop(self, screen, clock):
        self.overlay = overlay.Overlay(self, self.settings, 1, -1)
        screen, clock = self.overlay.loop(screen, clock)
        
        while self.run:
            self.dummy_count += 1

            # Draw screen
            if self.settings.darkness:
                self.darkness_layer(self.dummy_count)
            mouse_pos = self.mouse(pygame.mouse.get_pos())
            self.redraw(screen, mouse_pos)
                    
            screen, clock = self.event_handling(pygame.event.get(), screen, clock, mouse_pos)
            if not self.run:
                return
            
            while self.level_count == 0:
                self.creator = creator.Creator(self, self.settings)
                screen, clock = self.creator.loop(screen, clock)
                if not self.run:
                    return
        
            if self.paused:
                pygame.display.flip()
                clock.tick(FRAME_RATE)
                continue
        
            # Game logic
            self.inflate()
            self.physics()
        
            # Go to the next level if the goals are achieved
            for goal in self.Goals:
                if goal.air > 0:
                    break
            else:
                if self.invalid:
                    print(f"completion does not qualify for scoring (level: {self.level_count}, frames: {self.frame_count})")
                elif self.frame_count == 0:
                    print(f"erroneous completion registered (level: {self.level_count}, frames: {self.frame_count})")
                else:
                    print(f"completed level {self.level_count}, time: {self.minutes:02}:{self.seconds:02} ({self.frame_count} frames)")
                    self.completion(self.level_count, self.frame_count)
                if self.settings.animations[1]:
                    self.delay(self, screen, clock, mouse_pos, round(FRAME_RATE * 1.2), FRAME_RATE)
                if self.level_count == len(self.settings.level_names) - 1:
                    self.overlay = overlay.Overlay(self, self.settings, self.level_count, -1)
                    self.level_count = None
                    screen, clock = self.overlay.loop(screen, clock)
                else:
                    self.level_count += 1
                    self.level(self.level_count)
            
            # Update counters
            if self.started:
                self.frame_count += 1
                self.minutes = self.frame_count // FRAME_RATE // 60
                self.seconds = self.frame_count // FRAME_RATE % 60
            pygame.display.flip()
            clock.tick(FRAME_RATE)
            
    def reset(self):
        self.drain = False
        self.L = [False, False]
        self.R = [False, False]
        self.I = [False, False]
        self.started = False
        self.invalid = bool(self.creator)
        self.paused = False
        self.frame_count = 0
        self.physics()
        if self.output:
            self.seconds = 0
            self.minutes = 0
            self.actions.clear()
            self.mouse_actions.clear()
            self.update_beam_surface(True)
            if self.settings.pathclear:
                self.draw_surface.fill(BLACK)
            
    def level(self, level_no, *, message_start = True):
        if message_start:
            print(f"level {level_no} ({self.settings.level_names[level_no]})")
        self.open(self.settings.level_names[level_no])
        self.reset()
        
    def open(self, name):
        with open(f"game_data/levels/{name}.txt", "r") as file:
            self.Balls, self.Beams, self.Goals, self.Teleporters, self.Removers, self.Deposits = eval(''.join(file.read().splitlines()))
        for coin in chain(self.Goals, self.Teleporters, self.Removers, self.Deposits):
            coin.attach(self)

    def event_handling(self, events, screen, clock, mouse_pos):
        action = [str(self.frame_count)]
        for event in events:
            # User pressed the cross
            if event.type == pygame.QUIT:
                print("Best session times:")
                print(self.times)
                self.run = False
            # User used the mouse
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.drag = True
            elif event.type == pygame.MOUSEBUTTONUP:
                self.prev_mouse_pos = None
                self.drag = False
            # User pressed a key
            elif event.type == pygame.KEYDOWN:
                if event.key in controls:
                    if self.paused:
                        continue
                    action.append(name_map[event.key])
                    self.started = True
                    if event.key == pygame.K_LEFT:
                        self.L[0] = True
                    elif event.key == pygame.K_RIGHT:
                        self.R[0] = True
                    elif event.key == pygame.K_UP:
                        self.Balls[0].jump()
                    elif event.key == pygame.K_DOWN:
                        for goal in self.Goals:
                            if goal.air > 0 and mouse_pos and goal.touch(mouse_pos):
                                self.inflator(self.Balls[0].weight() - goal.air - 16)
                                break
                        else:
                            self.I[0] = True
                    elif event.key == pygame.K_a:
                        self.L[1] = True
                    elif event.key == pygame.K_d:
                        self.R[1] = True
                    elif event.key == pygame.K_w:
                        self.Balls[1].jump()
                    elif event.key == pygame.K_s:
                        for goal in self.Goals:
                            if goal.air > 0 and mouse_pos and goal.touch(mouse_pos):
                                self.inflator(goal.air - self.Balls[1].weight() + 16)
                                break
                        else:
                            self.I[1] = True
                    elif event.key == pygame.K_RALT:
                        self.inflator(-self.Balls[1].weight())
                    elif event.key == pygame.K_LALT:
                        self.inflator(self.Balls[0].weight())
                    elif event.key == pygame.K_SPACE:
                        self.shooter()            
                    elif event.key == pygame.K_r:
                        self.drain = True
    
                elif event.key == pygame.K_q:
                    print("Best session times:")
                    print(self.times)
                    self.run = False
                elif event.key == pygame.K_f:
                    self.settings.frame = not self.settings.frame
                    screen = pygame.display.set_mode([750, screen.get_height()], 0 if self.settings.frame else pygame.NOFRAME)     
                elif event.key == pygame.K_ESCAPE:
                    self.paused = not self.paused
                elif event.key == pygame.K_m:
                    self.overlay = overlay.Overlay(self, self.settings, self.level_count, -1)
                    screen, clock = self.overlay.loop(screen, clock)
                elif event.key == pygame.K_l:
                    self.overlay = overlay.Overlay(self, self.settings, self.level_count, max((self.level_count - 1) // 30, 0))
                    screen, clock = self.overlay.loop(screen, clock)
                elif event.key == pygame.K_c:
                    self.invalid = True
                    self.creator = creator.Creator(self, self.settings)
                    screen, clock = self.creator.loop(screen, clock)
                elif event.key == pygame.K_j:
                    try:
                        with open(f"game_data/profiles/{self.settings.profile}/highscores/{self.settings.level_names[self.level_count]}.txt", "r") as file:
                            self.replay = replay.Replay(self, self.settings, *eval(file.read()))
                        screen, clock = self.replay.loop(screen, clock)
                    except FileNotFoundError:
                        print("No highscore set")
                elif event.key == pygame.K_k:
                    if self.actions:
                        self.replay = replay.Replay(self, self.settings, [[eval(a) for a in action] for action in self.actions], self.mouse_actions.copy(), self.frame_count)
                        screen, clock = self.replay.loop(screen, clock)
                elif event.key == pygame.K_b:
                    self.settings.background = (self.settings.background + 1) % 19
                    self.create_background()
                    self.update_beam_surface(True)
                elif event.key == pygame.K_F1:
                    if self.level_count > 1:
                        self.level_count -= 1
                        self.level(self.level_count)
                elif event.key == pygame.K_F2:
                    if self.level_count > 0:
                        self.level(self.level_count, message_start = False)
                elif event.key == pygame.K_F3:
                    if 0 < self.level_count < len(self.settings.level_names) - 1:
                        self.level_count += 1
                        self.level(self.level_count)
                elif event.key == pygame.K_F4:
                    self.path_color_id = (self.path_color_id + 1) % 9
                elif event.key == pygame.K_F5:
                    self.draw_surface.fill(BLACK)
                elif event.key == pygame.K_F6:
                    self.settings.dark_radius = max(self.settings.dark_radius - 10, 10)
                    print(f"Sight distance is set to {self.settings.dark_radius}")
                elif event.key == pygame.K_F7:
                    self.settings.darkness = not self.settings.darkness
                elif event.key == pygame.K_F8:
                    self.settings.dark_radius = min(self.settings.dark_radius + 10, 750)
                    print(f"Sight distance is set to {self.settings.dark_radius}")
                elif event.key == pygame.K_F9:
                    self.settings.dark_shape = (self.settings.dark_shape + 1) % 5
                elif event.key == pygame.K_F10:
                    self.level_count = random.randint(1, len(self.settings.level_names) - 1)
                    self.level(self.level_count)
                elif event.key == pygame.K_F11:
                    self.level_count = 0
                    self.level(self.level_count)
                elif event.key == pygame.K_F12:
                    self.save_level(f"game_data/levels/{time.strftime('%Y%m%d-%H%M%S')}.txt")
    
            # User released a key
            elif event.type == pygame.KEYUP and self.started and event.key in controls:
                action.append('-' + name_map[event.key])
                if event.key == pygame.K_LEFT:
                    self.L[0] = False
                    self.Balls[0].velocity.x = 0
                elif event.key == pygame.K_RIGHT:
                    self.R[0] = False
                    self.Balls[0].velocity.x = 0
                elif event.key == pygame.K_DOWN:
                    self.message_lock = False
                    self.I[0] = False
                elif event.key == pygame.K_a:
                    self.L[1] = False
                    self.Balls[1].velocity.x = 0
                elif event.key == pygame.K_d:
                    self.R[1] = False
                    self.Balls[1].velocity.x = 0
                elif event.key == pygame.K_s:
                    self.message_lock = False
                    self.I[1] = False
                elif event.key == pygame.K_r:
                    self.drain = False 
                elif event.key == pygame.K_RALT or event.key == pygame.K_LALT:
                    self.message_lock = False
        
        if len(action) > 1 and self.output:
            self.actions.append(action)
        return screen, clock
    
    def ball_interaction(self):
        if self.Balls[0].touch(self.Balls[1].next_pos(), self.Balls[0].size + self.Balls[1].size, True):
            interaction_speed = (self.Balls[0].weighted_speed() + self.Balls[1].weighted_speed()) / (self.Balls[0].weight() + self.Balls[1].weight())
            if self.Balls[0].position.y < self.Balls[1].position.y:
                if abs(self.Balls[0].position.y + self.Balls[0].velocity.y - self.Balls[1].position.y) < abs(self.Balls[0].position.y - self.Balls[1].position.y):
                    self.Balls[0].on_ball = True
                    self.Balls[0].doublejump = True
            elif self.Balls[1].position.y < self.Balls[0].position.y:
                if abs(self.Balls[1].position.y + self.Balls[1].velocity.y - self.Balls[0].position.y) < abs(self.Balls[1].position.y - self.Balls[0].position.y):
                    self.Balls[1].on_ball = True
                    self.Balls[1].doublejump = True
            self.interaction = True
            return interaction_speed
        else:
            self.interaction = False
        return 0, 0
    
    def ball_draw(self, surface):
        for ball in self.Balls:
            gfxdraw.aacircle(surface, round(ball.position.x), round(ball.position.y), round(ball.size), RED if ball.doublejump else DARK_RED)
            gfxdraw.filled_circle(surface, round(ball.position.x), round(ball.position.y), round(ball.size), RED if ball.doublejump else DARK_RED)
        
        icon_color = WHITE if self.Balls[0].size < 18 else BLACK
        pygame.draw.polygon(surface, icon_color, [self.Balls[0].position + delta for delta in arrow_icon])
        icon_color = WHITE if self.Balls[1].size < 18 else BLACK
        ball_control_w = font25.render("W", True, icon_color)
        ball_control_a = font25.render("A", True, icon_color)
        ball_control_s = font25.render("S", True, icon_color)
        ball_control_d = font25.render("D", True, icon_color)
        surface.blit(ball_control_w, self.Balls[1].position + (-ball_control_w.get_rect().width/2 + 0.5, -ball_control_w.get_rect().height        ))
        surface.blit(ball_control_a, self.Balls[1].position + (-ball_control_a.get_rect().width   - 5  , -ball_control_a.get_rect().height/2 + 0.5))
        surface.blit(ball_control_s, self.Balls[1].position + (-ball_control_s.get_rect().width/2 + 0.5,                                       3  ))
        surface.blit(ball_control_d, self.Balls[1].position + (                                     6.5, -ball_control_d.get_rect().height/2 + 0.5))

    def ball_animate(self, surface):
        if self.Balls[0].touch(self.Balls[1].position, self.Balls[0].size + self.Balls[1].size + 4):
            wave = False
            for i in range(2):
                if self.glow_radius >= 2 * self.Balls[i].size + math.ceil(20 // math.sqrt(2 * self.Balls[i].size)):
                    gfxdraw.circle(surface, int(self.Balls[i].position.x), int(self.Balls[i].position.y), int(self.Balls[i].size + 1), (194, 165, 0))
                else:
                    wave = True
            if wave:
                self.glow_radius += 1
                if self.glow_radius > 3:
                    arc_surface = pygame.Surface((750, 750))
                    arc_surface.set_colorkey(BLACK)
                    pygame.draw.circle(arc_surface, WHITE, [self.Balls[0].position.x + (self.Balls[1].position.x - self.Balls[0].position.x) * self.Balls[0].size / (self.Balls[0].size + self.Balls[1].size), self.Balls[0].position.y + (self.Balls[1].position.y - self.Balls[0].position.y) * self.Balls[0].size / (self.Balls[0].size + self.Balls[1].size)], self.glow_radius, width = math.ceil(20 // math.sqrt(self.glow_radius)))
                    surface.set_colorkey(RED)
                    maskscreen = pygame.mask.from_surface(surface)
                    maskscreen.invert()
                    surface.set_colorkey(DARK_RED)
                    maskscreen2 = pygame.mask.from_surface(surface)
                    maskscreen2.invert()
                    maskscreen.draw(maskscreen2, (0, 0))
                    maskarc = pygame.mask.from_surface(arc_surface).overlap_mask(maskscreen, (0, 0))
                    maskarc.to_surface(arc_surface, setcolor = (194, 165, 0))
                    surface.blit(arc_surface, [0, 0])
                    for i in range(2):
                        gfxdraw.arc(surface, int(self.Balls[i].position.x), int(self.Balls[i].position.y), int(self.Balls[i].size + 1), int(math.atan((self.Balls[0].position.y - self.Balls[1].position.y)/(self.Balls[0].position.x - self.Balls[1].position.x))*180/math.pi - math.pow((self.glow_radius*40/self.Balls[i].size), 1.46)/4) % 360 + (180 if self.Balls[i].position.x > self.Balls[i - 1].position.x else 0), int(math.atan((self.Balls[0].position.y - self.Balls[1].position.y)/(self.Balls[0].position.x - self.Balls[1].position.x))*180/math.pi + math.pow((self.glow_radius*40/self.Balls[i].size), 1.46)/4) % 360 + (180 if self.Balls[i].position.x > self.Balls[i - 1].position.x else 0), GOLD)
        else:
            self.glow_radius = 0

    def inflator(self, inflate):
        # if not inflate == 0 and (self.Balls[0].size > 4 or inflate < 0) and (self.Balls[1].size > 4 or inflate > 0) and (self.Balls[0].position.x - self.Balls[1].position.x) * (self.Balls[0].position.x - self.Balls[1].position.x) + (self.Balls[0].position.y - self.Balls[1].position.y) * (self.Balls[0].position.y - self.Balls[1].position.y) - (self.Balls[0].size + self.Balls[1].size) * (self.Balls[0].size + self.Balls[1].size) < 256:
        if not inflate == 0 and (self.Balls[0].size > 4 or inflate < 0) and (self.Balls[1].size > 4 or inflate > 0) and self.Balls[0].touch(self.Balls[1].position, self.Balls[0].size + self.Balls[1].size + 4):   
            d_size = [math.sqrt(self.Balls[0].weight() - inflate) - self.Balls[0].size, math.sqrt(self.Balls[1].weight() + inflate) - self.Balls[1].size]
            for i in range(2):
                if self.Balls[i].size + d_size[i] < 4:
                    d_size[i] = 4 - self.Balls[i].size
                    d_size[i-1] = math.sqrt(self.Balls[i].size * self.Balls[i].size - 16 + self.Balls[i - 1].size * self.Balls[i - 1].size) - self.Balls[i - 1].size
            self.Balls[0].size += d_size[0]
            self.Balls[1].size += d_size[1]
            temp_pos = [pygame.math.Vector2(self.Balls[0].position), pygame.math.Vector2(self.Balls[1].position)]
            # Try to keep the x_coords the same
            if temp_pos[0].y > temp_pos[1].y:
                temp_pos[0].y -= d_size[0]
                if self.Balls[0].size + self.Balls[1].size > abs(temp_pos[0].x - temp_pos[1].x):
                    temp_pos[1].y = temp_pos[0].y - math.sqrt((self.Balls[0].size + self.Balls[1].size) * (self.Balls[0].size + self.Balls[1].size) - (temp_pos[0].x - temp_pos[1].x) * (temp_pos[0].x - temp_pos[1].x))
            else: 
                temp_pos[1].y -= d_size[1]
                if self.Balls[0].size + self.Balls[1].size > abs(temp_pos[0].x - temp_pos[1].x):
                    temp_pos[0].y = temp_pos[1].y - math.sqrt((self.Balls[0].size + self.Balls[1].size) * (self.Balls[0].size + self.Balls[1].size) - (temp_pos[0].x - temp_pos[1].x) * (temp_pos[0].x - temp_pos[1].x))
            # Try to find a new location with small corrections, if that is impossible: fix the y_coords
            temp = self.inflator_correct(d_size, temp_pos, [self.Balls[0].size, self.Balls[1].size])
            if not temp:
                temp_pos = [pygame.math.Vector2(self.Balls[0].position), pygame.math.Vector2(self.Balls[1].position)]
                temp_pos[0].y -= min(d_size[0], 0)
                temp_pos[1].y -= min(d_size[1], 0)
                if self.Balls[0].size + self.Balls[1].size > abs(temp_pos[0].y - temp_pos[1].y):
                    if inflate > 0:
                        if temp_pos[0].x < temp_pos[1].x:
                            temp_pos[0].x = temp_pos[1].x - math.sqrt((self.Balls[0].size + self.Balls[1].size) * (self.Balls[0].size + self.Balls[1].size) - (temp_pos[0].y - temp_pos[1].y) * (temp_pos[0].y - temp_pos[1].y))
                        else:
                            temp_pos[0].x = temp_pos[1].x + math.sqrt((self.Balls[0].size + self.Balls[1].size) * (self.Balls[0].size + self.Balls[1].size) - (temp_pos[0].y - temp_pos[1].y) * (temp_pos[0].y - temp_pos[1].y))
                    else:
                        if temp_pos[0].x > temp_pos[1].x:
                            temp_pos[1].x = temp_pos[0].x - math.sqrt((self.Balls[0].size + self.Balls[1].size) * (self.Balls[0].size + self.Balls[1].size) - (temp_pos[0].y - temp_pos[1].y) * (temp_pos[0].y - temp_pos[1].y))
                        else:
                            temp_pos[1].x = temp_pos[0].x + math.sqrt((self.Balls[0].size + self.Balls[1].size) * (self.Balls[0].size + self.Balls[1].size) - (temp_pos[0].y - temp_pos[1].y) * (temp_pos[0].y - temp_pos[1].y))            
                temp = self.inflator_correct(d_size, temp_pos, [self.Balls[0].size, self.Balls[1].size])
                if not temp:
                    temp_pos = [pygame.math.Vector2(self.Balls[0].position), pygame.math.Vector2(self.Balls[1].position)]
                    temp_pos[0].y -= max(d_size[0], 0)
                    temp_pos[1].y -= max(d_size[1], 0)
                    if self.Balls[0].size + self.Balls[1].size > abs(temp_pos[0].y - temp_pos[1].y):
                        if inflate > 0:
                            if temp_pos[0].x < temp_pos[1].x:
                                temp_pos[0].x = temp_pos[1].x - math.sqrt((self.Balls[0].size + self.Balls[1].size) * (self.Balls[0].size + self.Balls[1].size) - (temp_pos[0].y - temp_pos[1].y) * (temp_pos[0].y - temp_pos[1].y))
                            else:
                                temp_pos[0].x = temp_pos[1].x + math.sqrt((self.Balls[0].size + self.Balls[1].size) * (self.Balls[0].size + self.Balls[1].size) - (temp_pos[0].y - temp_pos[1].y) * (temp_pos[0].y - temp_pos[1].y))
                        else:
                            if temp_pos[0].x > temp_pos[1].x:
                                temp_pos[1].x = temp_pos[0].x - math.sqrt((self.Balls[0].size + self.Balls[1].size) * (self.Balls[0].size + self.Balls[1].size) - (temp_pos[0].y - temp_pos[1].y) * (temp_pos[0].y - temp_pos[1].y))
                            else:
                                temp_pos[1].x = temp_pos[0].x + math.sqrt((self.Balls[0].size + self.Balls[1].size) * (self.Balls[0].size + self.Balls[1].size) - (temp_pos[0].y - temp_pos[1].y) * (temp_pos[0].y - temp_pos[1].y))            
                    # Check if there is space to inflate both balls, undo growth if there is no space
                    temp = self.inflator_correct(d_size, temp_pos, [self.Balls[0].size, self.Balls[1].size])
                    if not temp:
                        self.Balls[0].size -= d_size[0]
                        self.Balls[1].size -= d_size[1]
                        if self.output and not self.message_lock:
                            print("inflation impossible")
                            self.message_lock = True
                        return
            self.Balls[0].position, self.Balls[1].position = temp

    def inflator_correct(self, d_size, pos, size):
        # Returns False if the new situation is not allowed
        if isinstance(d_size, list):
            min_d = min(d_size, key = abs)
            min_d += PRECISION if min_d > 0 else -PRECISION
            max_d = max(d_size, key = abs)
            max_d += PRECISION if max_d > 0 else -PRECISION
            for c in [(0, 0), (0, PRECISION), (-min_d, PRECISION), (min_d, PRECISION), (-max_d, PRECISION), (max_d, PRECISION)]:
                if not self.beam_border_restrict([(pos[0] - c, size[0]), (pos[1] - c, size[1])]):
                    return pos[0] - c, pos[1] - c
        else:
            for c in [(0, 0), (0, PRECISION), (-PRECISION, PRECISION), (PRECISION, PRECISION), (-d_size + PRECISION, PRECISION), (d_size - PRECISION, PRECISION), (-d_size - PRECISION, PRECISION), (d_size + PRECISION, PRECISION)]:
                if not self.beam_border_restrict([(pos - c, size)]):
                    return pos - c
        return False
    
    def beam_border_restrict(self, test_cases):
        # Returns False if the new situation is allowed
        for test_case in test_cases:
            for beam in self.Beams:
                if beam.restrict(*test_case):
                    return True
            if self.border.restrict(*test_case):
                return True
        return False
    
    def shooter(self):
        # Fire the balls away from each other upon pressing the space bar
        if self.Balls[0].touch(self.Balls[1].position, self.Balls[0].size + self.Balls[1].size + 4):
            direction = pygame.math.Vector2.normalize(self.Balls[0].position - self.Balls[1].position)
            self.Balls[0].velocity += direction * self.Balls[1].size / 4
            self.Balls[1].velocity -= direction * self.Balls[0].size / 4
            self.Balls[self.Balls[0].position.y > self.Balls[1].position.y].doublejump = True
    
    def inflate(self):
        self.inflator((self.I[1] - self.I[0]) * INFLATE_SPEED)
        if self.drain:
            for deposit in self.Deposits:
                for ball in self.Balls:
                    deposit.proximity(ball)
    
    def physics(self):
        for i, ball in enumerate(self.Balls):
            ball.velocity.y += GRAVITY
            if self.L[i] and self.R[i]:
                ball.velocity.x = 0
            elif self.L[i]:
                ball.velocity.x = min(ball.velocity.x, -MOVE_SPEED)
            elif self.R[i]:
                ball.velocity.x = max(ball.velocity.x, MOVE_SPEED)
            elif abs(ball.velocity.x) < 0.1:
                ball.velocity.x = 0
            else:
                ball.velocity.x += (GRAVITY * (ball.velocity.x < 0) - GRAVITY * (ball.velocity.x > 0))
        
        for ball in self.Balls:
            ball.on_top = False
            ball.on_ball = False
            ball.velocity.update(self.border.proximity(*ball.velocity, ball))
            for beam in self.Beams:
                ball.velocity.update(beam.proximity_edge(*ball.velocity, ball))
            for beam in self.Beams:
                ball.velocity.update(beam.proximity_vertex(*ball.velocity, ball))

        interaction_speed = self.ball_interaction()
        
        if self.interaction:
            for ball in self.Balls:
                interaction_speed = self.border.proximity(*interaction_speed, ball)
                for beam in self.Beams:
                    interaction_speed = beam.proximity_edge(*interaction_speed, ball)
                for beam in self.Beams:
                    interaction_speed = beam.proximity_vertex(*interaction_speed, ball)
                
        temp_loc = [pygame.math.Vector2(self.Balls[0].position), pygame.math.Vector2(self.Balls[1].position)]
           
        magnetic_move = [False, False, False, False]
        for i, ball in enumerate(self.Balls):
            if self.interaction and abs(ball.position.x + interaction_speed[0] - self.Balls[i - 1].position.x) >= abs(ball.position.x + ball.velocity.x - self.Balls[i - 1].position.x):
                ball.position.x += interaction_speed[0]
                magnetic_move[2 * i] = True
            else: 
                ball.position.x += ball.velocity.x
                if self.interaction and self.beam_border_restrict([(ball.position, ball.size)]):
                    ball.position.x += interaction_speed[0] - ball.velocity.x
                    magnetic_move[2 * i] = True
            if self.interaction and abs(ball.position.y + interaction_speed[1] - self.Balls[i - 1].position.y) >= abs(ball.position.y + ball.velocity.y - self.Balls[i - 1].position.y):
                ball.position.y += interaction_speed[1]
                ball.velocity.y = interaction_speed[1]
                magnetic_move[2 * i + 1] = True      
            else: 
                ball.position.y += ball.velocity.y
                if self.interaction and self.beam_border_restrict([(ball.position, ball.size)]):
                    ball.position.y += interaction_speed[1] - ball.velocity.y
                    ball.velocity.y = interaction_speed[1]
                    magnetic_move[2 * i + 1] = True
        if magnetic_move == [True, True, True, True]:
            self.magnet()
                    
        for i, ball in enumerate(self.Balls):
            if self.beam_border_restrict([(ball.position, ball.size)]):
                ball.position = temp_loc[i]
    
        for goal in self.Goals:
            for ball in self.Balls:
                goal.proximity(ball, self.settings.animations[1])
     
        for teleporter in self.Teleporters:
            teleporter.proximity(self.Balls[0], self.Balls[1])
            teleporter.proximity(self.Balls[1], self.Balls[0])
            
        for remover in self.Removers:
            for ball in self.Balls:
                remover.proximity(ball)
        
    def magnet(self):
        # Make the balls touch each other for visual effects
        if self.Balls[0].on_top and self.Balls[1].on_top:
            try:
                magnetic = abs(self.Balls[0].position.x - self.Balls[1].position.x) - math.sqrt((self.Balls[0].size + self.Balls[1].size) * (self.Balls[0].size + self.Balls[1].size) - (self.Balls[0].position.y - self.Balls[1].position.y) * (self.Balls[0].position.y - self.Balls[1].position.y))
            except ValueError:
                return
            if self.Balls[0].position.x > self.Balls[1].position.x:
                self.Balls[0].position.x -= magnetic / 2
                self.Balls[1].position.x += magnetic / 2
            else:
                self.Balls[0].position.x += magnetic / 2
                self.Balls[1].position.x -= magnetic / 2
        else:
            direction = self.Balls[0].position - self.Balls[1].position
            magnetic = 1 - (self.Balls[0].size + self.Balls[1].size) / direction.length()            
            if self.Balls[0].on_top:
                self.Balls[0].position.x -= direction[0] * magnetic / 2
                self.Balls[1].position.x += direction[0] * magnetic / 2
                self.Balls[1].position.y += direction[1] * magnetic
            elif self.Balls[1].on_top:
                self.Balls[0].position.x -= direction[0] * magnetic / 2
                self.Balls[0].position.y -= direction[1] * magnetic
                self.Balls[1].position.x += direction[0] * magnetic / 2
            else:
                self.Balls[0].position -= direction * magnetic / 2
                self.Balls[1].position += direction * magnetic / 2
  
    def darkness_layer(self, frame):
        self.darkness_surface.fill(BLACK)
        if self.settings.dark_shape == 0:
            pygame.draw.circle(self.darkness_surface, GRAY, self.Balls[0].position, self.settings.dark_radius + 2, 2)
            pygame.draw.circle(self.darkness_surface, GRAY, self.Balls[1].position, self.settings.dark_radius + 2, 2)
            pygame.draw.circle(self.darkness_surface, WHITE, self.Balls[0].position, self.settings.dark_radius)
            pygame.draw.circle(self.darkness_surface, WHITE, self.Balls[1].position, self.settings.dark_radius)
        elif self.settings.dark_shape == 1:
            pygame.draw.rect(self.darkness_surface, GRAY, [self.Balls[0].position.x - self.settings.dark_radius - 2, self.Balls[0].position.y - self.settings.dark_radius - 2, 2 * self.settings.dark_radius + 4, 2 * self.settings.dark_radius + 4], 2)
            pygame.draw.rect(self.darkness_surface, GRAY, [self.Balls[1].position.x - self.settings.dark_radius - 2, self.Balls[1].position.y - self.settings.dark_radius - 2, 2 * self.settings.dark_radius + 4, 2 * self.settings.dark_radius + 4], 2)
            pygame.draw.rect(self.darkness_surface, WHITE, [self.Balls[0].position.x - self.settings.dark_radius, self.Balls[0].position.y - self.settings.dark_radius, 2 * self.settings.dark_radius, 2 * self.settings.dark_radius])
            pygame.draw.rect(self.darkness_surface, WHITE, [self.Balls[1].position.x - self.settings.dark_radius, self.Balls[1].position.y - self.settings.dark_radius, 2 * self.settings.dark_radius, 2 * self.settings.dark_radius])
        elif self.settings.dark_shape == 2:
            pygame.draw.polygon(self.darkness_surface, GRAY, [(self.Balls[0].position.x - self.settings.dark_radius - 2, self.Balls[0].position.y), (self.Balls[0].position.x, self.Balls[0].position.y - self.settings.dark_radius - 2), (self.Balls[0].position.x + self.settings.dark_radius + 2, self.Balls[0].position.y), (self.Balls[0].position.x, self.Balls[0].position.y + self.settings.dark_radius + 2)], 2)
            pygame.draw.polygon(self.darkness_surface, GRAY, [(self.Balls[1].position.x - self.settings.dark_radius - 2, self.Balls[1].position.y), (self.Balls[1].position.x, self.Balls[1].position.y - self.settings.dark_radius - 2), (self.Balls[1].position.x + self.settings.dark_radius + 2, self.Balls[1].position.y), (self.Balls[1].position.x, self.Balls[1].position.y + self.settings.dark_radius + 2)], 2)                
            pygame.draw.polygon(self.darkness_surface, WHITE, [(self.Balls[0].position.x - self.settings.dark_radius, self.Balls[0].position.y), (self.Balls[0].position.x, self.Balls[0].position.y - self.settings.dark_radius), (self.Balls[0].position.x + self.settings.dark_radius, self.Balls[0].position.y), (self.Balls[0].position.x, self.Balls[0].position.y + self.settings.dark_radius)])
            pygame.draw.polygon(self.darkness_surface, WHITE, [(self.Balls[1].position.x - self.settings.dark_radius, self.Balls[1].position.y), (self.Balls[1].position.x, self.Balls[1].position.y - self.settings.dark_radius), (self.Balls[1].position.x + self.settings.dark_radius, self.Balls[1].position.y), (self.Balls[1].position.x, self.Balls[1].position.y + self.settings.dark_radius)])
        elif self.settings.dark_shape == 3:
            x = math.sqrt(3)/2
            pygame.draw.polygon(self.darkness_surface, GRAY, [(self.Balls[0].position.x, self.Balls[0].position.y - self.settings.dark_radius - 2), (self.Balls[0].position.x - x * (self.settings.dark_radius + 2), self.Balls[0].position.y + 0.5 * self.settings.dark_radius + 1), (self.Balls[0].position.x + x * (self.settings.dark_radius + 2), self.Balls[0].position.y + 0.5 * self.settings.dark_radius + 1)], 2)
            pygame.draw.polygon(self.darkness_surface, GRAY, [(self.Balls[1].position.x, self.Balls[1].position.y + self.settings.dark_radius + 2), (self.Balls[1].position.x - x * (self.settings.dark_radius + 2), self.Balls[1].position.y - 0.5 * self.settings.dark_radius - 1), (self.Balls[1].position.x + x * (self.settings.dark_radius + 2), self.Balls[1].position.y - 0.5 * self.settings.dark_radius - 1)], 2)
            pygame.draw.polygon(self.darkness_surface, WHITE, [(self.Balls[0].position.x, self.Balls[0].position.y - self.settings.dark_radius), (self.Balls[0].position.x - x * self.settings.dark_radius, self.Balls[0].position.y + 0.5 * self.settings.dark_radius), (self.Balls[0].position.x + x * self.settings.dark_radius, self.Balls[0].position.y + 0.5 * self.settings.dark_radius)])
            pygame.draw.polygon(self.darkness_surface, WHITE, [(self.Balls[1].position.x, self.Balls[1].position.y + self.settings.dark_radius), (self.Balls[1].position.x - x * self.settings.dark_radius, self.Balls[1].position.y - 0.5 * self.settings.dark_radius), (self.Balls[1].position.x + x * self.settings.dark_radius, self.Balls[1].position.y - 0.5 * self.settings.dark_radius)])
        elif self.settings.dark_shape == 4:
            pygame.draw.polygon(self.darkness_surface, GRAY, [(self.Balls[0].position.x + (self.settings.dark_radius + 2) * math.cos(frame/100                ), self.Balls[0].position.y + (self.settings.dark_radius + 2) * math.sin(frame/100                )), (self.Balls[0].position.x + (self.settings.dark_radius + 2) * math.cos(frame/100 +     math.pi/5) / 3, self.Balls[0].position.y + (self.settings.dark_radius + 2) * math.sin(frame/100 +     math.pi/5) / 3),
                                                              (self.Balls[0].position.x + (self.settings.dark_radius + 2) * math.cos(frame/100 + 2 * math.pi/5), self.Balls[0].position.y + (self.settings.dark_radius + 2) * math.sin(frame/100 + 2 * math.pi/5)), (self.Balls[0].position.x + (self.settings.dark_radius + 2) * math.cos(frame/100 + 3 * math.pi/5) / 3, self.Balls[0].position.y + (self.settings.dark_radius + 2) * math.sin(frame/100 + 3 * math.pi/5) / 3),
                                                              (self.Balls[0].position.x + (self.settings.dark_radius + 2) * math.cos(frame/100 + 4 * math.pi/5), self.Balls[0].position.y + (self.settings.dark_radius + 2) * math.sin(frame/100 + 4 * math.pi/5)), (self.Balls[0].position.x + (self.settings.dark_radius + 2) * math.cos(frame/100 + 5 * math.pi/5) / 3, self.Balls[0].position.y + (self.settings.dark_radius + 2) * math.sin(frame/100 + 5 * math.pi/5) / 3),
                                                              (self.Balls[0].position.x + (self.settings.dark_radius + 2) * math.cos(frame/100 + 6 * math.pi/5), self.Balls[0].position.y + (self.settings.dark_radius + 2) * math.sin(frame/100 + 6 * math.pi/5)), (self.Balls[0].position.x + (self.settings.dark_radius + 2) * math.cos(frame/100 + 7 * math.pi/5) / 3, self.Balls[0].position.y + (self.settings.dark_radius + 2) * math.sin(frame/100 + 7 * math.pi/5) / 3),
                                                              (self.Balls[0].position.x + (self.settings.dark_radius + 2) * math.cos(frame/100 + 8 * math.pi/5), self.Balls[0].position.y + (self.settings.dark_radius + 2) * math.sin(frame/100 + 8 * math.pi/5)), (self.Balls[0].position.x + (self.settings.dark_radius + 2) * math.cos(frame/100 + 9 * math.pi/5) / 3, self.Balls[0].position.y + (self.settings.dark_radius + 2) * math.sin(frame/100 + 9 * math.pi/5) / 3)], 2)
            pygame.draw.polygon(self.darkness_surface, GRAY, [(self.Balls[1].position.x + (self.settings.dark_radius + 2) * math.sin(frame/100                ), self.Balls[1].position.y + (self.settings.dark_radius + 2) * math.cos(frame/100                )), (self.Balls[1].position.x + (self.settings.dark_radius + 2) * math.sin(frame/100 +     math.pi/5) / 3, self.Balls[1].position.y + (self.settings.dark_radius + 2) * math.cos(frame/100 +     math.pi/5) / 3),
                                                              (self.Balls[1].position.x + (self.settings.dark_radius + 2) * math.sin(frame/100 + 2 * math.pi/5), self.Balls[1].position.y + (self.settings.dark_radius + 2) * math.cos(frame/100 + 2 * math.pi/5)), (self.Balls[1].position.x + (self.settings.dark_radius + 2) * math.sin(frame/100 + 3 * math.pi/5) / 3, self.Balls[1].position.y + (self.settings.dark_radius + 2) * math.cos(frame/100 + 3 * math.pi/5) / 3),
                                                              (self.Balls[1].position.x + (self.settings.dark_radius + 2) * math.sin(frame/100 + 4 * math.pi/5), self.Balls[1].position.y + (self.settings.dark_radius + 2) * math.cos(frame/100 + 4 * math.pi/5)), (self.Balls[1].position.x + (self.settings.dark_radius + 2) * math.sin(frame/100 + 5 * math.pi/5) / 3, self.Balls[1].position.y + (self.settings.dark_radius + 2) * math.cos(frame/100 + 5 * math.pi/5) / 3),
                                                              (self.Balls[1].position.x + (self.settings.dark_radius + 2) * math.sin(frame/100 + 6 * math.pi/5), self.Balls[1].position.y + (self.settings.dark_radius + 2) * math.cos(frame/100 + 6 * math.pi/5)), (self.Balls[1].position.x + (self.settings.dark_radius + 2) * math.sin(frame/100 + 7 * math.pi/5) / 3, self.Balls[1].position.y + (self.settings.dark_radius + 2) * math.cos(frame/100 + 7 * math.pi/5) / 3),
                                                              (self.Balls[1].position.x + (self.settings.dark_radius + 2) * math.sin(frame/100 + 8 * math.pi/5), self.Balls[1].position.y + (self.settings.dark_radius + 2) * math.cos(frame/100 + 8 * math.pi/5)), (self.Balls[1].position.x + (self.settings.dark_radius + 2) * math.sin(frame/100 + 9 * math.pi/5) / 3, self.Balls[1].position.y + (self.settings.dark_radius + 2) * math.cos(frame/100 + 9 * math.pi/5) / 3)], 2)
            pygame.draw.polygon(self.darkness_surface, WHITE, [(self.Balls[0].position.x + self.settings.dark_radius * math.cos(frame/100                ), self.Balls[0].position.y + self.settings.dark_radius * math.sin(frame/100                )), (self.Balls[0].position.x + self.settings.dark_radius * math.cos(frame/100 +     math.pi/5) / 3, self.Balls[0].position.y + self.settings.dark_radius * math.sin(frame/100 +     math.pi/5) / 3),
                                                               (self.Balls[0].position.x + self.settings.dark_radius * math.cos(frame/100 + 2 * math.pi/5), self.Balls[0].position.y + self.settings.dark_radius * math.sin(frame/100 + 2 * math.pi/5)), (self.Balls[0].position.x + self.settings.dark_radius * math.cos(frame/100 + 3 * math.pi/5) / 3, self.Balls[0].position.y + self.settings.dark_radius * math.sin(frame/100 + 3 * math.pi/5) / 3),
                                                               (self.Balls[0].position.x + self.settings.dark_radius * math.cos(frame/100 + 4 * math.pi/5), self.Balls[0].position.y + self.settings.dark_radius * math.sin(frame/100 + 4 * math.pi/5)), (self.Balls[0].position.x + self.settings.dark_radius * math.cos(frame/100 + 5 * math.pi/5) / 3, self.Balls[0].position.y + self.settings.dark_radius * math.sin(frame/100 + 5 * math.pi/5) / 3),
                                                               (self.Balls[0].position.x + self.settings.dark_radius * math.cos(frame/100 + 6 * math.pi/5), self.Balls[0].position.y + self.settings.dark_radius * math.sin(frame/100 + 6 * math.pi/5)), (self.Balls[0].position.x + self.settings.dark_radius * math.cos(frame/100 + 7 * math.pi/5) / 3, self.Balls[0].position.y + self.settings.dark_radius * math.sin(frame/100 + 7 * math.pi/5) / 3),
                                                               (self.Balls[0].position.x + self.settings.dark_radius * math.cos(frame/100 + 8 * math.pi/5), self.Balls[0].position.y + self.settings.dark_radius * math.sin(frame/100 + 8 * math.pi/5)), (self.Balls[0].position.x + self.settings.dark_radius * math.cos(frame/100 + 9 * math.pi/5) / 3, self.Balls[0].position.y + self.settings.dark_radius * math.sin(frame/100 + 9 * math.pi/5) / 3)])
            pygame.draw.polygon(self.darkness_surface, WHITE, [(self.Balls[1].position.x + self.settings.dark_radius * math.sin(frame/100                ), self.Balls[1].position.y + self.settings.dark_radius * math.cos(frame/100                )), (self.Balls[1].position.x + self.settings.dark_radius * math.sin(frame/100 +     math.pi/5) / 3, self.Balls[1].position.y + self.settings.dark_radius * math.cos(frame/100 +     math.pi/5) / 3),
                                                               (self.Balls[1].position.x + self.settings.dark_radius * math.sin(frame/100 + 2 * math.pi/5), self.Balls[1].position.y + self.settings.dark_radius * math.cos(frame/100 + 2 * math.pi/5)), (self.Balls[1].position.x + self.settings.dark_radius * math.sin(frame/100 + 3 * math.pi/5) / 3, self.Balls[1].position.y + self.settings.dark_radius * math.cos(frame/100 + 3 * math.pi/5) / 3),
                                                               (self.Balls[1].position.x + self.settings.dark_radius * math.sin(frame/100 + 4 * math.pi/5), self.Balls[1].position.y + self.settings.dark_radius * math.cos(frame/100 + 4 * math.pi/5)), (self.Balls[1].position.x + self.settings.dark_radius * math.sin(frame/100 + 5 * math.pi/5) / 3, self.Balls[1].position.y + self.settings.dark_radius * math.cos(frame/100 + 5 * math.pi/5) / 3),
                                                               (self.Balls[1].position.x + self.settings.dark_radius * math.sin(frame/100 + 6 * math.pi/5), self.Balls[1].position.y + self.settings.dark_radius * math.cos(frame/100 + 6 * math.pi/5)), (self.Balls[1].position.x + self.settings.dark_radius * math.sin(frame/100 + 7 * math.pi/5) / 3, self.Balls[1].position.y + self.settings.dark_radius * math.cos(frame/100 + 7 * math.pi/5) / 3),
                                                               (self.Balls[1].position.x + self.settings.dark_radius * math.sin(frame/100 + 8 * math.pi/5), self.Balls[1].position.y + self.settings.dark_radius * math.cos(frame/100 + 8 * math.pi/5)), (self.Balls[1].position.x + self.settings.dark_radius * math.sin(frame/100 + 9 * math.pi/5) / 3, self.Balls[1].position.y + self.settings.dark_radius * math.cos(frame/100 + 9 * math.pi/5) / 3)])
            
    def mouse(self, mouse_pos):
        if self.drag:
            self.update_draw_surface(mouse_pos)
        
        if self.started:
            if self.mouse_actions and self.mouse_actions[-1][0] == mouse_pos:
                self.mouse_actions[-1][1] += 1
            else:
                self.mouse_actions.append([mouse_pos, 1])

        if self.settings.darkness and self.darkness_surface.get_at(pygame.mouse.get_pos()) != WHITE:
            return None
            
        return mouse_pos

    def redraw(self, surface, mouse_pos):
        if self.creator:
            surface.fill(BLACK)
            for beam in self.Beams:
                beam.draw(surface, "full", True)
        else:
            surface.blit(self.beam_surface, (0, 0))
            
        for goal in self.Goals:
            goal.fill_overlay()
            goal.draw(surface, "back")
        for deposit in self.Deposits:
            deposit.draw(surface, "back")
        for teleporter in self.Teleporters:
            teleporter.update_colors(self.dummy_count)
            teleporter.draw(surface, "back", self.dummy_count)
        for remover in self.Removers:
            remover.draw(surface, "back")

        self.ball_draw(surface)

        for goal in self.Goals:
            goal.draw(surface, "front")
        for deposit in self.Deposits:
            deposit.draw(surface, "front")
        for teleporter in self.Teleporters:
            teleporter.draw(surface, "front", self.dummy_count)
        for remover in self.Removers:
            remover.draw(surface, "front", bool(self.creator), self.dummy_count)
    
        if self.settings.animations[0]:
            self.ball_animate(surface)
    
        if mouse_pos:
            for goal in self.Goals:
                if goal.touch(mouse_pos):
                    if self.settings.animations[1]:
                        goal.animated = True
                    break
            else:
                for teleporter in self.Teleporters:
                    if teleporter.touch(mouse_pos):
                        teleporter.animate(surface, self.settings.animations[2])
                        break
                else:
                    for remover in self.Removers:
                        if remover.touch(mouse_pos):
                            remover.animate(surface, self.settings.animations[3])
                        elif remover.sparks and remover.sparks.progress >= 38:
                            remover.sparks = None
        
        if self.settings.darkness:
            surface.blit(self.darkness_surface, (0, 0))
                      
        if self.paused:
            paused_text = font100.render("paused", True, RED)
            surface.blit(paused_text, [375 - paused_text.get_rect().width/2, 375 - paused_text.get_rect().height/2])
        
        # Calculate and show air and time information        
        if self.settings.show_info_mode >= 2 or (self.settings.show_info_mode == 1 and mouse_pos[1] > 60):
            time_text = font25.render("Level creation mode" if self.creator else f"Time: {self.minutes:02}:{self.seconds:02} ({self.frame_count}, invalid)" if self.invalid else f"Time: {self.minutes:02}:{self.seconds:02} ({self.frame_count})", True, WHITE)
            air_text = font25.render("Air: {0:0g} + {1:0g} = {2:0g}".format(self.Balls[0].weight() - 16, self.Balls[1].weight() - 16, self.Balls[0].weight() + self.Balls[1].weight() - 32), True, WHITE)
            if not (self.settings.show_info_mode == 2 and mouse_pos and air_text.get_rect().collidepoint(mouse_pos[0] + air_text.get_rect().width - 730, mouse_pos[1] - 38)):
                surface.blit(air_text, [730 - air_text.get_rect().width, 38])
            if not (self.settings.show_info_mode == 2 and mouse_pos and time_text.get_rect().collidepoint(mouse_pos[0] - 20, mouse_pos[1] - 38)):
                surface.blit(time_text, [20, 38])

        # Introduction text
        if 0 < self.level_count <= 3 and self.settings.show_intro_text:
            for i, text in enumerate(INTRO_TEXT[self.level_count - 1].splitlines()):
                intro_text = (font25.render(text, True, WHITE))
                if self.creator:
                    intro_text.set_alpha(127)
                surface.blit(intro_text, [20, 60 + 20 * i])
        
        surface.blit(self.draw_surface, (0,0))
                
    def delay(self, host, surface, clock, mouse_pos, frames, rate):
        for _ in range(frames):
            self.dummy_count += 1
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    print("Best session times:")
                    print(self.times)
                    self.run = False
                    return
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        print("Best session times:")
                        print(self.times)
                        self.run = False
                        return
                    elif event.key == pygame.K_ESCAPE:
                        return
            host.redraw(surface, mouse_pos)
            pygame.display.flip()
            clock.tick(rate)
            
    def completion(self, level, frame_count):
        if not self.times.get(self.settings.level_names[level]) or frame_count < self.times.get(self.settings.level_names[level]):
            self.times[self.settings.level_names[level]] = frame_count
            if not self.settings.highscores.get(self.settings.level_names[level]) or frame_count < self.settings.highscores.get(self.settings.level_names[level]):
                if self.settings.highscores.get(self.settings.level_names[level]):
                    print("New highscore!, frames: {0:02}, old frames: {1:02}". format(frame_count, self.settings.highscores.get(self.settings.level_names[level])))
                    self.settings.global_profile_scores[self.settings.profile][1] += frame_count - self.settings.highscores.get(self.settings.level_names[level])
                else:
                    print("New highscore!, frames: {0:02}". format(frame_count))
                    self.settings.global_profile_scores[self.settings.profile][0] += 1
                    self.settings.global_profile_scores[self.settings.profile][1] += frame_count
                self.settings.highscores[self.settings.level_names[level]] = frame_count
                for score in self.settings.global_highscores[self.settings.level_names[level]]:
                    if score[0] == self.settings.profile:
                        self.settings.global_highscores[self.settings.level_names[level]].remove(score)
                        break
                self.settings.global_highscores[self.settings.level_names[level]].append((self.settings.profile, frame_count))
                self.settings.global_highscores[self.settings.level_names[level]].sort(key = lambda x:x[1])
                with open(f"game_data/profiles/{self.settings.profile}/highscores/highscores.txt", "w") as file:
                    print(self.settings.highscores, file = file)
                with open(f"game_data/profiles/{self.settings.profile}/highscores/{self.settings.level_names[level]}.txt", "w") as file:
                    print('[[', end  = '', file = file)
                    for i, y in enumerate(self.actions):
                        print('[' + ', '.join(y) + ']', end = '', file = file)
                        if i < len(self.actions) - 1:
                            print(',', file = file)
                        else:
                            print('],\n\n[', end = '', file = file)
                            
                    for i, m in enumerate(self.mouse_actions):
                        print(m, end = '', file = file)
                        if i < len(self.mouse_actions) - 1:
                            print(',', file = file)
                        else:
                            print(']]', end = '', file = file)
            
    def save_level(self, filename):
        with open(filename, "w") as file:
            print("[" + ', '.join(f"Ball({int(ball.position.x)}, {int(ball.position.y)}, {int(ball.size)})" for ball in self.Balls) + "],", file = file)
            print("[" + ', '.join(f"Beam({beam.left}, {beam.right}, {beam.up}, {beam.down}, {beam.remover})" for beam in self.Beams) + "],", file = file)
            print("[" + ', '.join(f"Goal({goal.center_x}, {goal.center_y}, {goal.radius}, {goal.air})" for goal in self.Goals) + "],", file = file)
            print("[" + ', '.join(f"Teleporter({teleporter.center_x}, {teleporter.center_y}, {teleporter.radius}, {int(teleporter.destination.x)}, {int(teleporter.destination.y)})" for teleporter in self.Teleporters) + "],", file = file)
            print("[" + ', '.join(f"Remover({remover.center_x}, {remover.center_y}, {remover.radius}, {remover.id})" for remover in self.Removers) + "],", file = file)
            print("[" + ', '.join(f"Deposit({deposit.center_x}, {deposit.center_y}, {deposit.radius}, {deposit.air})" for deposit in self.Deposits) + "]", file = file)
        print(f"level saved as {filename}")
        self.settings.update_levels()
        
    def create_background(self):
        if self.settings.background == 0:
            self.background_surface.fill(BLACK)
        elif self.settings.background < 10:
            self.background_surface.fill(self.color_set[self.settings.background - 1])
            shades = np.repeat(self.rng.integers(0, 31, 1440)[..., np.newaxis], 3, axis = 1)
            outlim = np.repeat(750 + np.tan(np.radians(np.arange(360) % 45)) * 750, 4)
            select = self.rng.integers(0, outlim, 1440)
            for i, (shade, s, x) in enumerate(zip(shades, outlim, select)):
                if i % 4 == 0:
                    pygame.draw.line(self.background_surface, shade, (s - x, 0), (750 - x, 750), 4)
                elif i % 4 == 1:
                    pygame.draw.line(self.background_surface, shade, (750 - s + x, 0), (x, 750), 4)
                elif i % 4 == 2:
                    pygame.draw.line(self.background_surface, shade, (0, s - x), (750, 750 - x), 4)
                else:
                    pygame.draw.line(self.background_surface, shade, (0, 750 - s + x), (750, x), 4)
        else:
            color_blobs = self.rng.choice([0, 10000], size = (750, 750), p = [0.9998, 0.0002])
            color_array = self.rng.integers(0, 31, (750, 750, 3))
            np.add(color_array, color_blobs[..., np.newaxis], out = color_array)
            gaussian_filter(color_array, (3, 3, 0), output = color_array)
            np.minimum(color_array, self.color_set[self.settings.background - 10][:3], out = color_array)
            self.background_surface = pygame.surfarray.make_surface(color_array)

    def create_beam_surface(self):
        color_ranges = np.array([[0, 63], [0, 63], [0, 255]])
        color_array = self.rng.integers(color_ranges[:, 0], color_ranges[:, 1], (750, 750, 3))
        gaussian_filter(color_array, (8, 2, 0), order = 0, output = color_array)
        self.beam_surface_textured = pygame.surfarray.make_surface(color_array)
                
    def update_beam_surface(self, remover_id):           
        if type(remover_id) is int:
            self.Removers = [remover for remover in self.Removers if remover_id != remover.id or (self.creator.editor.parent == remover and self.creator.editor.kill(False))] if self.creator and self.creator.editor and isinstance(self.creator.editor.parent, Remover) else [remover for remover in self.Removers if remover_id != remover.id]
            self.Beams = [beam for beam in self.Beams if remover_id not in beam.remover or (self.output and beam.draw(self.beam_surface_blue, "full", False, BLACK)) or (self.creator.editor.parent == beam and self.creator.editor.kill(False))] if self.creator and self.creator.editor and isinstance(self.creator.editor.parent, Beam) else [beam for beam in self.Beams if remover_id not in beam.remover or (self.output and beam.draw(self.beam_surface_blue, "full", False, BLACK))]
        elif remover_id:
            self.beam_surface_blue.fill(BLACK)
            for beam in self.Beams:
                beam.draw(self.beam_surface_blue, "full")
        if self.output:
            mask = pygame.mask.from_surface(self.beam_surface_blue)
            if self.settings.textured_beams:
                mask.to_surface(surface = self.beam_surface, setsurface = self.beam_surface_textured, unsetsurface = self.background_surface)
                bg_mask = mask.copy()
                bg_mask.invert()
                edge_mask = mask.overlap_mask(bg_mask, (-2, -2))
                edge_mask.draw(mask.overlap_mask(bg_mask, (-2, 2)), (0, 0))
                edge_mask.draw(mask.overlap_mask(bg_mask, (2, -2)), (0, 0))
                edge_mask.draw(mask.overlap_mask(bg_mask, (2, 2)), (0, 0))
                edge_surf = edge_mask.to_surface(setcolor = (20, 20, 20), unsetcolor = BLACK)
                edge_surf.set_colorkey(BLACK)
                self.beam_surface.blit(edge_surf, (0, 0), special_flags = BLEND_RGB_ADD)
            else:
                mask.to_surface(surface = self.beam_surface, setcolor = BLUE, unsetsurface = self.background_surface)

    def update_draw_surface(self, mouse_pos):
        if self.prev_mouse_pos and mouse_pos != self.prev_mouse_pos:
            pygame.draw.line(self.draw_surface, self.color_set[self.path_color_id], self.prev_mouse_pos, mouse_pos, 2)
        self.prev_mouse_pos = mouse_pos