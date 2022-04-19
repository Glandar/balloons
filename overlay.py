import pygame, math, os
from bisect import bisect_left
from pygame import gfxdraw
from threading import Thread
from strings import CONTROLS_TEXT, INTRO_HEADERS, INTRO_TEXT #@UnresolvedImport
from colors import BLACK, GRAY, LIGHT_GRAY, WHITE, RED, GREEN, BLUE, ORANGE, PURPLE, CYAN #@UnresolvedImport
from constants import FRAME_RATE #@UnresolvedImport
from fonts import font20, font28, font40, font100, num_font50 #@UnresolvedImport
from ball import Ball #@UnusedImport #@UnresolvedImport
from beam import Beam  #@UnusedImport #@UnresolvedImport
from goal import Goal #@UnusedImport #@UnresolvedImport
from teleporter import Teleporter #@UnusedImport #@UnresolvedImport
from remover import Remover #@UnusedImport #@UnresolvedImport
from deposit import Deposit #@UnusedImport #@UnresolvedImport
import game #@UnresolvedImport

class Overlay:
    color_count = 0
    
    def __init__(self, host, settings, level_count, state):
        self.host = host
        self.settings = settings
        self.level_count = level_count
        self.state = state
        self.sliding = False
        self.slide_direction = None
        self.slide_speed = 10
        self.slide_pending = 0
        self.slide_displacement = 0
        self.surface_left = pygame.Surface((750, 750))
        self.surface_right = pygame.Surface((750, 750))
        
    def loop(self, screen, clock):       
        self.menu = self.Menu(self.host, self)
        self.selector = self.Selector(self.host, self)
        
        screen_height = screen.get_height()
        if screen_height != 750:
            screen = pygame.display.set_mode([750, 750], screen.get_flags())
        visual_settings_bg, visual_settings_tb = self.settings.background, self.settings.textured_beams
        
        while self.host.run and self.host.overlay:
            self.host.dummy_count += 1
        
            screen = self.event_handling(pygame.event.get(), screen)
            if not self.host.run or not self.host.overlay:
                break
            
            if self.sliding:
                self.slide(screen)
            else:
                self.draw(screen, self.state, True)
                if pygame.mouse.get_visible():
                    self.mouse(pygame.mouse.get_pos())
                
            pygame.display.flip()
            clock.tick(FRAME_RATE)
            
        pygame.mouse.set_visible(True)
        if screen_height != 750:
            screen = pygame.display.set_mode([750, 800], screen.get_flags())
        if visual_settings_bg != self.settings.background:
            self.host.create_background()
        if visual_settings_tb != self.settings.textured_beams:
            self.host.update_beam_surface(False)
        if self.host.level_count != self.level_count:
            self.host.level_count = self.level_count
            self.host.level(self.level_count)
        return screen, clock

    def draw(self, surface, page, title):
        self.color = (max(0, min(510, (Overlay.color_count - 255) % 1530, 1530 - (Overlay.color_count - 255) % 1530) - 255),
                      max(0, min(510, (Overlay.color_count + 255) % 1530, 1530 - (Overlay.color_count + 255) % 1530) - 255),
                      max(0, min(510, (Overlay.color_count + 765) % 1530, 1530 - (Overlay.color_count + 765) % 1530) - 255))

        if page == -1:
            return self.menu.draw(surface, self.color)
        elif title:
            return self.selector.draw(surface, page, self.color)
        else:
            return self.selector.body(surface, page)
        
    def mouse(self, mouse_pos):
        if self.state == -1:
            return self.menu.mouse(mouse_pos)
        else:
            return self.selector.mouse(mouse_pos)
        
    def event_handling(self, events, screen):
        if self.state == -1:
            return self.menu.event_handling(events, screen)
        else:
            return self.selector.event_handling(events, screen)
    
    def start_slide(self, from_page, to_page, dh = 0):
        if self.sliding:
            if (to_page > from_page) != self.slide_direction:
                self.slide_displacement = 750 - self.slide_displacement
                self.slide_pending = 0
                self.slide_speed = 10
            else:
                self.slide_pending += 1
                self.slide_speed = max(self.slide_speed, (self.slide_pending + 1) * 10)
                return

        self.state = (to_page + 1) % (math.ceil(len(self.settings.level_names) / 30) + 1) - 1
        self.sliding = True
        self.slide_direction = to_page > from_page

        if self.slide_direction:
            if from_page >= 0 and self.state >= 0:
                self.draw(self.surface_left, from_page, False)
                if dh:
                    self.selector.hover += dh
                self.draw(self.surface_right, self.state, False)
            else:
                self.draw(self.surface_left, from_page, True)
                self.draw(self.surface_right, self.state, True)
        elif from_page >= 0 and self.state >= 0:
            self.draw(self.surface_right, from_page, False)
            if dh:
                self.selector.hover -= dh
            self.draw(self.surface_left, self.state, False)
        else:
            self.draw(self.surface_right, from_page, True)
            self.draw(self.surface_left, self.state, True)

        if self.state == -1:
            self.selector.hover = None
            pygame.mouse.set_visible(True)

    def slide(self,surface):
        self.slide_displacement = min(self.slide_displacement + self.slide_speed, 750)
        if self.slide_direction:
            if pygame.mouse.get_pos()[0] > 750 - self.slide_displacement and pygame.mouse.get_visible():
                self.mouse((pygame.mouse.get_pos()[0] + self.slide_displacement - 750 if pygame.mouse.get_pos()[1] > 150 else pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1]))
            self.draw(self.surface_right, self.state, False)
            surface.blit(self.surface_left, [-self.slide_displacement, 0])
            surface.blit(self.surface_right, [750 - self.slide_displacement, 0])
        else:
            if pygame.mouse.get_pos()[0] < self.slide_displacement and pygame.mouse.get_visible():
                self.mouse((pygame.mouse.get_pos()[0] - self.slide_displacement + 750 if pygame.mouse.get_pos()[1] > 150 else pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1]))
            self.draw(self.surface_left, self.state, False)
            surface.blit(self.surface_left, [self.slide_displacement - 750, 0])
            surface.blit(self.surface_right, [self.slide_displacement, 0])
        if self.slide_displacement == 750:
            self.sliding = False
            self.slide_displacement = 0
            if self.slide_pending > 0:
                self.slide_pending -= 1
                if self.slide_direction:
                    self.start_slide(self.state, self.state + 1)
                else:
                    self.start_slide(self.state, self.state - 1)
            else:
                self.slide_speed = 10
        if not (self.state < 1 and self.slide_direction) and not ((self.state + 1) % math.ceil(len(self.settings.level_names) / 30) == 0 and not self.slide_direction):
            self.selector.title(surface, self.color)
        
    class Selector:
        def __init__(self, host, overlay):
            self.host = host
            self.overlay = overlay
            self.hover = None
            self.ranking_scroll = 0
            self.preview_count = None
            self.preview_surface = pygame.Surface((326, 326))
            self.rotation = 0
            self.angular_velocity = 0
        
        def mouse(self, mouse_pos):
            mouse_x = mouse_pos[0] / 120
            mouse_y = mouse_pos[1] / 120
            mouse_fx = math.floor(mouse_x)
            mouse_fy = math.floor(mouse_y)
            if mouse_y > 1 and mouse_x - mouse_fx >= 0.25 and mouse_y - mouse_fy >= 0.25:
                mouse_fxy = mouse_fx + 3 * mouse_fy - 2 + 12 * (mouse_x > 3) + self.overlay.state * 30
                if 0 < mouse_fxy <= len(self.overlay.settings.level_names):
                    self.hover = mouse_fxy
                    return
            elif 115 <= mouse_pos[0] <= 635 and 41 <= mouse_pos[1] <= 109:
                Overlay.color_count += 6
            elif mouse_pos[0] <= 75 and 125 - mouse_pos[0] <= mouse_pos[1] <= mouse_pos[0] + 25:
                self.hover = -1
            elif mouse_pos[0] >= 675 and mouse_pos[0] - 625 <= mouse_pos[1] <= 775 - mouse_pos[0]:
                self.hover = -2
            else:
                self.hover = None
            self.ranking_scroll = 0
        
        def click(self, button):
            if button == 1:
                if self.hover == -1:
                    self.overlay.start_slide(self.overlay.state, self.overlay.state - 1)
                elif self.hover == -2:
                    self.overlay.start_slide(self.overlay.state, self.overlay.state + 1)
                else:
                    self.overlay.level_count = self.hover % len(self.overlay.settings.level_names)
                    self.host.overlay = None
            elif button == 4:
                self.ranking_scroll = max(self.ranking_scroll - 1, 0)
            elif button == 5:
                if len(self.overlay.settings.global_highscores[self.overlay.settings.level_names[self.hover]]) > 3:
                    self.ranking_scroll = min(self.ranking_scroll + 1, len(self.overlay.settings.global_highscores[self.overlay.settings.level_names[self.hover]]) - 3)
                
        def event_handling(self, events, screen):
            for event in events:
                if event.type == pygame.QUIT:
                    print("Best session times:")
                    print(self.host.times)
                    self.host.run = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.hover:
                        self.click(event.button)
                elif event.type == pygame.MOUSEMOTION:
                    pygame.mouse.set_visible(True)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        print("Best session times:")
                        print(self.host.times)
                        self.host.run = False
                    elif event.key == pygame.K_f:
                        self.overlay.settings.frame = not self.overlay.settings.frame
                        screen = pygame.display.set_mode([750, screen.get_height()], 0 if self.overlay.settings.frame else pygame.NOFRAME)     
                    elif event.key == pygame.K_m:
                        self.overlay.start_slide(self.overlay.state, -1)
                    elif event.key == pygame.K_l or event.key == pygame.K_ESCAPE:
                        self.host.overlay = None
                    elif event.key == pygame.K_RETURN:
                        if self.hover and self.hover > 0:
                            self.overlay.level_count = self.hover % len(self.overlay.settings.level_names)
                            self.host.overlay = None
                    elif event.key in [pygame.K_UP, pygame.K_LEFT, pygame.K_DOWN, pygame.K_RIGHT]:
                        pygame.mouse.set_visible(False)
                        if not self.hover:
                            if 30 * self.overlay.state < self.overlay.level_count <= 30 * (self.overlay.state + 1):
                                self.hover = self.overlay.level_count
                            else:
                                self.hover = 30 * self.overlay.state + 1
                        elif event.key == pygame.K_UP:
                            if (self.hover - 1) % 15 > 2:
                                self.hover -= 3
                        elif event.key == pygame.K_LEFT:
                            if (self.hover - 1) % 3 > 0:
                                self.hover -= 1
                            elif self.hover - 30 * self.overlay.state > 15:
                                self.hover -= 13
                            elif self.hover > 30:
                                self.overlay.start_slide(self.overlay.state, self.overlay.state - 1, 13)
                            else:
                                self.overlay.start_slide(self.overlay.state, self.overlay.state - 1)
                        elif event.key == pygame.K_DOWN:
                            if (self.hover - 1) % 15 < 12 and self.hover <= len(self.overlay.settings.level_names) - 3:
                                self.hover += 3
                        elif event.key == pygame.K_RIGHT:
                            if self.hover == len(self.overlay.settings.level_names):
                                self.overlay.start_slide(self.overlay.state, self.overlay.state + 1)
                            elif (self.hover - 1) % 3 < 2:
                                self.hover += 1
                            elif self.hover > len(self.overlay.settings.level_names) - 13:
                                if self.hover - 30 * self.overlay.state < 16 and len(self.overlay.settings.level_names) - 30 * self.overlay.state > 16:
                                    self.hover = len(self.overlay.settings.level_names)
                                else:
                                    self.overlay.start_slide(self.overlay.state, self.overlay.state + 1, (len(self.overlay.settings.level_names) - 1)//3 * 3 + 1 - self.hover)
                            elif self.hover - 30 * self.overlay.state < 16:
                                self.hover += 13
                            else:
                                self.overlay.start_slide(self.overlay.state, self.overlay.state + 1, 13)
            return screen
    
        def draw(self, surface, page, accent):
            self.rotate()
            self.title(surface, accent)
            self.body(surface, page)
    
        def title(self, surface, accent):
            surface.fill(BLACK, [0, 0, 750, 150])
            menu_text = font100.render("Level Selection", True, accent)
            surface.blit(menu_text, [375 - menu_text.get_rect().width/2, 75 - menu_text.get_rect().height/2])
            pygame.draw.polygon(surface, LIGHT_GRAY if self.hover == -1 else GRAY, [(75, 100), (75, 50), (50, 75)])
            pygame.draw.polygon(surface, LIGHT_GRAY if self.hover == -2 else GRAY, [(675, 100), (675, 50), (700, 75)])
            
        def body(self, surface, page):
            surface.fill(BLACK, [0, 150, 750, 750])
            if self.hover and 0 < self.hover < len(self.overlay.settings.level_names):
                dx = 360 if self.hover <= 15 + page * 30 else 0
        
                pygame.draw.rect(surface, GREEN, [30 + dx, 150, 330, 330], 2)
                pygame.draw.rect(surface, GREEN, [30 + dx, 510, 330, 210], 2)
                info_text = font28.render(f"Level name: {self.overlay.settings.level_names[self.hover]}", True, WHITE)
                surface.blit(info_text, [40 + dx, 515])
                info_text = font28.render(f"Personal best time: {self.overlay.settings.highscores.get(self.overlay.settings.level_names[self.hover])}", True, WHITE)
                surface.blit(info_text, [40 + dx, 545])
                info_text = font28.render(f"Session best time: {self.host.times.get(self.overlay.settings.level_names[self.hover])}", True, WHITE)
                surface.blit(info_text, [40 + dx, 575])
    
                draw_count = 0
                found = not self.overlay.settings.highscores.get(self.overlay.settings.level_names[self.hover])
                if found:
                    info_text = font28.render(f"Global best times:", True, WHITE)
                    surface.blit(info_text, [40 + dx, 605])
    
                if self.overlay.settings.global_highscores.get(self.overlay.settings.level_names[self.hover]):
                    for i, score in enumerate(self.overlay.settings.global_highscores.get(self.overlay.settings.level_names[self.hover])[self.ranking_scroll:self.ranking_scroll + 3], self.ranking_scroll):
                        rank = i
                        if rank == self.ranking_scroll:
                            while (score[1] == self.overlay.settings.global_highscores.get(self.overlay.settings.level_names[self.hover])[rank - 1][1]):
                                if rank == 0:
                                    break
                                rank -= 1
                                draw_count += 1
                        elif score[1] == self.overlay.settings.global_highscores.get(self.overlay.settings.level_names[self.hover])[rank - 1][1]:
                            draw_count += 1
                            rank -= draw_count
                        else:
                            draw_count = 0
        
                        if score[0] == self.overlay.settings.profile:
                            info_text = font28.render(f"Global best times: (rank {rank + 1})", True, WHITE)
                            surface.blit(info_text, [40 + dx, 605])
                            info_text = font28.render(f"{rank + 1}. {score[0]}: {score[1]}", True, RED)
                            found = True
                        else:
                            info_text = font28.render(f"{rank + 1}. {score[0]}: {score[1]}", True, WHITE)
                        surface.blit(info_text, [40 + dx, 635 + 30 * (i - self.ranking_scroll)])
                if not found:
                    pos = bisect_left(self.overlay.settings.global_highscores.get(self.overlay.settings.level_names[self.hover]), self.overlay.settings.highscores.get(self.overlay.settings.level_names[self.hover]), key = lambda x:x[1])
                    info_text = font28.render(f"Global best times: (rank {pos + 1})", True, WHITE)
                    surface.blit(info_text, [40 + dx, 605])
    
                if self.hover != self.preview_count:
                    self.preview_count = self.hover
                    self.preview(self.hover)
                surface.blit(self.preview_surface, [32 + dx, 152])
        
            if not self.hover or self.hover <= 15 + page * 30 or self.hover in [len(self.overlay.settings.level_names), -1, -2]:
                for y in range(5):
                    for x in range(3):
                        n = x + y * 3 + 1 + page * 30
                        if 0 < n < len(self.overlay.settings.level_names):
                            pygame.draw.rect(surface, GREEN if n == self.hover else RED if n == self.overlay.level_count else BLUE, [x * 120 + 30, y * 120 + 150, 90, 90], 2)
                            level_number = num_font50.render(str(n), True, WHITE)
                            surface.blit(level_number, [x * 120 + 75 - level_number.get_rect().width/2, y * 120 + 173 - level_number.get_rect().height/2])
                            hs_text = font28.render("G: " + str(self.overlay.settings.global_highscores.get(self.overlay.settings.level_names[n])[0][1]) if self.overlay.settings.global_highscores.get(self.overlay.settings.level_names[n]) else "G: None", True, WHITE)
                            surface.blit(hs_text, [x * 120 + 75 - hs_text.get_rect().width/2, y * 120 + 207 - hs_text.get_rect().height/2])
                            ss_text = font28.render("P: " + str(self.overlay.settings.highscores.get(self.overlay.settings.level_names[n])), True, WHITE)
                            surface.blit(ss_text, [x * 120 + 75 - ss_text.get_rect().width/2, y * 120 + 227 - ss_text.get_rect().height/2])
                        elif n == len(self.overlay.settings.level_names):
                            pygame.draw.rect(surface, GREEN if n == self.hover else RED if self.overlay.level_count == 0 else BLUE, [x * 120 + 30, y * 120 + 150, 90, 90], 2)
                            self.plusle(surface, (x * 120 + 75, y * 120 + 195), 32, 0.06, self.rotation)
                            if self.hover == n:
                                create_level_text = font40.render("Create new level", True, WHITE)
                                if y < 4:
                                    pygame.draw.rect(surface, GREEN, [30, 270 + 120 * y, 330, 90], 2)
                                    surface.blit(create_level_text, [195 - create_level_text.get_rect().width/2, 315 + 120 * y - create_level_text.get_rect().height/2])
                                else:
                                    pygame.draw.rect(surface, GREEN, [150 + 120 * x, 150 + 120 * y, 330, 90], 2)
                                    surface.blit(create_level_text, [315 + 120 * x - create_level_text.get_rect().width/2, 195 + 120 * y - create_level_text.get_rect().height/2])
    
            if not self.hover or self.hover >= 16 + page * 30 or self.hover in [len(self.overlay.settings.level_names), -1, -2]:
                for y in range(5):
                    for x in range(3):
                        n = x + y * 3 + 16 + page * 30
                        if 0 < n < len(self.overlay.settings.level_names):
                            pygame.draw.rect(surface, GREEN if n == self.hover else RED if n == self.overlay.level_count else BLUE, [x * 120 + 390, y * 120 + 150, 90, 90], 2)
                            level_number = num_font50.render(str(n), True, WHITE)
                            surface.blit(level_number, [x * 120 + 435 - level_number.get_rect().width/2, y * 120 + 173 - level_number.get_rect().height/2])
                            hs_text = font28.render("G: " + str(self.overlay.settings.global_highscores.get(self.overlay.settings.level_names[n])[0][1]) if self.overlay.settings.global_highscores.get(self.overlay.settings.level_names[n]) else "G: None", True, WHITE)
                            surface.blit(hs_text, [x * 120 + 435 - hs_text.get_rect().width/2, y * 120 + 207 - hs_text.get_rect().height/2])
                            ss_text = font28.render("P: " + str(self.overlay.settings.highscores.get(self.overlay.settings.level_names[n])), True, WHITE)
                            surface.blit(ss_text, [x * 120 + 435 - ss_text.get_rect().width/2, y * 120 + 227 - ss_text.get_rect().height/2])
                        elif n == len(self.overlay.settings.level_names):
                            pygame.draw.rect(surface, GREEN if n == self.hover else RED if self.overlay.level_count == 0 else BLUE, [x * 120 + 390, y * 120 + 150, 90, 90], 2)
                            self.plusle(surface, (x * 120 + 435, y * 120 + 195), 32, 0.06, self.rotation)
                            if self.hover == n:
                                create_level_text = font40.render("Create new level", True, WHITE)
                                if y < 4:
                                    pygame.draw.rect(surface, GREEN, [390, 270 + 120 * y, 330, 90], 2)
                                    surface.blit(create_level_text, [555 - create_level_text.get_rect().width/2, 315 + 120 * y - create_level_text.get_rect().height/2])
                                else:
                                    surface.fill(BLACK, [390, 510, 330, 90])
                                    pygame.draw.rect(surface, GREEN, [390, 510, 330, 90], 2)
                                    surface.blit(create_level_text, [555 - create_level_text.get_rect().width/2, 75 + 120 * y - create_level_text.get_rect().height/2])
    
        def preview(self, level):
            self.preview_surface.fill(BLACK)
            
            with open(f"game_data/levels/{self.overlay.settings.level_names[level]}.txt", "r") as file:
                b, o, g, t, r, d = eval(''.join(file.read().splitlines()))
            
            for ball in b:
                gfxdraw.aacircle(self.preview_surface, round(ball.position.x * 326/750), round(ball.position.y * 326/750), round(ball.size * 326/750), RED)
                gfxdraw.filled_circle(self.preview_surface, round(ball.position.x * 326/750), round(ball.position.y * 326/750), round(ball.size * 326/750), RED)
            for beam in o:
                self.preview_surface.fill(BLUE, [round(beam.left * 326/750), round(beam.up * 326/750), round(beam.right * 326/750) - round(beam.left * 326/750), round(beam.down * 326/750) - round(beam.up * 326/750)])
            for goal in g:
                gfxdraw.aacircle(self.preview_surface, round(goal.center_x * 326/750), round(goal.center_y * 326/750), round(goal.radius * 326/750), GREEN)
                gfxdraw.filled_circle(self.preview_surface, round(goal.center_x * 326/750), round(goal.center_y * 326/750), round(goal.radius * 326/750), GREEN)
            for deposit in d:
                gfxdraw.aacircle(self.preview_surface, round(deposit.center_x * 326/750), round(deposit.center_y * 326/750), round(deposit.radius * 326/750), ORANGE)
                gfxdraw.filled_circle(self.preview_surface, round(deposit.center_x * 326/750), round(deposit.center_y * 326/750), round(deposit.radius * 326/750), ORANGE)
            for teleporter in t:
                gfxdraw.aacircle(self.preview_surface, round(teleporter.center_x * 326/750), round(teleporter.center_y * 326/750), round(teleporter.radius * 326/750), PURPLE)
                gfxdraw.filled_circle(self.preview_surface, round(teleporter.center_x * 326/750), round(teleporter.center_y * 326/750), round(teleporter.radius * 326/750), PURPLE)
            for remover in r:
                gfxdraw.aacircle(self.preview_surface, round(remover.center_x * 326/750), round(remover.center_y * 326/750), round(remover.radius * 326/750), CYAN)
                gfxdraw.filled_circle(self.preview_surface, round(remover.center_x * 326/750), round(remover.center_y * 326/750), round(remover.radius * 326/750), CYAN)

        def plusle(self, surface, center, scale, angle, rotation):
            pygame.draw.aalines(surface, WHITE, True, [(center[0] + scale * math.sin((  - angle) * math.pi + rotation), center[1] + scale * math.sin((1.5 - angle) * math.pi + rotation)),
                                                       (center[0] + scale * math.sin((    angle) * math.pi + rotation), center[1] + scale * math.sin((1.5 + angle) * math.pi + rotation)),
                                                       (center[0] + scale * math.sin((1 - angle) * math.pi + rotation), center[1] + scale * math.sin((0.5 - angle) * math.pi + rotation)),
                                                       (center[0] + scale * math.sin((1 + angle) * math.pi + rotation), center[1] + scale * math.sin((0.5 + angle) * math.pi + rotation))])      
            pygame.draw.aalines(surface, WHITE, True, [(center[0] + scale * math.sin((0.5 - angle) * math.pi + rotation), center[1] + scale * math.sin((  - angle) * math.pi + rotation)),
                                                       (center[0] + scale * math.sin((0.5 + angle) * math.pi + rotation), center[1] + scale * math.sin((    angle) * math.pi + rotation)),
                                                       (center[0] + scale * math.sin((1.5 - angle) * math.pi + rotation), center[1] + scale * math.sin((1 - angle) * math.pi + rotation)),
                                                       (center[0] + scale * math.sin((1.5 + angle) * math.pi + rotation), center[1] + scale * math.sin((1 + angle) * math.pi + rotation))])
            gfxdraw.filled_polygon(surface, [(center[0] + scale * math.sin((  - angle) * math.pi + rotation), center[1] + scale * math.sin((1.5 - angle) * math.pi + rotation)),
                                             (center[0] + scale * math.sin((    angle) * math.pi + rotation), center[1] + scale * math.sin((1.5 + angle) * math.pi + rotation)),
                                             (center[0] + scale * math.sin((1 - angle) * math.pi + rotation), center[1] + scale * math.sin((0.5 - angle) * math.pi + rotation)),
                                             (center[0] + scale * math.sin((1 + angle) * math.pi + rotation), center[1] + scale * math.sin((0.5 + angle) * math.pi + rotation))], WHITE)      
            gfxdraw.filled_polygon(surface, [(center[0] + scale * math.sin((0.5 - angle) * math.pi + rotation), center[1] + scale * math.sin((  - angle) * math.pi + rotation)),
                                             (center[0] + scale * math.sin((0.5 + angle) * math.pi + rotation), center[1] + scale * math.sin((    angle) * math.pi + rotation)),
                                             (center[0] + scale * math.sin((1.5 - angle) * math.pi + rotation), center[1] + scale * math.sin((1 - angle) * math.pi + rotation)),
                                             (center[0] + scale * math.sin((1.5 + angle) * math.pi + rotation), center[1] + scale * math.sin((1 + angle) * math.pi + rotation))], WHITE)
    
        def rotate(self):
            if self.hover == len(self.overlay.settings.level_names):
                self.angular_velocity = min(self.angular_velocity + 0.001, 0.2)
            else:
                self.angular_velocity = max(self.angular_velocity - 0.002, 0)
            self.rotation += self.angular_velocity
            
    class Menu:
        def __init__(self, host, overlay):
            self.host = host
            self.overlay = overlay
            self.hover = None
            self.level = 1
            self.rects = [pygame.Rect(50, 200, 290, 30)] + [None] * 6
            self.texts = [None] * (12 + 3 * len(self.overlay.settings.profile_names) + len(self.overlay.settings.level_names))
            self.coords = [None] * 31
            self.profiles = min(6, len(self.overlay.settings.profile_names))
            self.intro_lengths = [len(text.splitlines()) for text in INTRO_TEXT]
            self.edit = 0
            self.editable = ""
            self.data_mode = 0
            self.data_scroll = 0
            self.data_scroll_bar = 285
            self.data_scroll_drag = False
            self.overlay.settings_mode = 0
            self.control_mode = 0
            self.control_scroll = 0
            self.control_scroll_bar = 515
            self.control_scroll_drag = False
            
        def switch_profile(self):
            try:
                self.overlay.settings.load_settings(self.editable)
            except FileNotFoundError:
                return self.create_profile()
            self.overlay.settings.profile = self.editable
            self.host.times = {}
            print(f"Loaded profile: {self.overlay.settings.profile}")
        
        def create_profile(self):
            if not self.editable:
                return
            try:
                os.makedirs(f"game_data/profiles/{self.editable}/highscores")
            except OSError:
                print("IO system error, try again")
                return
            self.overlay.settings.profile = self.editable
            self.overlay.settings.update_profiles()
            self.overlay.settings.save_settings()
            self.overlay.settings.highscores = {}
            self.host.times = {}
            self.texts.extend([None] * 3)
            print(f"Created profile: {self.overlay.settings.profile}")
            self.profiles = min(6, self.profiles + 1)
            
        def verify_highscores(self):
            class replay_event:
                def __init__(self, t = None, k = None):
                    self.type = t
                    self.key = k
                    
            local_game = game.Game(self.overlay.settings, False)
            local_highscores = self.overlay.settings.load_highscores(self.overlay.settings.profile)
            print(f"Verifying highscores for {self.overlay.settings.profile}:")
                
            for level_no in range(1, len(self.overlay.settings.level_names)):
                local_game.level(level_no, message_start = False)
                
                try:
                    with open(f"game_data/profiles/{self.overlay.settings.profile}/highscores/{self.overlay.settings.level_names[level_no]}.txt", "r") as file:
                        replay_actions, replay_mouse = eval(file.read())
                except FileNotFoundError:
                    print(f"Level {level_no}: No highscore set") 
                    continue
                        
                while local_game.frame_count < local_highscores[self.overlay.settings.level_names[level_no]] + 60:
                    if replay_mouse:
                        if replay_mouse[0][1] > 1:
                            mouse_pos = replay_mouse[0][0]
                            replay_mouse[0][1] -= 1
                        else:
                            mouse_pos = replay_mouse.pop(0)[0]
                    
                    if replay_actions and replay_actions[0][0] == local_game.frame_count:
                        del replay_actions[0][0]
                        replay_events = [replay_event(pygame.KEYDOWN, a) if a > 0 else replay_event(pygame.KEYUP, -a) for a in replay_actions[0]]
                        del replay_actions[0]
                        local_game.event_handling(replay_events, None, None, mouse_pos)
                    
                    local_game.inflate()
                    local_game.physics()
                        
                    for goal in local_game.Goals:
                        if goal.air > 0:
                            break
                    else:
                        if local_game.frame_count == self.overlay.settings.highscores[self.overlay.settings.level_names[level_no]]:
                            print(f"Level {level_no}: {local_game.frame_count}/{local_highscores[self.overlay.settings.level_names[level_no]]}")
                        else:
                            print(f"Level {level_no}: {local_game.frame_count}/{local_highscores[self.overlay.settings.level_names[level_no]]} - incorrect highscore")
                        break
                    
                    local_game.frame_count += 1
                    
                else:
                    print(f"Level {level_no}: not completed")
            
        def rename_level(self):
            if self.editable == self.overlay.settings.level_names[self.level]:
                print("Level name unchanged")
            elif self.editable in self.overlay.settings.level_names:
                print("Level name not unique")
            else:
                os.rename(f"game_data/levels/{self.overlay.settings.level_names[self.level]}.txt", f"game_data/levels/{self.editable}.txt")
                for profile_name in self.overlay.settings.profile_names:
                    if os.path.exists(f"game_data/profiles/{profile_name}/highscores/{self.overlay.settings.level_names[self.level]}.txt"):
                        os.rename(f"game_data/profiles/{profile_name}/highscores/{self.overlay.settings.level_names[self.level]}.txt", f"game_data/profiles/{profile_name}/highscores/{self.editable}.txt")
                        with open(f"game_data/profiles/{profile_name}/highscores/highscores.txt", 'r') as file:
                            new_highscores = file.read().replace(f"'{self.overlay.settings.level_names[self.level]}':", f"'{self.editable}':")
                        with open(f"game_data/profiles/{profile_name}/highscores/highscores.txt", 'w') as file:
                            file.write(new_highscores)
                if self.overlay.settings.level_names[self.level] in self.overlay.settings.highscores:
                    self.overlay.settings.highscores[self.editable] = self.overlay.settings.highscores.pop(self.overlay.settings.level_names[self.level])
                if self.overlay.settings.level_names[self.level] in self.host.times:
                    self.host.times[self.editable] = self.host.times.pop(self.overlay.settings.level_names[self.level])
                print(f"Level {self.overlay.settings.level_names[self.level]} renamed to {self.editable}")
                self.overlay.settings.level_names = [os.path.splitext(filename)[0] for filename in sorted(os.listdir("game_data/levels"), key = lambda x: (os.path.splitext(x)[1], os.path.splitext(x)[0]))]
                self.overlay.settings.update_profiles()
        
        def delete_level(self):
            if input(f"Are you sure you want to delete level {self.overlay.settings.level_names[self.level]}? (type delete to confirm)\n") == "delete":
                os.remove(f"game_data/levels/{self.overlay.settings.level_names[self.level]}.txt")
                for profile_name in self.overlay.settings.profile_names:
                    try:
                        os.remove(f"game_data/profiles/{profile_name}/highscores/{self.overlay.settings.level_names[self.level]}.txt")
                        self.overlay.settings.load_highscores(profile_name, True)
                        if self.overlay.settings.level_names[self.level] in self.overlay.settings.highscores:
                            del self.overlay.settings.highscores[self.overlay.settings.level_names[self.level]]
                        with open(f"game_data/profiles/{profile_name}/highscores/highscores.txt", "w") as file:
                            print(self.overlay.settings.highscores, file = file)
                    except FileNotFoundError:
                        pass
                self.overlay.settings.load_highscores(self.overlay.settings.profile, True)
                if self.overlay.settings.level_names[self.level] in self.host.times:
                    del self.host.times[self.overlay.settings.level_names[self.level]]
                print(f"Level {self.overlay.settings.level_names[self.level]} deleted")
                self.overlay.settings.level_names = [os.path.splitext(filename)[0] for filename in sorted(os.listdir("game_data/levels"), key = lambda x: (os.path.splitext(x)[1], os.path.splitext(x)[0]))]
                self.overlay.settings.update_profiles()
                self.level -= 1
                self.data_scroll = max(self.data_scroll - 1, 0)
    
        def mouse(self, mouse_pos):
            if 281 <= mouse_pos[0] <= 469 and 41 <= mouse_pos[1] <= 109:
                Overlay.color_count += 6
            elif self.rects[0].collidepoint(*mouse_pos):
                self.hover = 0
            elif self.overlay.settings_mode == 2 and self.rects[1].collidepoint(*mouse_pos):
                self.hover = 8
            elif mouse_pos[0] >= 675 and mouse_pos[0] - 625 <= mouse_pos[1] <= 775 - mouse_pos[0]:
                self.hover = -1
            elif mouse_pos[0] <= 75 and 125 - mouse_pos[0] <= mouse_pos[1] <= mouse_pos[0] + 25:
                self.hover = -2
            elif 333 <= mouse_pos[0] <= 343 and 0 <= mouse_pos[1] - self.data_scroll_bar <= 30 and self.data_mode == 1:
                self.hover = -3
            elif 705 <= mouse_pos[0] <= 715 and 0 <= mouse_pos[1] - self.control_scroll_bar <= 30:
                self.hover = -4
            elif 50 <= mouse_pos[0] <= 340 and 285 <= mouse_pos[1] <= 465:
                self.hover = (mouse_pos[1] - 285)//30 + 13
            else:
                for i, (t, c) in enumerate(zip(self.texts[1:13], self.coords[1:13]), 1): 
                    if t.get_rect().collidepoint(mouse_pos[0] - c[0], mouse_pos[1] - c[1]):
                        self.hover = i
                        break
                else:
                    if self.overlay.settings_mode == 2:
                        for i, rect in enumerate(self.rects[2:], 19):
                            if rect.collidepoint(*mouse_pos):
                                self.hover = i
                                break
                        else:
                            self.hover = None
                    else:
                        self.hover = None
            
        def click(self, button, screen):
            if button == 1:
                if not (395 <= pygame.mouse.get_pos()[0] <= 715 and 155 <= pygame.mouse.get_pos()[1] <= 315):
                    self.overlay.settings_mode = 0
                
                if self.hover is None:
                    self.edit = 0
                    self.editable = ""
                    return screen
                
                if self.hover == 0:
                    if self.edit != 1:
                        self.edit = 1
                        self.editable = self.overlay.settings.profile if self.data_mode == 0 else self.overlay.settings.level_names[self.level]
                elif self.hover == -1:
                    self.overlay.start_slide(-1, 0)
                elif self.hover == -2:
                    self.overlay.start_slide(-1, -2)
                elif self.hover == -3:
                    self.data_scroll_drag = True
                elif self.hover == -4:
                    self.control_scroll_drag = True
                elif self.hover == 1:
                    self.data_mode = 0
                    self.data_scroll = 0
                    self.data_scroll_bar = 285
                elif self.hover == 2:
                    self.data_mode = 1
                    self.data_scroll = 0
                elif self.hover == 3:
                    if self.data_mode == 0:
                        if self.editable != self.overlay.settings.profile:
                            self.overlay.settings.save_settings()
                            self.switch_profile()
                    elif self.data_mode == 1:
                        self.rename_level()
                elif self.hover == 4:
                    if self.data_mode == 0:
                        thread = Thread(target = self.verify_highscores)
                        thread.start()
                    elif self.data_mode == 1:
                        self.delete_level()
                elif 5 <= self.hover <= 8:
                    if self.overlay.settings_mode == 0:
                        self.overlay.settings_mode = self.hover - 4
                    elif self.overlay.settings_mode == 1:
                        if self.hover == 5:
                            self.overlay.settings.show_intro_text = not self.overlay.settings.show_intro_text
                        elif self.hover == 6:
                            self.overlay.settings.textured_beams = not self.overlay.settings.textured_beams
                        elif self.hover == 7:
                            self.overlay.settings.pathclear = not self.overlay.settings.pathclear
                        elif self.hover == 8:
                            self.overlay.settings.frame = not self.overlay.settings.frame
                            screen = pygame.display.set_mode([750, screen.get_height()], 0 if self.overlay.settings.frame else pygame.NOFRAME)     
                    elif self.overlay.settings_mode == 2:
                        if self.hover == 5:
                            self.overlay.settings.darkness = False
                        elif self.hover == 6:
                            self.overlay.settings.darkness = True
                        elif self.hover == 7:
                            self.overlay.settings.dark_radius = int(self.editable)
                            print(f"Sight distance is set to {self.overlay.settings.dark_radius}")
                        elif self.hover == 8:
                            if self.edit != 2:
                                self.edit = 2
                                self.editable = str(self.overlay.settings.dark_radius)
                    elif self.overlay.settings_mode == 3:
                        self.overlay.settings.animations[self.hover - 5] = not self.overlay.settings.animations[self.hover - 5]
                    elif self.overlay.settings_mode == 4:
                        self.overlay.settings.show_info_mode = self.hover - 5
                elif self.hover == 9:
                    self.host.overlay = None
                elif self.hover == 10:
                    print("Best session times:")
                    print(self.host.times)
                    self.host.run = False
                elif self.hover == 11:
                    self.control_mode = 0
                    self.control_scroll = 0
                    self.control_scroll_bar = 515
                elif self.hover == 12:
                    self.control_mode = 1
                    self.control_scroll = 0
                    self.control_scroll_bar = 515
                elif 13 <= self.hover <= 18:
                    if self.data_mode == 0:
                        if self.hover - 13 < self.profiles:
                            if self.overlay.settings.profile_names[self.hover - 13 + self.data_scroll] != self.overlay.settings.profile:
                                self.overlay.settings. save_settings()
                                self.editable = self.overlay.settings.profile_names[self.hover - 13 + self.data_scroll]
                                self.switch_profile()
                    elif self.data_mode == 1:
                        if self.hover - 13 < len(self.overlay.settings.level_names):
                            self.level = self.hover - 12 + self.data_scroll
                            self.editable = self.overlay.settings.level_names[self.level]
                elif self.hover > 18:
                    self.overlay.settings.dark_shape = self.hover - 19
                
                if not (self.edit, self.hover) in [(1, 0), (2, 8)]:
                    self.edit = 0
                    self.editable = ""
                        
    
            elif button == 4:
                if 30 <= pygame.mouse.get_pos()[0] <= 720 and 510 <= pygame.mouse.get_pos()[1] <= 720:
                    if self.control_scroll > 0:
                        self.control_scroll -= 1
                        if self.control_mode == 0:
                            self.control_scroll_bar -= 170 / (len(CONTROLS_TEXT.splitlines()) - 7)
                        elif self.control_mode == 1:
                            self.control_scroll_bar -= 170 / (sum(self.intro_lengths) - 5)
                elif 30 <= pygame.mouse.get_pos()[0] <= 360 and 150 <= pygame.mouse.get_pos()[1] <= 480:
                    if self.data_scroll > 0:
                        self.data_scroll -= 1
                        if self.data_mode == 1:
                            self.data_scroll_bar -= 148 / (len(self.overlay.settings.level_names) - 7)
            elif button == 5:
                if 30 <= pygame.mouse.get_pos()[0] <= 720 and 510 <= pygame.mouse.get_pos()[1] <= 720:
                    if self.control_mode == 0:
                        if self.control_scroll < len(CONTROLS_TEXT.splitlines()) - 7:
                            self.control_scroll += 1
                            self.control_scroll_bar += 170 / (len(CONTROLS_TEXT.splitlines()) - 7)
                    elif self.control_mode == 1:
                        if self.control_scroll < sum(self.intro_lengths) - 5:
                            self.control_scroll += 1
                            self.control_scroll_bar += 170 / (sum(self.intro_lengths) - 5)
                elif 30 <= pygame.mouse.get_pos()[0] <= 360 and 150 <= pygame.mouse.get_pos()[1] <= 480:
                    if self.data_mode == 0:
                        self.data_scroll = min(self.data_scroll + 1, len(self.overlay.settings.profile_names) - self.profiles)
                    elif self.data_mode == 1:
                        if self.data_scroll < len(self.overlay.settings.level_names) - 7:
                            self.data_scroll += 1
                            self.data_scroll_bar += 148 / (len(self.overlay.settings.level_names) - 7)
            return screen
    
        def event_handling(self, events, screen):
            for event in events:
                if event.type == pygame.QUIT:
                    print("Best session times:")
                    print(self.host.times)
                    self.host.run = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    screen = self.click(event.button, screen)
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        if self.data_scroll_drag:
                            self.data_scroll_drag = False
                            self.data_scroll_bar = self.data_scroll * 148 / (len(self.overlay.settings.level_names) - 7) + 285
                        elif self.control_scroll_drag:
                            self.control_scroll_drag = False
                            if self.control_mode == 0:
                                self.control_scroll_bar = self.control_scroll * 170 / (len(CONTROLS_TEXT.splitlines()) - 7) + 515
                            elif self.control_mode == 1:
                                self.control_scroll_bar = self.control_scroll * 170 / (sum(self.intro_lengths) - 5) + 515
                elif event.type == pygame.MOUSEMOTION:
                    if self.data_scroll_drag:
                        self.data_scroll_bar = min(max(285, self.data_scroll_bar + event.rel[1]), 433)
                        self.data_scroll = round((self.data_scroll_bar - 285) / 148 * (len(self.overlay.settings.level_names) - 7))
                    elif self.control_scroll_drag:
                        self.control_scroll_bar = min(max(515, self.control_scroll_bar + event.rel[1]), 685)
                        if self.control_mode == 0:
                            self.control_scroll = round((self.control_scroll_bar - 515) / 170 * (len(CONTROLS_TEXT.splitlines()) - 7))
                        elif self.control_mode == 1:
                            self.control_scroll = round((self.control_scroll_bar - 515) / 170 * (sum(self.intro_lengths) - 5))
                elif event.type == pygame.KEYDOWN:
                    if self.edit > 0:
                        if event.key== pygame.K_BACKSPACE:
                            self.editable = self.editable[:-1]
                        elif event.key == pygame.K_ESCAPE:
                            self.edit = 0
                            self.editable = ""
                        elif (self.edit == 1 and event.unicode not in "\/:*?<>|") or (self.edit == 2 and event.unicode.isdecimal()):
                            self.editable += event.unicode             
                    elif event.key == pygame.K_q:
                        print("Best session times:")
                        print(self.host.times)
                        self.host.run = False
                    elif event.key == pygame.K_f:
                        self.overlay.settings.frame = not self.overlay.settings.frame
                        screen = pygame.display.set_mode([750, screen.get_height()], 0 if self.overlay.settings.frame else pygame.NOFRAME)     
                    elif event.key == pygame.K_m or event.key == pygame.K_ESCAPE:
                        self.host.overlay = None
                    elif event.key == pygame.K_l:
                        self.overlay.start_slide(-1, max((self.overlay.level_count - 1) // 30, 0))
                    elif event.key == pygame.K_RIGHT:
                        self.overlay.start_slide(-1, 0)
                        pygame.mouse.set_visible(False)
                    elif event.key == pygame.K_LEFT:
                        self.overlay.start_slide(-1, -2)
                        pygame.mouse.set_visible(False)
                    elif event.key == pygame.K_DOWN:
                        if 30 <= pygame.mouse.get_pos()[0] <= 720 and 510 <= pygame.mouse.get_pos()[1] <= 720:
                            if self.control_mode == 0:
                                if self.control_scroll < len(CONTROLS_TEXT.splitlines()) - 7:
                                    self.control_scroll += 1
                                    self.control_scroll_bar += 170 / (len(CONTROLS_TEXT.splitlines()) - 7)
                            elif self.control_mode == 1:
                                if self.control_scroll < sum(self.intro_lengths) - 5:
                                    self.control_scroll += 1
                                    self.control_scroll_bar += 170 / (sum(self.intro_lengths) - 5)
                        elif 30 <= pygame.mouse.get_pos()[0] <= 360 and 150 <= pygame.mouse.get_pos()[1] <= 480:
                            if self.data_mode == 0:
                                self.data_scroll = min(self.data_scroll + 1, len(self.overlay.settings.profile_names) - self.profiles)
                            elif self.data_mode == 1:
                                if self.data_scroll < len(self.overlay.settings.level_names) - 7:
                                    self.data_scroll += 1
                                    self.data_scroll_bar += 148 / (len(self.overlay.settings.level_names) - 7)
                    elif event.key == pygame.K_UP:
                        if 30 <= pygame.mouse.get_pos()[0] <= 720 and 510 <= pygame.mouse.get_pos()[1] <= 720:
                            if self.control_scroll > 0:
                                self.control_scroll -= 1
                                if self.control_mode == 0:
                                    self.control_scroll_bar -= 170 / (len(CONTROLS_TEXT.splitlines()) - 7)
                                elif self.control_mode == 1:
                                    self.control_scroll_bar -= 170 / (sum(self.intro_lengths) - 5)
                        elif 30 <= pygame.mouse.get_pos()[0] <= 360 and 150 <= pygame.mouse.get_pos()[1] <= 480:
                            if self.data_scroll > 0:
                                self.data_scroll -= 1
                                if self.data_mode == 1:
                                    self.data_scroll_bar -= 148 / (len(self.overlay.settings.level_names) - 7)
            return screen

        def draw(self, surface, accent):
            self.update(accent)
            self.title(surface, accent)
            self.body(surface, accent)

        def update(self, accent):
            self.texts[0] = font28.render(self.editable if self.edit == 1 else self.overlay.settings.profile if self.data_mode == 0 else self.overlay.settings.level_names[self.level], True, GREEN if self.hover == 0 else WHITE)
            self.texts[1] = font40.render("Profiles", True, GREEN if self.hover == 1 else WHITE)
            self.texts[2] = font40.render("Levels", True, GREEN if self.hover == 2 else WHITE)
            self.texts[3] = font28.render("Load profile" if self.data_mode == 0 else "Rename level", True, GREEN if self.hover == 3 else WHITE)
            self.texts[4] = font28.render("Verify profile" if self.data_mode == 0 else "Delete level", True, GREEN if self.hover == 4 else WHITE)
            if self.overlay.settings_mode == 0:
                self.texts[5] = font40.render("Visuals & Frame", True, RED if self.hover == 5 else WHITE)
                self.texts[6] = font40.render("Darkness settings", True, RED if self.hover == 6 else WHITE)
                self.texts[7] = font40.render("Animation settings", True, RED if self.hover == 7 else WHITE)
                self.texts[8] = font40.render("Time & Air overlay", True, RED if self.hover == 8 else WHITE)
            elif self.overlay.settings_mode == 1:
                self.texts[5] = font40.render("Show intro text", True, RED if self.hover == 5 else accent if self.overlay.settings.show_intro_text else WHITE)
                self.texts[6] = font40.render("Textured objects", True, RED if self.hover == 6 else accent if self.overlay.settings.textured_beams else WHITE)
                self.texts[7] = font40.render("Clear drawing on start", True, RED if self.hover == 7 else accent if self.overlay.settings.pathclear else WHITE)
                self.texts[8] = font40.render("Show window frame", True, RED if self.hover == 8 else accent if self.overlay.settings.frame else WHITE)
            elif self.overlay.settings_mode == 2:
                self.texts[5] = font40.render("Full field vision", True, RED if self.hover == 5 else accent if not self.overlay.settings.darkness else WHITE)
                self.texts[6] = font40.render("Local vision only", True, RED if self.hover == 6 else accent if self.overlay.settings.darkness else WHITE)
                self.texts[7] = font40.render("Set radius:", True, RED if self.hover == 7 else WHITE)
                self.texts[8] = font40.render(self.editable if self.edit == 2 else str(self.overlay.settings.dark_radius), True, RED if self.hover == 8 else WHITE)
                self.rects[1] = pygame.Rect(430 + self.texts[7].get_rect().width, 238, 260 - self.texts[7].get_rect().width, 30)
            elif self.overlay.settings_mode == 3:
                self.texts[5] = font40.render("Ball animation", True, RED if self.hover == 5 else accent if self.overlay.settings.animations[0] else WHITE)
                self.texts[6] = font40.render("Goal animation", True, RED if self.hover == 6 else accent if self.overlay.settings.animations[1] else WHITE)
                self.texts[7] = font40.render("Teleporter anim.", True, RED if self.hover == 7 else accent if self.overlay.settings.animations[2] else WHITE)
                self.texts[8] = font40.render("Remover anim.", True, RED if self.hover == 8 else accent if self.overlay.settings.animations[3] else WHITE)
            elif self.overlay.settings_mode == 4:
                self.texts[5] = font40.render("Always hide overlay", True, RED if self.hover == 5 else accent if self.overlay.settings.show_info_mode == 0 else WHITE)
                self.texts[6] = font40.render("Hide overlay on prox", True, RED if self.hover == 6 else accent if self.overlay.settings.show_info_mode == 1 else WHITE)
                self.texts[7] = font40.render("Hide overlay on hover", True, RED if self.hover == 7 else accent if self.overlay.settings.show_info_mode == 2 else WHITE)
                self.texts[8] = font40.render("Always show overlay", True, RED if self.hover == 8 else accent if self.overlay.settings.show_info_mode == 3 else WHITE)
            self.texts[9] = font40.render("Play", True, RED if self.hover == 9 else WHITE)
            self.texts[10] = font40.render("Quit", True, RED if self.hover == 10 else WHITE)
            self.texts[11] = font40.render("Game controls", True, ORANGE if self.hover == 11 else WHITE)
            self.texts[12] = font40.render("Game explanation", True, ORANGE if self.hover == 12 else WHITE)
            for i, name in enumerate(self.overlay.settings.profile_names):
                self.texts[13 + 3 * i] = font28.render(name, True, GREEN if self.hover == 13 + i - self.data_scroll else accent if name == self.overlay.settings.profile else WHITE)
                self.texts[14 + 3 * i] = font28.render(f"({self.overlay.settings.global_profile_scores[name][0]}/{len(self.overlay.settings.level_names) - 1})", True, GREEN if self.hover == 13 + i - self.data_scroll else accent if name == self.overlay.settings.profile else WHITE)
                self.texts[15 + 3 * i] = font28.render(str(self.overlay.settings.global_profile_scores[name][1]), True, GREEN if self.hover == 13 + i - self.data_scroll else accent if name == self.overlay.settings.profile else WHITE)     
            for i, name in enumerate(self.overlay.settings.level_names[1:]):
                self.texts[13 + 3 * len(self.overlay.settings.profile_names) + i] = font28.render(name, True, GREEN if self.hover == 13 + i - self.data_scroll else accent if i + 1 == self.level else WHITE)
            
            self.coords[0] = (60, 215 - self.texts[0].get_rect().height/2)
            self.coords[1] = (50, 180 - self.texts[1].get_rect().height/2)
            self.coords[2] = (340 - self.texts[2].get_rect().width, 180 - self.texts[2].get_rect().height/2)
            self.coords[3] = (50, 250 - self.texts[3].get_rect().height/2)
            self.coords[4] = (340 - self.texts[4].get_rect().width, 250 - self.texts[4].get_rect().height/2)
            self.coords[5] = (555 - self.texts[5].get_rect().width/2, 175 - self.texts[5].get_rect().height/2)
            self.coords[6] = (555 - self.texts[6].get_rect().width/2, 215 - self.texts[6].get_rect().height/2)
            if self.overlay.settings_mode == 2:
                self.coords[7] = (420, 255 - self.texts[7].get_rect().height/2)
                self.coords[8] = (560 + (self.texts[7].get_rect().width - self.texts[8].get_rect().width)/2, 255 - self.texts[8].get_rect().height/2)
            else:
                self.coords[7] = (555 - self.texts[7].get_rect().width/2, 255 - self.texts[7].get_rect().height/2)
                self.coords[8] = (555 - self.texts[8].get_rect().width/2, 295 - self.texts[8].get_rect().height/2)
            self.coords[9] = (500 - self.texts[9].get_rect().width/2, 335 - self.texts[9].get_rect().height/2)
            self.coords[10] = (610 - self.texts[10].get_rect().width/2, 335 - self.texts[10].get_rect().height/2)
            self.coords[11] = (555 - self.texts[11].get_rect().width/2, 415 - self.texts[11].get_rect().height/2)
            self.coords[12] = (555 - self.texts[12].get_rect().width/2, 455 - self.texts[12].get_rect().height/2)
            for i in range(6):
                self.coords[13 + 3 * i] = (50, 290 + 30 * i)
                self.coords[14 + 3 * i] = (260, 290 + 30 * i)
                self.coords[15 + 3 * i] = (340, 290 + 30 * i)
    
        def title(self, surface, accent):
            surface.fill(BLACK, [0, 0, 750, 150])
            menu_text = font100.render("Menu", True, accent)
            surface.blit(menu_text, [375 - menu_text.get_rect().width/2, 75 - menu_text.get_rect().height/2])
            pygame.draw.polygon(surface, LIGHT_GRAY if self.hover == -1 else GRAY, [(675, 100), (675, 50), (700, 75)])
            pygame.draw.polygon(surface, LIGHT_GRAY if self.hover == -2 else GRAY, [(75, 100), (75, 50), (50, 75)])
            
        def body(self, surface, accent):
            surface.fill(BLACK, [0, 150, 750, 750])
            pygame.draw.rect(surface, GREEN, [30, 150, 330, 330], 2)
            pygame.draw.rect(surface, GREEN, [42, 280, 306, 188], 1)
            pygame.draw.rect(surface, GREEN if self.hover == 0 else WHITE, self.rects[0], 1)
            if self.data_mode == 1:
                pygame.draw.rect(surface, GREEN, [333, self.data_scroll_bar, 10, 30], 0 if (self.data_scroll_drag or self.hover == -3) else 1)
            pygame.draw.rect(surface, RED, [390, 150, 330, 210], 2)
            if self.overlay.settings_mode > 0:
                pygame.draw.rect(surface, RED, [395, 155, 320, 160], 1)
                if self.overlay.settings_mode == 2:
                    pygame.draw.rect(surface, RED if self.hover == 8 else WHITE, self.rects[1], 1) 
                    self.rects[2] = pygame.draw.circle(surface, RED if self.hover == 19 else accent if self.overlay.settings.dark_shape == 0 else WHITE, (455, 295), 13)
                    self.rects[3] = pygame.draw.rect(surface, RED if self.hover == 20 else accent if self.overlay.settings.dark_shape == 1 else WHITE, [492, 282, 26, 26])
                    self.rects[4] = pygame.draw.polygon(surface, RED if self.hover == 21 else accent if self.overlay.settings.dark_shape == 2 else WHITE, [(542, 295), (555, 282), (568, 295), (555, 308)])
                    self.rects[5] = pygame.draw.polygon(surface, RED if self.hover == 22 else accent if self.overlay.settings.dark_shape == 3 else WHITE, [(605, 281), (589, 308), (621, 308)])
                    self.rects[6] = pygame.draw.polygon(surface, RED if self.hover == 23 else accent if self.overlay.settings.dark_shape == 4 else WHITE, [(655, 279), (659, 291), (671, 290), (660, 297), (665, 308), (655, 301), (645, 308), (650, 297), (639, 290), (651, 291)])
                    gfxdraw.aacircle(surface, 455, 295, 13,  RED if self.hover == 19 else accent if self.overlay.settings.dark_shape == 0 else WHITE)
                    gfxdraw.aapolygon(surface, [(605, 281), (589, 308), (621, 308)], RED if self.hover == 22 else accent if self.overlay.settings.dark_shape == 3 else WHITE)
                    gfxdraw.aapolygon(surface, [(655, 279), (659, 291), (671, 290), (660, 297), (665, 308), (655, 301), (645, 308), (650, 297), (639, 290), (651, 291)], RED if self.hover == 23 else accent if self.overlay.settings.dark_shape == 4 else WHITE)
            pygame.draw.rect(surface, ORANGE, [390, 390, 330, 90], 2)
            gfxdraw.aapolygon(surface, [(553, 478), (553, 505), (550, 505), (555, 510), (560, 505), (557, 505), (557, 478)], ORANGE)
            pygame.draw.rect(surface, BLUE, [30, 510, 690, 210], 2)
            pygame.draw.rect(surface, BLUE, [705, self.control_scroll_bar, 10, 30], 0 if (self.control_scroll_drag or self.hover == -4) else 1)
            
            for t, c in zip(self.texts[:13], self.coords[:13]):
                surface.blit(t, c)    
            if self.data_mode == 0:
                for i, (t, c) in enumerate(zip(self.texts[13 + 3 * self.data_scroll : 13 + 3 * (self.profiles + self.data_scroll)], self.coords[13 : 13 + 3 * self.profiles])):
                    surface.blit(t, c if i % 3 == 0 else (c[0] - t.get_rect().width, c[1]))
            elif self.data_mode == 1:
                for t, c in zip(self.texts[13 + 3 * len(self.overlay.settings.profile_names) + self.data_scroll : 19 + 3 * len(self.overlay.settings.profile_names) + self.data_scroll], self.coords[13 :: 3]):
                    surface.blit(t, c)            
                
            if self.edit > 0 and self.host.dummy_count % FRAME_RATE < FRAME_RATE / 2:
                if self.edit == 1:
                    pygame.draw.line(surface, WHITE, [self.coords[0][0] + self.texts[0].get_rect().width + 2, self.coords[0][1]], [self.coords[0][0] + self.texts[0].get_rect().width + 2, self.coords[0][1] + self.texts[0].get_rect().height])
                if self.edit == 2:
                    pygame.draw.line(surface, WHITE, [self.coords[8][0] + self.texts[8].get_rect().width + 2, self.coords[8][1]], [self.coords[8][0] + self.texts[8].get_rect().width + 2, self.coords[8][1] + self.texts[8].get_rect().height - 3])
            
            if self.control_mode == 0:
                for i, line in enumerate(CONTROLS_TEXT.splitlines()[self.control_scroll : self.control_scroll + 7]):
                    surface.blit(font28.render(line, True, WHITE), [40, 514 + 30 * i])        
            
            elif self.control_mode == 1:
                line = self.control_scroll
                for title, paragraph, length in zip(INTRO_HEADERS, INTRO_TEXT, self.intro_lengths):
                    if line < 0:
                        if line > - 8:
                            surface.blit(font28.render(title, True, WHITE), [60, 558 - 19 * line])
                            for i, text in enumerate(paragraph.splitlines()[:line + 8]):
                                surface.blit(font20.render(text, True, WHITE), [50, 569 + 19 * (i - line)])
                        break
                    elif line < length:
                        surface.blit(font28.render(title, True, WHITE), [60, 520 if (line > 0 or self.control_scroll == 0) else 539])
                        for i, text in enumerate(paragraph.splitlines()[line : line + 9]):
                            surface.blit(font20.render(text, True, WHITE), [50, 550 + 19 * i])
                    line -= length