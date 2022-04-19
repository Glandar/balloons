import pygame
from colors import GRAY, WHITE, RED, ORANGE, BLACK #@UnresolvedImport
from constants import FRAME_RATE #@UnresolvedImport
from controls import controls, replay_blitmap #@UnresolvedImport
from fonts import font20, font25 #@UnresolvedImport
from ball import Ball #@UnusedImport #@UnresolvedImport
from beam import Beam #@UnusedImport #@UnresolvedImport
from goal import Goal #@UnusedImport #@UnresolvedImport
from teleporter import Teleporter #@UnusedImport #@UnresolvedImport
from remover import Remover #@UnusedImport #@UnresolvedImport
from deposit import Deposit #@UnusedImport #@UnresolvedImport
import overlay

class Replay():
    def __init__(self, host, settings, replay_actions, replay_mouse, end = None, start = 0):
        self.host = host
        self.settings = settings
        self.replay_blits = []
        self.replay_mouse = replay_mouse
        if start:
            self.replay_actions = [[replay_action[0] - start, *replay_action[1:]] for replay_action in replay_actions if replay_action[0] >= start]
            self.end = end - start
            while self.replay_mouse[0][1] < start:
                start -= self.replay_mouse[0][1]
                self.replay_mouse.pop(0)
            self.replay_mouse[0][1] -= start
        else:
            self.replay_actions = replay_actions
            self.end = end
    
    def loop(self, screen, clock):                
        screen_height = screen.get_height()
        if screen_height != 800:
            screen = pygame.display.set_mode([750, 800], screen.get_flags())
        self.level(self.host.level_count)
        self.host.delay(self, screen, clock, self.replay_mouse[0][0], self.settings.replay_frame_rate, self.settings.replay_frame_rate)
        
        while self.host.run and self.host.replay:
            self.host.dummy_count += 1
            
            # Event Processing
            if self.settings.darkness:
                self.host.darkness_layer(self.host.dummy_count)
            mouse_pos = self.mouse(pygame.mouse.get_pos())
            self.redraw(screen, mouse_pos)
        
            self.replay_blits, screen, clock = self.replay_handling(self.replay_blits, screen, clock, mouse_pos)
            if not self.host.run or not self.host.replay:
                break
        
            if self.host.paused:
                pygame.display.flip()
                clock.tick(self.settings.replay_frame_rate)
                continue
        
            # Game logic
            self.host.inflate()
            self.host.physics()
        
            # Go to the next level if the goals are achieved
            for goal in self.host.Goals:
                if goal.air > 0:
                    break
            else:
                if not self.host.creator:
                    self.host.replay = None
                    self.host.level(self.host.level_count, message_start = False)
                    break
            
            if self.end and self.host.frame_count == self.end:
                self.host.replay = None
                print(f"Continuing from replay (frame {self.host.frame_count})")
                screen, clock = self.host.event_handling([replay_event(pygame.KEYUP, key) for key, pressed in zip([pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d, pygame.K_DOWN, pygame.K_s], self.host.L + self.host.R + self.host.I) if pressed], screen, clock, mouse_pos)
                self.host.started = any(ball.velocity for ball in self.host.Balls)
                break
            
            # Update frame
            self.host.frame_count += 1
            self.host.minutes = self.host.frame_count // FRAME_RATE // 60
            self.host.seconds = self.host.frame_count // FRAME_RATE % 60
            pygame.display.flip()
            clock.tick(self.settings.replay_frame_rate)
            
        if screen_height != 800:
            screen = pygame.display.set_mode([750, 750], screen.get_flags())
        return screen, clock
    
    def level(self, level_no):
        if self.end:
            print(f"Replaying the current session for level {level_no} ({self.end} frames)")
        else:
            print(f"Replaying the highscore for level {level_no} ({self.settings.highscores.get(self.settings.level_names[level_no])} frames)")
        if self.host.creator:
            self.host.creator.pin_frame = 0
            self.host.open("creator/pinned")
        else:
            self.host.open(self.settings.level_names[level_no])
        self.host.reset()
        
    def replay_handling(self, blits, screen, clock, mouse_pos):    
        replay_events = []
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                print("Best session times:")
                print(self.host.times)
                self.host.run = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.host.drag = True
            elif event.type == pygame.MOUSEBUTTONUP:
                self.host.prev_mouse_pos = None
                self.host.drag = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    print("Best session times:")
                    print(self.host.times)
                    self.host.run = False
                elif event.key == pygame.K_f:
                    self.settings.frame = not self.settings.frame
                    screen = pygame.display.set_mode([750, screen.get_height()], 0 if self.settings.frame else pygame.NOFRAME)     
                elif event.key == pygame.K_ESCAPE:
                    self.host.paused = not self.host.paused
                elif event.key == pygame.K_m:
                    self.host.overlay = overlay.Overlay(self.host, self.settings, self.host.level_count, -1)
                    screen, clock = self.host.overlay.loop(screen, clock)
                elif event.key == pygame.K_l:
                    self.host.overlay = overlay.Overlay(self.host, self.settings, self.host.level_count, max((self.host.level_count - 1) // 30, 0))
                    screen, clock = self.host.overlay.loop(screen, clock)
                if event.key == pygame.K_UP:
                    self.settings.replay_frame_rate += 10
                elif event.key == pygame.K_DOWN:
                    self.settings.replay_frame_rate = max(self.settings.replay_frame_rate - 10, 10)
                elif event.key == pygame.K_j:
                    self.host.replay = None
                    self.host.level(self.host.level_count)
                elif event.key == pygame.K_k:
                    self.host.replay = None
                    print(f"Playing from replay (frame {self.host.frame_count}, session invalid)")
                    self.host.invalid = True
                    for key, pressed in zip([pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d, pygame.K_DOWN, pygame.K_s], self.host.L + self.host.R + self.host.I):
                        if pressed:
                            replay_events.append(replay_event(pygame.KEYUP, key))
                    self.host.started = any(ball.velocity for ball in self.host.Balls)
                elif event.key == pygame.K_F4:
                    self.host.path_color_id = (self.host.path_color_id + 1) % 6
                elif event.key == pygame.K_F5:
                    self.host.draw_surface.fill(BLACK)
                    
        if self.replay_actions and self.replay_actions[0][0] == self.host.frame_count:
            del self.replay_actions[0][0]
            for a in self.replay_actions[0]:
                if a > 0:
                    replay_events.append(replay_event(pygame.KEYDOWN, a))
                    blits.append(a)
                else:
                    replay_events.append(replay_event(pygame.KEYUP, -a))
                    if -a in blits:
                        blits.remove(-a)
            del self.replay_actions[0]

        if replay_events:
            screen, clock = self.host.event_handling(replay_events, screen, clock, mouse_pos)
        
        return blits, screen, clock

    def mouse(self, mouse_pos):
        if self.host.drag:
            self.host.update_draw_surface(mouse_pos)
        
        if self.replay_mouse:
            if self.replay_mouse[0][1] > 1:
                mouse_pos = self.replay_mouse[0][0]
                self.replay_mouse[0][1] -= 1
            else:
                mouse_pos = self.replay_mouse.pop(0)[0]
                
        if self.host.mouse_actions and self.host.mouse_actions[-1][0] == mouse_pos:
            self.host.mouse_actions[-1][1] += 1
        else:
            self.host.mouse_actions.append([mouse_pos, 1])
            
        return mouse_pos
    
    def redraw(self, surface, mouse_pos):
        self.host.redraw(surface, pygame.mouse.get_pos())
        if self.end:
            rh_text = font25.render(f"Replaying current session ({(self.end) - self.host.frame_count}, {self.settings.replay_frame_rate}/s)", True, RED)
        else:
            rh_text = font25.render(f"Replaying highscore ({(self.settings.highscores.get(self.settings.level_names[self.host.level_count])) - self.host.frame_count}, {self.settings.replay_frame_rate}/s)", True, RED)
        surface.blit(rh_text, [375 - rh_text.get_rect().width/2, 38])
        surface.fill(GRAY, [0, 750, 750, 800])
        for c in controls:
            if c in self.replay_blits:
                surface.blit((font20.render(replay_blitmap[c][0], True, RED)), replay_blitmap[c][1])
            else:
                surface.blit((font20.render(replay_blitmap[c][0], True, WHITE)), replay_blitmap[c][1])
        if self.host.frame_count == 0 and self.replay_mouse:
            pygame.draw.circle(surface, ORANGE, [self.replay_mouse[0][0][0], self.replay_mouse[0][0][1]], 20, 0)
        elif mouse_pos:
            pygame.draw.circle(surface, ORANGE, [mouse_pos[0], mouse_pos[1]], 5, 0)

class replay_event:
    def __init__(self, t = None, k = None):
        self.type = t
        self.key = k