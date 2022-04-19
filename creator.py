import pygame
from time import strftime
from colors import GRAY, WHITE, RED, GREEN, BLUE, ORANGE, PURPLE, CYAN, BLACK #@UnresolvedImport
from constants import FRAME_RATE #@UnresolvedImport
from controls import controls #@UnresolvedImport
from fonts import font25,  num_font20 #@UnresolvedImport
from ball import Ball #@UnusedImport #@UnresolvedImport
from beam import Beam #@UnresolvedImport
from goal import Goal #@UnresolvedImport
from teleporter import Teleporter #@UnresolvedImport
from remover import Remover #@UnresolvedImport
from deposit import Deposit #@UnresolvedImport
import overlay #@UnresolvedImport
import game #@UnresolvedImport
import replay #@UnresolvedImport

class Creator():
    def __init__(self, host, settings):
        self.host = host
        self.settings = settings
        self.mode = 5
        self.path = []
        self.drag = False
        self.editor = None

    def loop(self, screen, clock):       
        screen_height = screen.get_height()
        if screen_height != 800:
            screen = pygame.display.set_mode([750, 800], screen.get_flags())
        
        while self.host.run and self.host.creator:
            self.host.dummy_count += 1
            
            # Event Processing
            mouse_pos = self.host.mouse(pygame.mouse.get_pos())
            self.redraw(screen, mouse_pos)
            
            if self.drag and self.path[-1] != mouse_pos:
                self.path.append(mouse_pos)
        
            screen, clock = self.event_handling(pygame.event.get(), screen, clock, mouse_pos)
            if not self.host.run or not self.host.creator:
                break
        
            if self.host.paused:
                pygame.display.flip()
                clock.tick(FRAME_RATE)
                continue
        
            # game.Game logic
            self.host.inflate()
            self.host.physics()
            
            if self.host.started:
                self.host.frame_count += 1
            pygame.display.flip()
            clock.tick(FRAME_RATE)
            
        if screen_height != 800:
            screen = pygame.display.set_mode([750, 750], screen.get_flags())
        return screen, clock
            
    def event_handling(self, events, screen, clock, mouse_pos):
        actions = []
        for event in events:
            # User pressed the cross
            if event.type == pygame.QUIT:
                print("Best session times:")
                print(self.host.times)
                self.host.run = False
            # User used the mouse
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.click(pygame.mouse.get_pos())
            elif event.type == pygame.MOUSEBUTTONUP:
                if self.drag:
                    self.click_release()
                else:
                    self.host.prev_mouse_pos = None
                    self.host.drag = False
            # User pressed a key
            elif event.type == pygame.KEYDOWN:
                if self.editor and (event.key == pygame.K_RETURN or event.key == pygame.K_DELETE or event.key == pygame.K_BACKSPACE or event.unicode.isnumeric()):
                    self.editor.edit(event)
                elif self.editor and self.host.paused and (event.key == pygame.K_UP or event.key == pygame.K_LEFT or event.key == pygame.K_DOWN or event.key == pygame.K_RIGHT):
                    self.editor.move(event)
                elif event.key in controls:
                    if self.host.paused:
                        continue
                    actions.append(event)
    
                elif event.key == pygame.K_q:
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
                elif event.key == pygame.K_c:
                    if self.host.level_count > 0:
                        self.host.creator = None
                        self.host.update_beam_surface(True)
                elif event.key == pygame.K_k:
                    if self.host.actions:
                        self.editor = None
                        self.host.replay = replay.Replay(self.host, self.settings, [[eval(a) for a in action] for action in self.host.actions], self.host.mouse_actions.copy(), self.host.frame_count, self.pin_frame)
                        screen, clock = self.host.replay.loop(screen, clock)
                elif event.key == pygame.K_F4:
                    self.host.path_color_id = (self.host.path_color_id + 1) % 6
                elif event.key == pygame.K_F5:
                    self.host.draw_surface.fill(BLACK)
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
                elif event.key == pygame.K_F11:
                    if self.host.level_count > 0:
                        self.host.level_count = 0
                        self.host.level(self.host.level_count)
                elif event.key == pygame.K_F12:
                    self.host.save_level(f"game_data/levels/{strftime('%Y%m%d-%H%M%S')}.txt")
    
            # User released a key
            elif event.type == pygame.KEYUP and self.host.started and event.key in controls:
                actions.append(event)

        return self.host.event_handling(actions, screen, clock, mouse_pos)

    def redraw(self, surface, mouse_pos):
        game.Game.redraw(self.host, surface, mouse_pos)
        save_text = font25.render("pin current state", True, RED)
        load_text = font25.render("open pinned state", True, RED)
        surface.blit(save_text, [214, 38])
        surface.blit(load_text, [375, 38])

        surface.fill(GRAY, [0, 750, 750, 800])
        if self.editor:
            self.editor.draw(surface)
            if self.editor.type != 4:
                self.editor.parent.draw(surface, "outline")
        else:
            pygame.draw.rect(surface, BLUE, [42, 755, 40, 40], 0)
            pygame.draw.circle(surface, GREEN, [187, 775], 20, 0)
            pygame.draw.circle(surface, PURPLE, [312, 775], 20, 0)
            pygame.draw.circle(surface, CYAN, [437, 775], 20, 0)
            pygame.draw.circle(surface, ORANGE, [562, 775], 20, 0)
            pygame.draw.line(surface, ORANGE, (667, 795), (707, 755), 3)
            pygame.draw.rect(surface, RED, [self.mode * 125 + 37, 750, 50, 50], 2)
        if self.drag and len(self.path) >= 2:
            pygame.draw.lines(surface, BLUE if self.mode == 0 else PURPLE, False, self.path, 2)
    
    def click(self, mouse_pos):
        if mouse_pos[1] < 750:
            if 38 <= mouse_pos[1] <= 56:
                if 214 <= mouse_pos[0] <= 350:
                    self.host.save_level("game_data/levels/creator/pinned.txt")
                    self.pin_frame = self.host.frame_count
                    return
                elif 375 <= mouse_pos[0] <= 519:
                    self.host.open("creator/pinned")
                    self.editor = None
                    self.pin_frame = self.host.frame_count
                    return

            if self.host.Balls[0].touch(mouse_pos, self.host.Balls[0].size) or self.host.Balls[1].touch(mouse_pos, self.host.Balls[1].size):
                self.editor = self.Editor(self.host, self, None)
            else:
                for deposit in self.host.Deposits:
                    if deposit.touch(mouse_pos):
                        self.editor = self.Editor(self.host, self, deposit)
                        break
                else:
                    for remover in self.host.Removers:
                        if remover.touch(mouse_pos):
                            self.editor = self.Editor(self.host, self, remover)
                            break
                    else:
                        for teleporter in self.host.Teleporters:
                            if teleporter.touch(mouse_pos):
                                self.editor = self.Editor(self.host, self, teleporter)
                                break
                        else:
                            for goal in self.host.Goals:
                                if goal.touch(mouse_pos):
                                    self.editor = self.Editor(self.host, self, goal)
                                    break
                            else:
                                for beam in self.host.Beams:
                                    if beam.mouse(mouse_pos):
                                        self.editor = self.Editor(self.host, self, beam)
                                        break
                                else:
                                    if self.mode == 1:
                                        goal = Goal(*mouse_pos, 25, 0)
                                        goal.attach(self.host)
                                        self.editor = self.Editor(self.host, self, goal)
                                        self.host.Goals.append(goal)
                                    elif self.mode == 3:
                                        remover = Remover(*mouse_pos, 25, 0)
                                        remover.attach(self.host)
                                        self.editor = self.Editor(self.host, self, remover)
                                        self.host.Removers.append(remover)
                                    elif self.mode == 4:
                                        deposit = Deposit(*mouse_pos, 25, 0)
                                        deposit.attach(self.host)
                                        self.editor = self.Editor(self.host, self, deposit)
                                        self.host.Deposits.append(deposit)
                                    elif self.mode == 5:
                                        self.host.drag = True
                                    else:
                                        self.path = [mouse_pos]
                                        self.drag = True
        else:
            if self.editor:
                self.editor.click(2 * (mouse_pos[0] // 150) + (mouse_pos[1] - 750) // 25)
            else:
                mouse_x = mouse_pos[0] // 42 - 1
                if mouse_x % 3 == 0:
                    self.mode = mouse_x // 3
    
    def click_release(self):
        if self.mode == 0:
            if len(self.path) > 5:
                up = min(self.path[0][0], self.path[-1][0]) // 5 * 5
                down = max(self.path[0][0], self.path[-1][0]) // 5 * 5
                left = min(self.path[0][1], self.path[-1][1]) // 5 * 5
                right = max(self.path[0][1], self.path[-1][1]) // 5 * 5
                if up < 20:
                    up = 0
                if down >= 730:
                    down = 750
                if left < 20:
                    left = 0
                if right >= 730:
                    right = 750
                if down - up < 50:
                    if down != 750:
                        down = up + 30
                    else:
                        up = down - 30
                if right - left < 50:
                    if right != 750:
                        right = left + 30
                    else:
                        left = right - 30
                self.host.Beams.append(Beam(up, down, left, right, []))   
                self.editor = self.Editor(self.host, self, self.host.Beams[-1])
        elif self.mode == 2 and (self.path[0][0] - self.path[-1][0]) * (self.path[0][0] - self.path[-1][0]) + (self.path[0][1] - self.path[-1][1]) * (self.path[0][1] - self.path[-1][1]) > 100:
            teleporter = Teleporter(*self.path[0], 25, *self.path[-1])
            teleporter.attach(self.host)
            self.editor = self.Editor(self.host, self, teleporter)
            self.host.Teleporters.append(teleporter)
        self.path.clear()
        self.drag = False

    class Editor:
        def __init__(self, host, creator, parent):
            self.host = host
            self.creator = creator
            self.parent = parent
            self.parameters = [None] * 8
            self.selected = 6
            if parent is None:
                self.text = ["arrow x", "wasd x", "arrow y", "wasd y", "size arrow", "size wasd"]
                self.type = 4
                self.selected = 4
            elif isinstance(parent, Beam):
                self.parameters[0] = parent.left
                self.parameters[1] = parent.right
                self.parameters[2] = parent.up
                self.parameters[3] = parent.down
                self.parameters[4] = parent.right - parent.left
                self.parameters[5] = parent.down - parent.up
                self.parameters[6] = parent.remover
                self.type = 0
                self.text = ["left", "right", "up", "down", "width", "height", "remover"]
            elif isinstance(parent, (Goal, Teleporter, Remover, Deposit)):
                self.parameters[0] = parent.center_x - parent.radius
                self.parameters[1] = parent.center_x + parent.radius
                self.parameters[2] = parent.center_y - parent.radius
                self.parameters[3] = parent.center_y + parent.radius
                self.parameters[4] = parent.radius
                if isinstance(parent, Goal):
                    self.parameters[6] = parent.air
                    self.parameters[7] = parent.capacity
                    self.type = 1
                    self.text = ["left", "right", "up", "down", "radius", "", "air", "capacity"]
                if isinstance(parent, Teleporter):
                    self.parameters[6] = parent.destination.x
                    self.parameters[7] = parent.destination.y
                    self.type = 2
                    self.text = ["left", "right", "up", "down", "radius", "", "to (x)", "to (y)"]
                if isinstance(parent, Remover):
                    self.parameters[6] = parent.id
                    self.type = 3
                    self.text = ["left", "right", "up", "down", "radius", "", "id"]
                if isinstance(parent, Deposit):
                    self.parameters[6] = parent.air
                    self.parameters[7] = parent.capacity
                    self.type = 5
                    self.text = ["left", "right", "up", "down", "radius", "", "air", "capacity"]
    
        def draw(self, surface):
            if self.type == 4:
                for i, (txt, var) in enumerate(zip(self.text, [self.host.Balls[0].position.x, self.host.Balls[1].position.x, self.host.Balls[0].position.y, self.host.Balls[1].position.y, self.host.Balls[0].size, self.host.Balls[1].size])):
                    text = num_font20.render(txt + ": " + str(int(var)), True, RED if self.selected == i else WHITE)
                    surface.blit(text, [75 + i // 2 * 150 - text.get_rect().width/2, 762 + i % 2 * 26 - text.get_rect().height/2])
                dja_txt = num_font20.render("doublejump arrow", True, WHITE)
                surface.blit(dja_txt, [550 - dja_txt.get_rect().width/2, 762 - dja_txt.get_rect().height/2])
                djw_txt = num_font20.render("doublejump wasd", True, WHITE)
                surface.blit(djw_txt, [550 - djw_txt.get_rect().width/2, 788 - djw_txt.get_rect().height/2])
            else:
                for i, txt in enumerate(self.text):
                    if txt:
                        text = num_font20.render(txt + ": " + str(self.parameters[i]), True, RED if self.selected == i else WHITE)
                        surface.blit(text, [75 + i // 2 * 150 - text.get_rect().width/2, 762 + i % 2 * 26 - text.get_rect().height/2])
            exit_txt = num_font20.render("exit", True, WHITE)
            surface.blit(exit_txt, [675 - exit_txt.get_rect().width/2, 762 - exit_txt.get_rect().height/2])
            delete_txt = num_font20.render("delete", True, WHITE)
            surface.blit(delete_txt, [675 - delete_txt.get_rect().width/2, 788 - delete_txt.get_rect().height/2])
            if self.type in [1, 5]:
                reset_txt = num_font20.render("reset air capacity", True, WHITE)
                surface.blit(reset_txt, [375 - reset_txt.get_rect().width/2, 788 - reset_txt.get_rect().height/2])
    
        def click(self, clicked):
            if clicked == 8:
                self.kill(False)
            elif clicked == 9:
                self.kill(True)
            elif clicked < len(self.text) and self.text[clicked]:
                self.selected = clicked
            elif self.type == 4 and clicked == 6:
                self.host.Balls[0].doublejump = not self.host.Balls[0].doublejump
            elif self.type == 4 and clicked == 7:
                self.host.Balls[1].doublejump = not self.host.Balls[1].doublejump
            elif self.type == 1 and clicked == 5:
                self.parameters[6] = self.parameters[7]
                self.parent.air = self.parameters[6]
                self.parent.air_draw = self.parameters[6]
            elif self.type == 5 and clicked == 5:
                self.parameters[6] = self.parameters[7]
                self.parent.air = self.parameters[6]

        def edit(self, event):
            if event.key == pygame.K_RETURN:
                self.kill(False)
            elif event.key == pygame.K_DELETE:
                self.kill(True)
            elif self.type == 0 and self.selected == 6:
                edit = self.parameters[6]
                if event.key== pygame.K_BACKSPACE:
                    if edit:
                        del edit[-1]
                elif event.unicode.isnumeric():
                    edit.append(int(event.unicode))
                self.parameters[6] = edit
                self.parent.remover = self.parameters[6]
            elif self.type != 4:
                edit = self.parameters[self.selected]
                if event.key== pygame.K_BACKSPACE:
                    edit = edit // 10
                elif event.unicode.isnumeric():
                    edit += edit * 9 + int(event.unicode)
                self.parameters[self.selected] = edit
    
                if self.type == 0:
                    if self.selected < 4:
                        self.parameters[4] = self.parameters[1] - self.parameters[0]
                        self.parameters[5] = self.parameters[3] - self.parameters[2]
                    elif self.selected == 4:
                        self.parameters[1] = self.parameters[0] + self.parameters[4]
                    elif self.selected == 5:
                        self.parameters[3] = self.parameters[2] + self.parameters[5]
                    self.parent.left = self.parameters[0]
                    self.parent.right = self.parameters[1]
                    self.parent.up = self.parameters[2]
                    self.parent.down = self.parameters[3]
                else:
                    if self.selected == 0:
                        self.parameters[1] = self.parameters[0] + 2 * self.parameters[4]
                    elif self.selected == 1:
                        self.parameters[0] = self.parameters[1] - 2 * self.parameters[4]
                    elif self.selected == 2:
                        self.parameters[3] = self.parameters[2] + 2 * self.parameters[4]
                    elif self.selected == 3:
                        self.parameters[2] = self.parameters[3] - 2 * self.parameters[4]
                    self.parent.center_x = self.parameters[0] + self.parameters[4]
                    self.parent.center_y = self.parameters[2] + self.parameters[4]
                    self.parent.center.update(self.parent.center_x, self.parent.center_y)
                    
                if self.type == 1:
                    if self.selected == 4:
                        self.parent.update_radius(self.parameters[4])
                    elif self.selected == 6:
                        self.parameters[7] += self.parameters[6] - self.parent.air
                    elif self.selected == 7:
                        self.parameters[6] += self.parameters[7] - self.parent.capacity
                    self.parent.air = self.parameters[6]
                    self.parent.air_draw = self.parameters[6]
                    self.parent.capacity = self.parameters[7]
                elif self.type == 2:
                    self.parent.radius = self.parameters[4]
                    self.parent.destination.update(self.parameters[6], self.parameters[7])
                elif self.type == 3:
                    self.parent.radius = self.parameters[4]
                    self.parent.id = self.parameters[6]
                elif self.type == 5:
                    if self.selected == 4:
                        self.parent.update_radius(self.parameters[4])
                    elif self.selected == 6:
                        self.parameters[7] += self.parameters[6] - self.parent.air
                    elif self.selected == 7:
                        self.parameters[6] += self.parameters[7] - self.parent.capacity
                    self.parent.air = self.parameters[6]
                    self.parent.capacity = self.parameters[7]
            else:
                if self.selected == 0:
                    if event.key== pygame.K_BACKSPACE:
                        self.host.Balls[0].position.x = self.host.Balls[0].position.x // 10
                    elif event.unicode.isnumeric():
                        self.host.Balls[0].position.x += self.host.Balls[0].position.x * 9 + int(event.unicode)
                elif self.selected == 1:
                    if event.key== pygame.K_BACKSPACE:
                        self.host.Balls[1].position.x = self.host.Balls[1].position.x // 10
                    elif event.unicode.isnumeric():
                        self.host.Balls[1].position.x += self.host.Balls[1].position.x * 9 + int(event.unicode)
                elif self.selected == 2:
                    if event.key== pygame.K_BACKSPACE:
                        self.host.Balls[0].position.y = self.host.Balls[0].position.y // 10
                    elif event.unicode.isnumeric():
                        self.host.Balls[0].position.y += self.host.Balls[0].position.y * 9 + int(event.unicode)
                elif self.selected == 3:   
                    if event.key== pygame.K_BACKSPACE:
                        self.host.Balls[1].position.y = self.host.Balls[1].position.y // 10
                    elif event.unicode.isnumeric():
                        self.host.Balls[1].position.y += self.host.Balls[1].position.y * 9 + int(event.unicode)
                elif self.selected == 4:
                    if event.key== pygame.K_BACKSPACE:
                        self.host.Balls[0].size = self.host.Balls[0].size // 10
                    elif event.unicode.isnumeric():
                        self.host.Balls[0].size += self.host.Balls[0].size * 9 + int(event.unicode)
                elif self.selected == 5:    
                    if event.key== pygame.K_BACKSPACE:
                        self.host.Balls[1].size = self.host.Balls[1].size // 10
                    elif event.unicode.isnumeric():
                        self.host.Balls[1].size += self.host.Balls[1].size * 9 + int(event.unicode)
    
        def move(self, event):
            if self.type == 4:
                return
            if event.key == pygame.K_LEFT:
                self.parameters[0] = max(self.parameters[0] - 5, 0)
                if self.type == 0:
                    self.parameters[1] = self.parameters[0] + self.parameters[4]
                    self.parent.left = self.parameters[0]
                    self.parent.right = self.parameters[1]
                else:
                    self.parameters[1] = self.parameters[0] + 2 * self.parameters[4]
                    self.parent.center_x = self.parameters[0] + self.parameters[4]
                    self.parent.center.x = self.parent.center_x
            elif event.key == pygame.K_RIGHT:
                self.parameters[1] = min(self.parameters[1] + 5, 750)
                if self.type == 0:
                    self.parameters[0] = self.parameters[1] - self.parameters[4]
                    self.parent.left = self.parameters[0]
                    self.parent.right = self.parameters[1]
                else:
                    self.parameters[0] = self.parameters[1] - 2 * self.parameters[4]
                    self.parent.center_x = self.parameters[0] + self.parameters[4]
                    self.parent.center.x = self.parent.center_x
            elif event.key == pygame.K_UP:
                self.parameters[2] = max(self.parameters[2] - 5, 0)
                if self.type == 0:
                    self.parameters[3] = self.parameters[2] + self.parameters[5]
                    self.parent.up = self.parameters[2]
                    self.parent.down = self.parameters[3]
                else:
                    self.parameters[3] = self.parameters[2] + 2 * self.parameters[4]
                    self.parent.center_y = self.parameters[2] + self.parameters[4]
                    self.parent.center.y = self.parent.center_y
            elif event.key == pygame.K_DOWN:
                self.parameters[3] = min(self.parameters[3] + 5, 750)
                if self.type == 0:
                    self.parameters[2] = self.parameters[3] - self.parameters[5]
                    self.parent.up = self.parameters[2]
                    self.parent.down = self.parameters[3]
                else:
                    self.parameters[2] = self.parameters[3] - 2 * self.parameters[4]
                    self.parent.center_y = self.parameters[2] + self.parameters[4]
                    self.parent.center.y = self.parent.center_y
    
        def kill(self, delete):
            if delete:
                if self.type == 0:
                    self.host.Beams.remove(self.parent)
                elif self.type == 1:
                    self.host.Goals.remove(self.parent)
                elif self.type == 2:
                    self.host.Teleporters.remove(self.parent)
                elif self.type == 3:
                    self.host.Removers.remove(self.parent)
                elif self.type == 5:
                    self.host.Deposits.remove(self.parent)
            self.creator.editor = None