from math import sqrt, pi, tan
from pygame import Surface, gfxdraw, BLEND_RGB_ADD, PixelArray
from pygame.draw import circle
from constants import FRAME_RATE #@UnresolvedImport
from colors import GREEN, DARK_GREEN, RED, BLACK #@UnresolvedImport
from coin import Coin #@UnresolvedImport
from fonts import num_font20 #@UnresolvedImport

class Goal(Coin):
    def __init__(self, cx, cy, r, a):
        super().__init__(cx, cy, r)
        self.air = a
        self.air_draw = a
        self.air_step = 0
        self.capacity = a
        
        self.fill = self.radius * 2
        self.display_surface = Surface((self.radius * 2, self.radius * 2))
        self.display_surface.set_colorkey(BLACK)
        gfxdraw.filled_circle(self.display_surface, self.radius, self.radius, self.radius, GREEN)
          
        self.animated = False
        self.animation_state = 1
        self.animation_surface = Surface((self.radius * 4, self.radius * 4))
        self.animation_surface.set_colorkey(BLACK)

    def proximity(self, ball, animate):
        if self.air > 0 and ball.size > 4 and self.touch(ball.position):
            if self.air > ball.size * ball.size - 16.1:
                self.air -= ball.size * ball.size - 16
                ball.size = 4
                if self.air < 0.1:
                    self.air = 0
            else:
                ball.size = sqrt(ball.weight() - self.air)
                self.air = 0

            if animate:
                self.air_step = (self.air_draw - self.air)/FRAME_RATE
            else:
                self.air_draw = self.air
                self.update_overlay()
    
            if self.host.creator and self.host.creator.editor and self.host.creator.editor.parent == self:
                self.host.creator.editor.parameters[6] = self.air

    def fill_overlay(self):
        if self.air_step:
            self.air_draw -= self.air_step
            if self.air_draw <= self.air:
                self.air_draw = self.air
                self.air_step = 0
            self.update_overlay()

    def update_overlay(self):
        prev_fill = self.fill
        self.fill = round((1 - tan((1/2 - self.air_draw/self.capacity) * pi/2)) * self.radius)
        if prev_fill > self.fill:
            dspa = PixelArray(self.display_surface)
            dspa[:, self.fill:prev_fill].replace(GREEN, DARK_GREEN)
            dspa.close()

    def draw(self, surface, mode):
        if mode == "back":
            surface.blit(self.display_surface, self.center - (self.radius, self.radius))
        elif mode == "front":
            gfxdraw.aacircle(surface, self.center_x, self.center_y, self.radius, GREEN if self.air_draw else DARK_GREEN)
            goal_air = num_font20.render("{0:0g}".format(self.air), True, BLACK)
            surface.blit(goal_air, self.center - (goal_air.get_width()/2, goal_air.get_height()/2))
            if self.animated:
                if self.air > 0:                   
                    self.animation_surface.fill(BLACK)
                    circle(self.animation_surface, (0, 255 * self.animation_state * self.animation_state, 0), (self.radius * 2, self.radius * 2), self.radius * (2 - self.animation_state))
                    circle(self.animation_surface, BLACK, (self.radius * 2, self.radius * 2), self.radius)
                    surface.blit(self.animation_surface, self.center - (2 * self.radius, 2 * self.radius), special_flags = BLEND_RGB_ADD)
                    self.animation_state -= 1/60
                    if self.animation_state < 0:
                        self.animated = False
                        self.animation_state = 1
                else:
                    self.animated = False
        elif mode == "outline":
            circle(surface, RED, self.center + (1, 1), self.radius + 1, 4)

    def update_radius(self, radius):
        self.fill = radius * 2
        self.radius = radius
        self.display_surface = Surface((self.radius * 2, self.radius * 2))
        self.display_surface.set_colorkey(BLACK)
        gfxdraw.filled_circle(self.display_surface, self.radius, self.radius, self.radius, GREEN)
        if self.capacity > 0:
            self.update_overlay()
        self.animation_surface = Surface((self.radius * 4, self.radius * 4))
        self.animation_surface.set_colorkey(BLACK)