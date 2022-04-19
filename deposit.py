from math import sqrt, pi, tan
from pygame import Surface, PixelArray, gfxdraw
from pygame.draw import circle
from colors import ORANGE, DARK_ORANGE, RED, BLACK #@UnresolvedImport
from coin import Coin #@UnresolvedImport
from constants import DRAIN_SPEED #@UnresolvedImport
from fonts import num_font20 #@UnresolvedImport

class Deposit(Coin):
    def __init__(self, cx, cy, r, a):
        super().__init__(cx, cy, r)
        self.air = a
        self.capacity = a
        
        self.fill = 0
        self.display_surface = Surface((self.radius * 2, self.radius * 2))
        self.display_surface.set_colorkey(BLACK)
        gfxdraw.filled_circle(self.display_surface, self.radius, self.radius, self.radius, ORANGE)

    def proximity(self, ball):
        if self.air > 0 and self.touch(ball.position):
            d_size = sqrt(ball.size * ball.size + min(self. air, DRAIN_SPEED)) - ball.size
            temp = self.host.inflator_correct(d_size, ball.position - (0, d_size), ball.size + d_size)
            if temp:
                ball.size += d_size
                ball.position.update(temp)
                self.air = max(self.air - DRAIN_SPEED, 0)
                self.update_overlay()
                
            if self.host.creator and self.host.creator.editor and self.host.creator.editor.parent == self:
                self.host.creator.editor.parameters[6] = self.air            
    
    def update_overlay(self):
        prev_fill = self.fill
        self.fill = round((1 + tan((1/2 - self.air/self.capacity) * pi/2)) * self.radius)
        if prev_fill < self.fill:
            dspa = PixelArray(self.display_surface)
            dspa[:, prev_fill:self.fill].replace(ORANGE, DARK_ORANGE)
            dspa.close()
 
    def draw(self, surface, mode):
        if mode == "back":
            surface.blit(self.display_surface, self.center - (self.radius, self.radius))
        elif mode == "front":
            gfxdraw.aacircle(surface, self.center_x, self.center_y, self.radius, DARK_ORANGE if self.air == 0 else ORANGE)
            goal_air = num_font20.render("{0:0g}".format(self.air), True, BLACK)
            surface.blit(goal_air, self.center - (goal_air.get_rect().width/2, goal_air.get_rect().height/2))
        elif mode == "outline":
            circle(surface, RED, self.center + (1, 1), self.radius + 1, 4)

    def update_radius(self, radius):
        self.fill = 0
        self.radius = radius
        self.display_surface = Surface((self.radius * 2, self.radius * 2))
        self.display_surface.set_colorkey(BLACK)
        gfxdraw.filled_circle(self.display_surface, self.radius, self.radius, self.radius, ORANGE)
        if self.capacity > 0:
            self.update_overlay()